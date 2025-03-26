import os
import logging
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request

# Importação dos serviços
from services.amadeus_service import AmadeusService
from services.openai_service import OpenAIService

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Inicializa os serviços
amadeus_service = AmadeusService()
openai_service = OpenAIService()

# Dados temporários (serão substituídos por banco de dados)
conversations = [
    {"id": 1, "title": "Viagem para Paris", "last_updated": "15/10/2023"},
    {"id": 2, "title": "Final de semana em Barcelona", "last_updated": "28/09/2023"},
    {"id": 3, "title": "Planejamento de férias de verão", "last_updated": "10/08/2023"}
]

# Armazena mensagens das conversas
conversation_messages = {
    1: [
        {"is_user": True, "content": "Olá, estou planejando uma viagem para Paris.", "timestamp": "2023-10-15T10:30:00"},
        {"is_user": False, "content": "Paris é um destino maravilhoso! A melhor época para visitar é na primavera (abril a junho) ou no outono (setembro a novembro). Gostaria que eu sugerisse algumas acomodações ou atividades?", "timestamp": "2023-10-15T10:30:15"}
    ]
}

# Dados de viagens
plans = [
    {
        "id": 1,
        "title": "Final de semana em Barcelona",
        "destination": "Barcelona, Espanha",
        "start_date": "15/12/2023",
        "end_date": "17/12/2023",
        "details": "Um fim de semana para explorar a arquitetura e a culinária de Barcelona."
    },
    {
        "id": 2,
        "title": "Verão na Grécia",
        "destination": "Atenas e Santorini, Grécia",
        "start_date": "10/06/2024",
        "end_date": "20/06/2024",
        "details": "Férias de 10 dias explorando Atenas e relaxando em Santorini."
    }
]

# Dados do perfil do usuário
user_profile = {
    "name": "João Silva",
    "email": "joao.silva@exemplo.com",
    "phone": "+55 11 98765-4321",
    "preferences": {
        "preferred_destinations": "Praia, Montanha",
        "accommodation_type": "Hotel",
        "budget": "Médio"
    }
}

# Sistema de monitoramento de preços
monitored_offers = {
    "flights": [],
    "hotels": []
}

price_alerts = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/conversations')
def get_conversations():
    return jsonify(conversations)

@app.route('/api/plans')
def get_plans():
    return jsonify(plans)

@app.route('/api/plan/<int:plan_id>')
def get_plan(plan_id):
    plan = next((p for p in plans if p["id"] == plan_id), None)
    if plan:
        return jsonify(plan)
    return jsonify({"error": "Plano não encontrado"}), 404

@app.route('/api/profile')
def get_profile():
    return jsonify(user_profile)

@app.route('/api/profile', methods=['POST'])
def update_profile():
    global user_profile
    data = request.json
    
    # Update only the provided fields
    if 'name' in data:
        user_profile['name'] = data['name']
    if 'email' in data:
        user_profile['email'] = data['email']
    if 'phone' in data:
        user_profile['phone'] = data['phone']
    if 'preferences' in data:
        user_profile['preferences'] = data['preferences']
    
    return jsonify({"success": True, "profile": user_profile})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    conversation_id = data.get('conversation_id')
    
    # Obter histórico da conversa, se existir
    messages_history = []
    if conversation_id and conversation_id in conversation_messages:
        messages_history = conversation_messages[conversation_id]
    
    try:
        # Chamar a API da OpenAI através do nosso serviço
        result = openai_service.travel_assistant(user_message, messages_history)
        
        if 'error' in result:
            logging.error(f"Erro na API do OpenAI: {result['error']}")
            return jsonify({
                "response": "Desculpe, estou enfrentando problemas para processar sua solicitação no momento. Por favor, tente novamente mais tarde.",
                "error": result['error']
            }), 500
        
        # Adicionar a mensagem do usuário e a resposta ao histórico
        now = datetime.now().isoformat()
        
        # Adicionar mensagem do usuário ao histórico
        new_user_message = {
            "is_user": True,
            "content": user_message,
            "timestamp": now
        }
        
        # Adicionar resposta do assistente ao histórico
        assistant_response = result['response']
        new_assistant_message = {
            "is_user": False,
            "content": assistant_response,
            "timestamp": now
        }
        
        # Se for uma nova conversa, criar um ID e título
        if not conversation_id:
            new_id = max([c['id'] for c in conversations], default=0) + 1
            title = user_message[:30] + "..." if len(user_message) > 30 else user_message
            conversations.append({
                "id": new_id,
                "title": title,
                "last_updated": datetime.now().strftime("%d/%m/%Y")
            })
            conversation_id = new_id
            conversation_messages[conversation_id] = []
        
        # Adicionar as novas mensagens ao histórico
        conversation_messages[conversation_id].append(new_user_message)
        conversation_messages[conversation_id].append(new_assistant_message)
        
        # Atualizar o timestamp da última atualização da conversa
        for conv in conversations:
            if conv['id'] == conversation_id:
                conv['last_updated'] = datetime.now().strftime("%d/%m/%Y")
                break
        
        return jsonify({
            "response": assistant_response,
            "conversation_id": conversation_id
        })
    
    except Exception as e:
        logging.error(f"Erro ao processar mensagem do chat: {str(e)}")
        return jsonify({
            "response": "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde.",
            "error": str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    search_type = data.get('type', '')
    search_params = data.get('params', {})
    
    try:
        if search_type == 'flights':
            # Adicionar parâmetros padrão se não estiverem presentes
            if 'currencyCode' not in search_params:
                search_params['currencyCode'] = 'BRL'
            if 'max' not in search_params:
                search_params['max'] = 10
                
            # Chamar a API da Amadeus
            result = amadeus_service.search_flights(search_params)
            
            if 'error' in result:
                logging.error(f"Erro na busca de voos: {result['error']}")
                return jsonify({
                    "error": "Não foi possível buscar voos no momento",
                    "details": result['error']
                }), 500
            
            # Formatar os resultados da API para um formato mais amigável
            flights = []
            if 'data' in result:
                for offer in result['data']:
                    try:
                        itinerary = offer['itineraries'][0]
                        first_segment = itinerary['segments'][0]
                        last_segment = itinerary['segments'][-1]
                        price = offer['price']['total']
                        currency = offer['price']['currency']
                        
                        flight = {
                            "id": offer['id'],
                            "offer_data": offer,  # Guardar os dados completos para uso futuro
                            "airline": first_segment['carrierCode'],
                            "flight_number": first_segment['number'],
                            "departure": f"{first_segment['departure']['iataCode']}",
                            "arrival": f"{last_segment['arrival']['iataCode']}",
                            "departure_time": first_segment['departure']['at'],
                            "arrival_time": last_segment['arrival']['at'],
                            "stops": len(itinerary['segments']) - 1,
                            "duration": itinerary['duration'],
                            "price": f"{price} {currency}"
                        }
                        flights.append(flight)
                    except (KeyError, IndexError) as e:
                        logging.warning(f"Erro ao processar oferta de voo: {str(e)}")
                        continue
            
            return jsonify({
                "results": flights,
                "raw_data": result if 'meta' in result else None
            })
            
        elif search_type == 'hotels':
            # Buscar hotéis usando a API da Amadeus
            if 'cityCode' not in search_params:
                return jsonify({
                    "error": "O código da cidade (cityCode) é obrigatório para busca de hotéis"
                }), 400
                
            # Fazer a busca de hotéis por cidade
            hotel_result = amadeus_service.search_hotels(search_params)
            
            if 'error' in hotel_result:
                logging.error(f"Erro na busca de hotéis: {hotel_result['error']}")
                return jsonify({
                    "error": "Não foi possível buscar hotéis no momento",
                    "details": hotel_result['error']
                }), 500
            
            # Extrair IDs dos hotéis para buscar ofertas
            hotel_ids = []
            hotels_info = {}
            
            if 'data' in hotel_result:
                for hotel in hotel_result['data']:
                    hotel_id = hotel['hotelId']
                    hotel_ids.append(hotel_id)
                    hotels_info[hotel_id] = {
                        "name": hotel.get('name', 'Hotel sem nome'),
                        "cityCode": hotel.get('cityCode', ''),
                        "address": hotel.get('address', {}).get('lines', [''])[0] if 'address' in hotel and 'lines' in hotel['address'] else '',
                    }
            
            # Se não houver hotéis, retornar lista vazia
            if not hotel_ids:
                return jsonify({
                    "results": [],
                    "message": "Nenhum hotel encontrado para os parâmetros informados"
                })
            
            # Buscar ofertas para os hotéis encontrados
            offers_params = {
                'hotelIds': ','.join(hotel_ids[:20]),  # Limitar a 20 hotéis por consulta
                'adults': search_params.get('adults', 1),
                'currency': search_params.get('currency', 'BRL')
            }
            
            # Adicionar datas se fornecidas
            if 'checkInDate' in search_params:
                offers_params['checkInDate'] = search_params['checkInDate']
            if 'checkOutDate' in search_params:
                offers_params['checkOutDate'] = search_params['checkOutDate']
            
            offers_result = amadeus_service.search_hotel_offers(offers_params)
            
            if 'error' in offers_result:
                logging.error(f"Erro na busca de ofertas de hotéis: {offers_result['error']}")
                return jsonify({
                    "error": "Não foi possível buscar ofertas de hotéis no momento",
                    "details": offers_result['error']
                }), 500
            
            # Formatar os resultados
            hotels = []
            
            if 'data' in offers_result:
                for offer in offers_result['data']:
                    try:
                        hotel_id = offer['hotel']['hotelId']
                        hotel_info = hotels_info.get(hotel_id, {})
                        
                        # Pegar a primeira oferta disponível
                        if 'offers' in offer and offer['offers']:
                            price_offer = offer['offers'][0]
                            price = price_offer['price']['total']
                            currency = price_offer['price']['currency']
                            
                            hotel = {
                                "id": hotel_id,
                                "offer_id": price_offer['id'],
                                "name": hotel_info.get('name', 'Hotel sem nome'),
                                "location": hotel_info.get('address', 'Localização não disponível'),
                                "stars": offer['hotel'].get('rating', 0),
                                "price_per_night": f"{price} {currency}",
                                "available": True,
                                "offer_data": price_offer  # Guardar os dados completos para uso futuro
                            }
                            hotels.append(hotel)
                    except (KeyError, IndexError) as e:
                        logging.warning(f"Erro ao processar oferta de hotel: {str(e)}")
                        continue
            
            return jsonify({
                "results": hotels,
                "raw_data": offers_result if 'meta' in offers_result else None
            })
            
        else:
            return jsonify({
                "error": "Tipo de pesquisa inválido. Use 'flights' ou 'hotels'."
            }), 400
            
    except Exception as e:
        logging.error(f"Erro ao processar pesquisa: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao processar sua pesquisa",
            "details": str(e)
        }), 500

@app.route('/api/price-monitor', methods=['GET'])
def get_monitored_offers():
    """Retorna todas as ofertas monitoradas"""
    return jsonify({
        "flights": monitored_offers["flights"],
        "hotels": monitored_offers["hotels"],
        "alerts": price_alerts
    })

@app.route('/api/price-monitor', methods=['POST'])
def add_monitored_offer():
    """Adiciona uma oferta ao monitoramento de preços"""
    global monitored_offers
    
    try:
        data = request.json
        offer_type = data.get('type')  # 'flight' ou 'hotel'
        offer_data = data.get('data')
        
        if not offer_type or not offer_data:
            return jsonify({"error": "Tipo de oferta e dados são obrigatórios"}), 400
            
        if offer_type not in ['flight', 'hotel']:
            return jsonify({"error": "Tipo de oferta inválido. Use 'flight' ou 'hotel'"}), 400
            
        # Gerar ID único para a oferta
        monitor_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Adicionar metadados do monitoramento
        monitored_offer = {
            "id": monitor_id,
            "type": offer_type,
            "date_added": now,
            "last_checked": now,
            "original_price": None,
            "current_price": None,
            "lowest_price": None,
            "price_history": [],
            "data": offer_data
        }
        
        # Extrair e formatar o preço atual
        if offer_type == 'flight':
            if 'price' in offer_data:
                price_str = offer_data['price']
                # Extrair valor numérico e moeda
                parts = price_str.split(' ')
                if len(parts) == 2:
                    try:
                        price = float(parts[0])
                        currency = parts[1]
                        monitored_offer['original_price'] = price
                        monitored_offer['current_price'] = price
                        monitored_offer['lowest_price'] = price
                        monitored_offer['currency'] = currency
                        monitored_offer['price_history'].append({
                            "date": now,
                            "price": price
                        })
                    except ValueError:
                        pass
        elif offer_type == 'hotel':
            if 'price_per_night' in offer_data:
                price_str = offer_data['price_per_night']
                parts = price_str.split(' ')
                if len(parts) == 2:
                    try:
                        price = float(parts[0])
                        currency = parts[1]
                        monitored_offer['original_price'] = price
                        monitored_offer['current_price'] = price
                        monitored_offer['lowest_price'] = price
                        monitored_offer['currency'] = currency
                        monitored_offer['price_history'].append({
                            "date": now,
                            "price": price
                        })
                    except ValueError:
                        pass
        
        # Adicionar a oferta à lista de monitoramento
        if offer_type == 'flight':
            monitored_offers['flights'].append(monitored_offer)
        else:
            monitored_offers['hotels'].append(monitored_offer)
            
        return jsonify({
            "success": True,
            "message": "Oferta adicionada ao monitoramento com sucesso",
            "monitor_id": monitor_id
        })
        
    except Exception as e:
        logging.error(f"Erro ao adicionar oferta ao monitoramento: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao adicionar a oferta ao monitoramento",
            "details": str(e)
        }), 500

@app.route('/api/price-monitor/<monitor_id>', methods=['DELETE'])
def remove_monitored_offer(monitor_id):
    """Remove uma oferta do monitoramento de preços"""
    global monitored_offers
    
    try:
        # Buscar e remover da lista de voos
        for i, offer in enumerate(monitored_offers['flights']):
            if offer['id'] == monitor_id:
                monitored_offers['flights'].pop(i)
                return jsonify({
                    "success": True,
                    "message": "Oferta de voo removida do monitoramento com sucesso"
                })
                
        # Buscar e remover da lista de hotéis
        for i, offer in enumerate(monitored_offers['hotels']):
            if offer['id'] == monitor_id:
                monitored_offers['hotels'].pop(i)
                return jsonify({
                    "success": True,
                    "message": "Oferta de hotel removida do monitoramento com sucesso"
                })
                
        return jsonify({
            "error": "Oferta não encontrada"
        }), 404
        
    except Exception as e:
        logging.error(f"Erro ao remover oferta do monitoramento: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao remover a oferta do monitoramento",
            "details": str(e)
        }), 500

@app.route('/api/price-monitor/check', methods=['POST'])
def check_prices():
    """Verifica os preços das ofertas monitoradas"""
    global monitored_offers, price_alerts
    
    try:
        now = datetime.now().isoformat()
        results = {
            "flights": {
                "checked": 0,
                "updated": 0,
                "errors": 0
            },
            "hotels": {
                "checked": 0,
                "updated": 0,
                "errors": 0
            },
            "alerts": []
        }
        
        # Verificar voos
        for offer in monitored_offers['flights']:
            results['flights']['checked'] += 1
            
            try:
                # Em produção, usaríamos a API Amadeus para verificar o preço atual
                # Aqui, vamos simular uma pequena variação de preço aleatória
                if 'current_price' in offer and offer['current_price']:
                    # Simular uma queda de preço para demonstração
                    import random
                    change = random.uniform(-0.15, 0.05)  # Tendência para queda
                    new_price = offer['current_price'] * (1 + change)
                    
                    # Registrar o novo preço
                    offer['last_checked'] = now
                    offer['price_history'].append({
                        "date": now,
                        "price": new_price
                    })
                    
                    # Atualizar preço atual
                    old_price = offer['current_price']
                    offer['current_price'] = new_price
                    
                    # Atualizar o menor preço, se aplicável
                    if new_price < offer['lowest_price']:
                        offer['lowest_price'] = new_price
                    
                    # Se houve queda significativa no preço, criar alerta
                    if new_price < old_price * 0.95:  # 5% de queda
                        alert = {
                            "id": str(uuid.uuid4()),
                            "type": "price_drop",
                            "offer_type": "flight",
                            "offer_id": offer['id'],
                            "offer_data": offer['data'],
                            "old_price": old_price,
                            "new_price": new_price,
                            "currency": offer.get('currency', 'BRL'),
                            "date": now,
                            "read": False
                        }
                        price_alerts.append(alert)
                        results['alerts'].append(alert)
                    
                    results['flights']['updated'] += 1
            except Exception as e:
                logging.error(f"Erro ao verificar preço do voo {offer['id']}: {str(e)}")
                results['flights']['errors'] += 1
        
        # Verificar hotéis
        for offer in monitored_offers['hotels']:
            results['hotels']['checked'] += 1
            
            try:
                # Mesma lógica da simulação para voos
                if 'current_price' in offer and offer['current_price']:
                    import random
                    change = random.uniform(-0.12, 0.03)  # Tendência para queda
                    new_price = offer['current_price'] * (1 + change)
                    
                    # Registrar o novo preço
                    offer['last_checked'] = now
                    offer['price_history'].append({
                        "date": now,
                        "price": new_price
                    })
                    
                    # Atualizar preço atual
                    old_price = offer['current_price']
                    offer['current_price'] = new_price
                    
                    # Atualizar o menor preço, se aplicável
                    if new_price < offer['lowest_price']:
                        offer['lowest_price'] = new_price
                    
                    # Se houve queda significativa no preço, criar alerta
                    if new_price < old_price * 0.93:  # 7% de queda
                        alert = {
                            "id": str(uuid.uuid4()),
                            "type": "price_drop",
                            "offer_type": "hotel",
                            "offer_id": offer['id'],
                            "offer_data": offer['data'],
                            "old_price": old_price,
                            "new_price": new_price,
                            "currency": offer.get('currency', 'BRL'),
                            "date": now,
                            "read": False
                        }
                        price_alerts.append(alert)
                        results['alerts'].append(alert)
                    
                    results['hotels']['updated'] += 1
            except Exception as e:
                logging.error(f"Erro ao verificar preço do hotel {offer['id']}: {str(e)}")
                results['hotels']['errors'] += 1
        
        return jsonify(results)
        
    except Exception as e:
        logging.error(f"Erro ao verificar preços: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao verificar os preços",
            "details": str(e)
        }), 500

@app.route('/api/price-alerts', methods=['GET'])
def get_price_alerts():
    """Retorna todos os alertas de preço"""
    return jsonify(price_alerts)

@app.route('/api/price-alerts/mark-read', methods=['POST'])
def mark_alerts_read():
    """Marca todos os alertas como lidos"""
    global price_alerts
    
    try:
        data = request.json
        alert_ids = data.get('alert_ids', [])
        
        if not alert_ids:
            # Se não há IDs específicos, marcar todos como lidos
            for alert in price_alerts:
                alert['read'] = True
        else:
            # Marcar apenas os alertas específicos
            for alert in price_alerts:
                if alert['id'] in alert_ids:
                    alert['read'] = True
        
        return jsonify({
            "success": True,
            "message": "Alertas marcados como lidos com sucesso"
        })
        
    except Exception as e:
        logging.error(f"Erro ao marcar alertas como lidos: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao marcar os alertas como lidos",
            "details": str(e)
        }), 500

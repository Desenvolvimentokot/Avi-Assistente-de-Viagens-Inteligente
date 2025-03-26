import os
import logging
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

# Importação dos serviços e modelos
from services.amadeus_service import AmadeusService
from services.openai_service import OpenAIService
from models import db, User, Conversation, Message, TravelPlan, PriceMonitor, PriceHistory, PriceAlert

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Inicializa os serviços
amadeus_service = AmadeusService()
openai_service = OpenAIService()

# Cria as tabelas do banco de dados
with app.app_context():
    db.create_all()
    
    # Criar um usuário padrão se não existir nenhum
    if User.query.count() == 0:
        default_user = User(
            name="João Silva",
            email="joao.silva@exemplo.com",
            phone="+55 11 98765-4321",
            preferred_destinations="Praia, Montanha",
            accommodation_type="Hotel",
            budget="Médio"
        )
        default_user.set_password("senha123")
        db.session.add(default_user)
        
        # Adicionar uma conversa inicial
        conv = Conversation(
            user=default_user,
            title="Viagem para Paris",
            last_updated=datetime.utcnow()
        )
        db.session.add(conv)
        
        # Adicionar mensagens à conversa
        msg1 = Message(
            conversation=conv,
            is_user=True,
            content="Olá, estou planejando uma viagem para Paris.",
            timestamp=datetime.utcnow()
        )
        db.session.add(msg1)
        
        msg2 = Message(
            conversation=conv,
            is_user=False,
            content="Paris é um destino maravilhoso! A melhor época para visitar é na primavera (abril a junho) ou no outono (setembro a novembro). Gostaria que eu sugerisse algumas acomodações ou atividades?",
            timestamp=datetime.utcnow()
        )
        db.session.add(msg2)
        
        # Adicionar um plano de viagem
        plan = TravelPlan(
            user=default_user,
            title="Final de semana em Barcelona",
            destination="Barcelona, Espanha",
            start_date=datetime.strptime("2023-12-15", "%Y-%m-%d").date(),
            end_date=datetime.strptime("2023-12-17", "%Y-%m-%d").date(),
            details="Um fim de semana para explorar a arquitetura e a culinária de Barcelona."
        )
        db.session.add(plan)
        
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        })
    
    return jsonify({"error": "Email ou senha inválidos"}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"success": True})

@app.route('/api/conversations')
@login_required
def get_conversations():
    user_conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.last_updated.desc()).all()
    
    result = []
    for conv in user_conversations:
        result.append({
            "id": conv.id,
            "title": conv.title,
            "last_updated": conv.last_updated.strftime("%d/%m/%Y")
        })
    
    return jsonify(result)

@app.route('/api/conversation/<int:conversation_id>/messages')
@login_required
def get_conversation_messages(conversation_id):
    conv = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
    if not conv:
        return jsonify({"error": "Conversa não encontrada"}), 404
    
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
    
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "is_user": msg.is_user,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        })
    
    return jsonify(result)

@app.route('/api/plans')
@login_required
def get_plans():
    user_plans = TravelPlan.query.filter_by(user_id=current_user.id).order_by(TravelPlan.updated_at.desc()).all()
    
    result = []
    for plan in user_plans:
        result.append({
            "id": plan.id,
            "title": plan.title,
            "destination": plan.destination,
            "start_date": plan.start_date.strftime("%d/%m/%Y") if plan.start_date else None,
            "end_date": plan.end_date.strftime("%d/%m/%Y") if plan.end_date else None,
            "details": plan.details
        })
    
    return jsonify(result)

@app.route('/api/plan/<int:plan_id>')
@login_required
def get_plan(plan_id):
    plan = TravelPlan.query.filter_by(id=plan_id, user_id=current_user.id).first()
    
    if not plan:
        return jsonify({"error": "Plano não encontrado"}), 404
    
    # Buscar voos associados
    flights_data = []
    for flight in plan.flights:
        flights_data.append({
            "id": flight.id,
            "airline": flight.airline,
            "flight_number": flight.flight_number,
            "departure_location": flight.departure_location,
            "arrival_location": flight.arrival_location,
            "departure_time": flight.departure_time.isoformat() if flight.departure_time else None,
            "arrival_time": flight.arrival_time.isoformat() if flight.arrival_time else None,
            "price": flight.price,
            "currency": flight.currency
        })
    
    # Buscar acomodações associadas
    accommodations_data = []
    for acc in plan.accommodations:
        accommodations_data.append({
            "id": acc.id,
            "name": acc.name,
            "location": acc.location,
            "check_in": acc.check_in.strftime("%d/%m/%Y") if acc.check_in else None,
            "check_out": acc.check_out.strftime("%d/%m/%Y") if acc.check_out else None,
            "price_per_night": acc.price_per_night,
            "currency": acc.currency,
            "stars": acc.stars
        })
    
    result = {
        "id": plan.id,
        "title": plan.title,
        "destination": plan.destination,
        "start_date": plan.start_date.strftime("%d/%m/%Y") if plan.start_date else None,
        "end_date": plan.end_date.strftime("%d/%m/%Y") if plan.end_date else None,
        "details": plan.details,
        "flights": flights_data,
        "accommodations": accommodations_data
    }
    
    return jsonify(result)

@app.route('/api/profile')
@login_required
def get_profile():
    user = current_user
    
    profile = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "preferences": {
            "preferred_destinations": user.preferred_destinations,
            "accommodation_type": user.accommodation_type,
            "budget": user.budget
        }
    }
    
    return jsonify(profile)

@app.route('/api/profile', methods=['POST'])
@login_required
def update_profile():
    user = current_user
    data = request.json
    
    # Update only the provided fields
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    if 'preferences' in data:
        preferences = data['preferences']
        if 'preferred_destinations' in preferences:
            user.preferred_destinations = preferences['preferred_destinations']
        if 'accommodation_type' in preferences:
            user.accommodation_type = preferences['accommodation_type']
        if 'budget' in preferences:
            user.budget = preferences['budget']
    
    db.session.commit()
    
    return jsonify({
        "success": True, 
        "profile": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "preferences": {
                "preferred_destinations": user.preferred_destinations,
                "accommodation_type": user.accommodation_type,
                "budget": user.budget
            }
        }
    })

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    user_message = data.get('message', '')
    conversation_id = data.get('conversation_id')
    
    # Obter histórico da conversa, se existir
    messages_history = []
    
    if conversation_id:
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
        if not conversation:
            return jsonify({"error": "Conversa não encontrada"}), 404
            
        # Buscar mensagens da conversa
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
        for msg in messages:
            messages_history.append({
                "is_user": msg.is_user,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            })
    
    try:
        # Chamar a API da OpenAI através do nosso serviço
        result = openai_service.travel_assistant(user_message, messages_history)
        
        if 'error' in result:
            logging.error(f"Erro na API do OpenAI: {result['error']}")
            return jsonify({
                "response": "Desculpe, estou enfrentando problemas para processar sua solicitação no momento. Por favor, tente novamente mais tarde.",
                "error": result['error']
            }), 500
        
        # Se for uma nova conversa, criar uma nova entrada no banco de dados
        if not conversation_id:
            title = user_message[:30] + "..." if len(user_message) > 30 else user_message
            new_conversation = Conversation(
                user_id=current_user.id,
                title=title,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            db.session.add(new_conversation)
            db.session.flush()  # Para obter o ID da nova conversa
            conversation_id = new_conversation.id
            conversation = new_conversation
        else:
            # Atualizar o timestamp da conversa existente
            conversation.last_updated = datetime.utcnow()
        
        # Adicionar mensagem do usuário ao banco de dados
        user_msg = Message(
            conversation_id=conversation_id,
            is_user=True,
            content=user_message,
            timestamp=datetime.utcnow()
        )
        db.session.add(user_msg)
        
        # Adicionar resposta do assistente ao banco de dados
        assistant_response = result['response']
        assistant_msg = Message(
            conversation_id=conversation_id,
            is_user=False,
            content=assistant_response,
            timestamp=datetime.utcnow()
        )
        db.session.add(assistant_msg)
        
        # Commit das alterações
        db.session.commit()
        
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
@login_required
def get_monitored_offers():
    """Retorna todas as ofertas monitoradas"""
    user_monitors = PriceMonitor.query.filter_by(user_id=current_user.id).all()
    user_alerts = PriceAlert.query.join(PriceMonitor).filter(PriceMonitor.user_id == current_user.id).order_by(PriceAlert.date.desc()).all()
    
    flights = []
    hotels = []
    
    # Organizar monitores por tipo
    for monitor in user_monitors:
        item = {
            "id": monitor.id,
            "type": monitor.type,
            "name": monitor.name,
            "description": monitor.description,
            "original_price": monitor.original_price,
            "current_price": monitor.current_price,
            "lowest_price": monitor.lowest_price,
            "currency": monitor.currency,
            "date_added": monitor.date_added.isoformat(),
            "last_checked": monitor.last_checked.isoformat(),
            "data": monitor.offer_data
        }
        
        # Adicionar histórico de preços
        price_history = []
        for history in monitor.price_history:
            price_history.append({
                "date": history.date.isoformat(),
                "price": history.price
            })
        item["price_history"] = price_history
        
        if monitor.type == 'flight':
            flights.append(item)
        else:
            hotels.append(item)
    
    # Processar alertas
    alerts = []
    for alert in user_alerts:
        monitor = alert.monitor
        alerts.append({
            "id": alert.id,
            "monitor_id": alert.monitor_id,
            "type": monitor.type,
            "name": monitor.name,
            "description": monitor.description,
            "old_price": alert.old_price,
            "new_price": alert.new_price,
            "currency": monitor.currency,
            "date": alert.date.isoformat(),
            "read": alert.read
        })
    
    return jsonify({
        "flights": flights,
        "hotels": hotels,
        "alerts": alerts
    })

@app.route('/api/price-monitor', methods=['POST'])
@login_required
def add_monitored_offer():
    """Adiciona uma oferta ao monitoramento de preços"""
    try:
        data = request.json
        offer_type = data.get('type')  # 'flight' ou 'hotel'
        offer_data = data.get('data')
        
        if not offer_type or not offer_data:
            return jsonify({"error": "Tipo de oferta e dados são obrigatórios"}), 400
            
        if offer_type not in ['flight', 'hotel']:
            return jsonify({"error": "Tipo de oferta inválido. Use 'flight' ou 'hotel'"}), 400
        
        now = datetime.utcnow()
        name = ""
        description = ""
        price = None
        currency = "BRL"
        
        # Extrair dados específicos com base no tipo de oferta
        if offer_type == 'flight':
            # Nome: Companhia aérea + número do voo
            if 'airline' in offer_data and 'flight_number' in offer_data:
                name = f"{offer_data['airline']} {offer_data['flight_number']}"
            
            # Descrição: Origem-Destino
            if 'departure' in offer_data and 'arrival' in offer_data:
                description = f"{offer_data['departure']} → {offer_data['arrival']}"
            
            # Preço: extrair valor numérico e moeda
            if 'price' in offer_data:
                price_str = offer_data['price']
                parts = price_str.split(' ')
                if len(parts) == 2:
                    try:
                        price = float(parts[0])
                        currency = parts[1]
                    except ValueError:
                        pass
                        
        elif offer_type == 'hotel':
            # Nome: Nome do hotel
            if 'name' in offer_data:
                name = offer_data['name']
            
            # Descrição: Localização
            if 'location' in offer_data:
                description = offer_data['location']
            
            # Preço: extrair valor numérico e moeda
            if 'price_per_night' in offer_data:
                price_str = offer_data['price_per_night']
                parts = price_str.split(' ')
                if len(parts) == 2:
                    try:
                        price = float(parts[0])
                        currency = parts[1]
                    except ValueError:
                        pass
        
        # Se não conseguimos extrair um preço, retornar erro
        if price is None:
            return jsonify({
                "error": "Não foi possível extrair o preço da oferta"
            }), 400
        
        # Criar a entrada de monitoramento no banco de dados
        monitor = PriceMonitor(
            user_id=current_user.id,
            type=offer_type,
            item_id=str(offer_data.get('id', '')),
            name=name,
            description=description,
            original_price=price,
            current_price=price,
            lowest_price=price,
            currency=currency,
            date_added=now,
            last_checked=now,
            offer_data=offer_data
        )
        db.session.add(monitor)
        db.session.flush()  # Para obter o ID
        
        # Adicionar o primeiro registro de histórico de preço
        price_history = PriceHistory(
            monitor_id=monitor.id,
            price=price,
            date=now
        )
        db.session.add(price_history)
        
        # Commit das alterações
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Oferta adicionada ao monitoramento com sucesso",
            "monitor_id": monitor.id
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao adicionar oferta ao monitoramento: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao adicionar a oferta ao monitoramento",
            "details": str(e)
        }), 500

@app.route('/api/price-monitor/<int:monitor_id>', methods=['DELETE'])
@login_required
def remove_monitored_offer(monitor_id):
    """Remove uma oferta do monitoramento de preços"""
    try:
        # Buscar o monitor no banco de dados
        monitor = PriceMonitor.query.filter_by(id=monitor_id, user_id=current_user.id).first()
        
        if not monitor:
            return jsonify({
                "error": "Oferta monitorada não encontrada"
            }), 404
        
        # Definir o tipo para a mensagem de sucesso
        offer_type = "voo" if monitor.type == "flight" else "hotel"
        
        # Remover o monitor e seus dados associados (histórico e alertas serão removidos em cascata)
        db.session.delete(monitor)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Oferta de {offer_type} removida do monitoramento com sucesso"
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao remover oferta do monitoramento: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao remover a oferta do monitoramento",
            "details": str(e)
        }), 500

@app.route('/api/price-monitor/check', methods=['POST'])
@login_required
def check_prices():
    """Verifica os preços das ofertas monitoradas"""
    try:
        now = datetime.utcnow()
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
        
        # Buscar monitores de preço do usuário
        user_monitors = PriceMonitor.query.filter_by(user_id=current_user.id).all()
        
        # Processar cada monitor
        for monitor in user_monitors:
            # Incrementar contadores
            if monitor.type == 'flight':
                results['flights']['checked'] += 1
                category = 'flights'
                threshold = 0.95  # 5% de queda para voos
            else:
                results['hotels']['checked'] += 1
                category = 'hotels'
                threshold = 0.93  # 7% de queda para hotéis
            
            try:
                # Em produção, usaríamos a API Amadeus para verificar o preço atual
                # Aqui, vamos simular uma pequena variação de preço aleatória
                if monitor.current_price:
                    # Simular uma queda de preço para demonstração
                    import random
                    change = random.uniform(-0.15, 0.05)  # Tendência para queda
                    new_price = monitor.current_price * (1 + change)
                    
                    # Atualizar preço atual
                    old_price = monitor.current_price
                    monitor.current_price = new_price
                    monitor.last_checked = now
                    
                    # Adicionar ao histórico de preços
                    price_history = PriceHistory(
                        monitor_id=monitor.id,
                        price=new_price,
                        date=now
                    )
                    db.session.add(price_history)
                    
                    # Atualizar o menor preço, se aplicável
                    if new_price < monitor.lowest_price:
                        monitor.lowest_price = new_price
                    
                    # Se houve queda significativa no preço, criar alerta
                    if new_price < old_price * threshold:
                        alert = PriceAlert(
                            monitor_id=monitor.id,
                            old_price=old_price,
                            new_price=new_price,
                            date=now,
                            read=False
                        )
                        db.session.add(alert)
                        db.session.flush()  # Para obter o ID
                        
                        # Adicionar aos resultados
                        results['alerts'].append({
                            "id": alert.id,
                            "monitor_id": monitor.id,
                            "type": monitor.type,
                            "name": monitor.name,
                            "description": monitor.description,
                            "old_price": old_price,
                            "new_price": new_price,
                            "currency": monitor.currency,
                            "date": now.isoformat(),
                            "read": False
                        })
                    
                    results[category]['updated'] += 1
            except Exception as e:
                db.session.rollback()
                logging.error(f"Erro ao verificar preço do item {monitor.id}: {str(e)}")
                results[category]['errors'] += 1
                continue
        
        # Commit das alterações
        db.session.commit()
        
        return jsonify(results)
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao verificar preços: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao verificar os preços",
            "details": str(e)
        }), 500

@app.route('/api/price-alerts', methods=['GET'])
@login_required
def get_price_alerts():
    """Retorna todos os alertas de preço do usuário atual"""
    try:
        # Buscar alertas de preço do usuário atual
        user_alerts = PriceAlert.query.join(PriceMonitor).filter(
            PriceMonitor.user_id == current_user.id
        ).order_by(PriceAlert.date.desc()).all()
        
        # Formatar resposta
        alerts = []
        for alert in user_alerts:
            monitor = alert.monitor
            alerts.append({
                "id": alert.id,
                "monitor_id": alert.monitor_id,
                "type": monitor.type,
                "name": monitor.name,
                "description": monitor.description,
                "old_price": alert.old_price,
                "new_price": alert.new_price,
                "currency": monitor.currency,
                "date": alert.date.isoformat(),
                "read": alert.read
            })
        
        return jsonify(alerts)
        
    except Exception as e:
        logging.error(f"Erro ao buscar alertas de preço: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao buscar os alertas de preço",
            "details": str(e)
        }), 500

@app.route('/api/price-alerts/mark-read', methods=['POST'])
@login_required
def mark_alerts_read():
    """Marca alertas como lidos"""
    try:
        data = request.json
        alert_ids = data.get('alert_ids', [])
        
        # Preparar a consulta para obter apenas alertas do usuário atual
        query = PriceAlert.query.join(PriceMonitor).filter(
            PriceMonitor.user_id == current_user.id
        )
        
        if alert_ids:
            # Se há IDs específicos, adicionar filtro
            query = query.filter(PriceAlert.id.in_(alert_ids))
        
        # Buscar e atualizar alertas
        alerts = query.all()
        for alert in alerts:
            alert.read = True
        
        # Commit das alterações
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Alertas marcados como lidos com sucesso",
            "count": len(alerts)
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao marcar alertas como lidos: {str(e)}")
        return jsonify({
            "error": "Ocorreu um erro ao marcar os alertas como lidos",
            "details": str(e)
        }), 500

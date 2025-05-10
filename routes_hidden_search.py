"""
Módulo para implementação da busca oculta de voos usando iframe invisível
Esta abordagem permite obter dados reais de voos sem usar um navegador headless no servidor.
"""

import json
import uuid
import logging
from flask import Blueprint, request, jsonify, render_template, session, current_app, make_response

# Configurar logger
logger = logging.getLogger(__name__)

# Criar Blueprint
hidden_search_bp = Blueprint('hidden_search', __name__)

@hidden_search_bp.route('/hidden-search')
def hidden_search():
    """
    Renderiza a página com o widget oculto de busca de voos.
    Esta página usa um iframe invisível para carregar o widget Trip.com
    e capturar os resultados.
    """
    logger.info("Acessando página de busca oculta")
    return render_template('hidden_flight_search.html')

@hidden_search_bp.route('/trip-com-test')
def trip_com_test():
    """
    Renderiza a página de teste da integração com o Trip.com.
    Esta página permite testar os diferentes componentes da integração.
    """
    logger.info("Acessando página de teste da integração Trip.com")
    return render_template('trip_com_test.html')

@hidden_search_bp.route('/api/hidden-flight-search', methods=['POST'])
def start_hidden_flight_search():
    """
    Inicia uma busca oculta de voos.
    
    Request JSON:
    {
        "origin": "GRU",
        "destination": "JFK",
        "departure_date": "2025-06-01",
        "return_date": "2025-06-15",  // opcional
        "adults": 1  // opcional, padrão é 1
    }
    
    Response:
    {
        "success": true,
        "message": "Buscando voos...",
        "action": "open_hidden_frame",
        "url": "/hidden-search?origin=GRU&destination=JFK...",
        "session_id": "uuid-string"
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Dados ausentes no corpo da requisição"
            }), 400
        
        # Extrair parâmetros
        origin = data.get('origin')
        destination = data.get('destination')
        departure_date = data.get('departure_date')
        return_date = data.get('return_date', '')
        adults = data.get('adults', 1)
        
        # Validar parâmetros obrigatórios
        if not origin or not destination or not departure_date:
            return jsonify({
                "success": False,
                "message": "Parâmetros obrigatórios ausentes (origin, destination, departure_date)"
            }), 400
        
        # Obter ou gerar ID de sessão
        session_id = request.cookies.get('flai_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Gerar URL para a página oculta
        search_url = f"/hidden-search?origin={origin}&destination={destination}&departure_date={departure_date}"
        
        if return_date:
            search_url += f"&return_date={return_date}"
            
        search_url += f"&adults={adults}&session_id={session_id}"
        
        logger.info(f"Iniciando busca oculta: {search_url}")
        
        # Resposta para o frontend
        return jsonify({
            "success": True,
            "message": "Buscando voos...",
            "action": "open_hidden_frame",
            "url": search_url,
            "session_id": session_id
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar busca oculta: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao iniciar busca: {str(e)}"
        }), 500

@hidden_search_bp.route('/api/hidden-search/notify-search-started', methods=['POST'])
def notify_search_started():
    """
    Notifica o servidor que uma busca automática foi iniciada.
    Isso permite acompanhar o progresso da busca no chat.
    
    Request JSON:
    {
        "session_id": "uuid-string",
        "origin": "GRU",
        "destination": "JFK",
        "departure_date": "2025-06-01",
        "return_date": "2025-06-15",
        "adults": 1,
        "search_url": "https://br.trip.com/flights/..."
    }
    
    Response:
    {
        "success": true,
        "message": "Busca iniciada com sucesso"
    }
    """
    try:
        data = request.json
        
        if not data or not data.get('session_id'):
            return jsonify({
                "success": False,
                "message": "Dados de sessão não fornecidos"
            }), 400
        
        session_id = data.get('session_id')
        
        # Armazenar informações da busca
        search_info = {
            'status': 'em_andamento',
            'progress': 20,
            'origin': data.get('origin'),
            'destination': data.get('destination'),
            'departure_date': data.get('departure_date'),
            'return_date': data.get('return_date'),
            'adults': data.get('adults'),
            'search_url': data.get('search_url'),
            'timestamp': current_app.config.get('server_time', 0),
            'message': 'Buscando voos automaticamente...'
        }
        
        # Salvar no config da aplicação
        if 'searches_in_progress' not in current_app.config:
            current_app.config['searches_in_progress'] = {}
        
        current_app.config['searches_in_progress'][session_id] = search_info
        
        # Tentar adicionar mensagem de busca em andamento ao chat (se a função estiver disponível)
        try:
            from services.chat_service import add_system_message
            message = f"⏳ **Buscando voos automaticamente...**\n\nEstou buscando as melhores opções de voos de {search_info['origin']} para {search_info['destination']}. Por favor, aguarde um momento enquanto consulto os preços mais atualizados."
            add_system_message(session_id, message)
            logger.info(f"Mensagem de busca em andamento adicionada ao chat para sessão {session_id}")
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem ao chat: {str(e)}")
        
        # Registrar no log
        logger.info(f"Busca de voos iniciada para sessão {session_id}: {data.get('origin')} → {data.get('destination')}")
        
        return jsonify({
            "success": True,
            "message": "Busca iniciada com sucesso"
        })
    except Exception as e:
        logger.error(f"Erro ao notificar início da busca: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao notificar início da busca: {str(e)}"
        }), 500

@hidden_search_bp.route('/api/save-flight-results', methods=['POST'])  # Rota antiga para compatibilidade
@hidden_search_bp.route('/api/hidden-search/save-results', methods=['POST'])
def save_flight_results():
    """
    Salva os resultados de voos encontrados pelo processo de busca automática.
    
    Request JSON:
    {
        "flights": [...],  // array de objetos de voos
        "session_id": "uuid-string",
        "url": "https://br.trip.com/flights/..."
    }
    
    Response:
    {
        "success": true,
        "message": "Resultados salvos com sucesso",
        "redirect_url": "/chat"
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Dados ausentes no corpo da requisição"
            }), 400
        
        # Extrair parâmetros
        flights = data.get('flights', [])
        session_id = data.get('session_id')
        trip_url = data.get('url', '')
        
        if not flights or not session_id:
            return jsonify({
                "success": False,
                "message": "Parâmetros inválidos (flights, session_id)"
            }), 400
        
        logger.info(f"Recebidos {len(flights)} resultados para sessão {session_id}")
        
        # Formatar os resultados
        formatted_flights = []
        for flight in flights:
            try:
                # A estrutura exata pode variar dependendo da fonte dos dados
                formatted_flight = {
                    "airline": flight.get('airline', 'Desconhecida'),
                    "flight_number": flight.get('flight_number', ''),
                    "origin": flight.get('origin', ''),
                    "destination": flight.get('destination', ''),
                    "departure_date": flight.get('departure_date', ''),
                    "return_date": flight.get('return_date', ''),
                    "departure_time": flight.get('departure_time', ''),
                    "arrival_time": flight.get('arrival_time', ''),
                    "duration": flight.get('duration', ''),
                    "stops": flight.get('stops', ''),
                    "price": flight.get('price', 'R$ 0,00'),
                    "url": trip_url  # URL para visualizar/comprar o voo no Trip.com
                }
                formatted_flights.append(formatted_flight)
            except Exception as e:
                logger.error(f"Erro ao formatar voo: {str(e)}")
        
        # Salvar no config da aplicação
        if 'flight_results' not in current_app.config:
            current_app.config['flight_results'] = {}
        
        current_app.config['flight_results'][session_id] = formatted_flights
        
        # Atualizar status da busca
        if 'searches_in_progress' in current_app.config and session_id in current_app.config['searches_in_progress']:
            current_app.config['searches_in_progress'][session_id]['status'] = 'concluida'
            current_app.config['searches_in_progress'][session_id]['progress'] = 100
            current_app.config['searches_in_progress'][session_id]['message'] = 'Busca concluída!'
        
        # Tentar enviar resultados diretamente para o chat
        try:
            from services.chat_service import add_system_message
            
            # Gerar uma mensagem formatada com os resultados
            if len(formatted_flights) > 0:
                # Ordenar voos por preço
                sorted_flights = sorted(formatted_flights, 
                                      key=lambda x: float(x['price'].replace('R$ ', '').replace('.', '').replace(',', '.')))
                
                # Pegar os 2 mais baratos
                best_flights = sorted_flights[:2]
                
                # Construir mensagem
                message = "✅ **Encontrei opções de voos para você!**\n\n"
                
                for i, flight in enumerate(best_flights):
                    # Origem e destino
                    message += f"**Opção {i+1}: {flight['airline']}**\n"
                    message += f"🛫 {flight['origin']} → {flight['destination']}\n"
                    
                    # Datas
                    message += f"📅 Ida: {flight['departure_date']}\n"
                    if flight['return_date']:
                        message += f"🔙 Volta: {flight['return_date']}\n"
                    
                    # Horários e duração
                    if flight['departure_time'] and flight['arrival_time']:
                        message += f"⏰ Horário: {flight['departure_time']} - {flight['arrival_time']}\n"
                    if flight['duration']:
                        message += f"⏱️ Duração: {flight['duration']}\n"
                    if flight['stops']:
                        message += f"🛑 Escalas: {flight['stops']}\n"
                    
                    # Preço e link
                    message += f"💰 **Preço: {flight['price']}**\n"
                    message += f"[Clique aqui para comprar este voo]({flight['url']})\n\n"
                
                message += "Estas são as melhores opções que encontrei para você. Posso ajudar com mais alguma coisa?"
                
                # Adicionar ao chat
                add_system_message(session_id, message)
                logger.info(f"Mensagem com resultados de voos adicionada ao chat para sessão {session_id}")
            else:
                # Mensagem de nenhum resultado encontrado
                message = "❌ **Não encontrei voos para as datas selecionadas.**\n\nGostaria de tentar com outras datas ou destinos?"
                add_system_message(session_id, message)
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem ao chat: {str(e)}")
        
        logger.info(f"Resultados salvos para sessão {session_id}")
        
        # Resposta para o frontend
        return jsonify({
            "success": True,
            "message": "Resultados salvos com sucesso",
            "redirect_url": "/chat",
            "flights": formatted_flights
        })
        
    except Exception as e:
        logger.error(f"Erro ao salvar resultados: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao salvar resultados: {str(e)}"
        }), 500
        
@hidden_search_bp.route('/api/chat-flight-results', methods=['GET'])
def get_chat_flight_results():
    """
    Verifica se há resultados de voos disponíveis para o chat.
    
    Response:
    {
        "success": true,
        "message": "Resultados disponíveis",
        "results": [...],  // array de objetos de voos ou vazio
        "has_results": true/false
    }
    """
    try:
        # Obter ID de sessão
        session_id = request.cookies.get('flai_session_id')
        
        if not session_id:
            return jsonify({
                "success": False,
                "message": "Sessão não encontrada",
                "results": [],
                "has_results": False
            })
        
        logger.info(f"Verificando resultados para sessão {session_id}")
        
        # Verificar se há resultados para esta sessão
        results = []
        if 'flight_results' in current_app.config and session_id in current_app.config['flight_results']:
            results = current_app.config['flight_results'][session_id]
            
            # Limpar resultados após retorná-los
            del current_app.config['flight_results'][session_id]
            
            logger.info(f"Encontrados {len(results)} resultados para sessão {session_id}")
        
        # Criar resposta
        response = jsonify({
            "success": True,
            "message": "Resultados verificados com sucesso",
            "results": results,
            "has_results": len(results) > 0
        })
        
        # Garantir que a sessão seja mantida
        if session_id:
            response.set_cookie('flai_session_id', session_id, max_age=86400*30, httponly=True)
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao verificar resultados: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao verificar resultados: {str(e)}",
            "results": [],
            "has_results": False
        }), 500
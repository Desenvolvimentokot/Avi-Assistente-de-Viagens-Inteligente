import os
import logging
import json
import uuid
import re
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

# Importação dos serviços e modelos
from services.amadeus_sdk_service import AmadeusSDKService
from services.busca_rapida_service import BuscaRapidaService
from services.chat_processor import ChatProcessor
from services.openai_service import OpenAIService
from services.pdf_service import PDFService
from models import db, User, Conversation, Message, TravelPlan, FlightBooking, Accommodation, PriceMonitor, PriceHistory, PriceAlert

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.config["DEBUG"] = True

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///flai.db")
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
amadeus_service = AmadeusSDKService()
busca_rapida_service = BuscaRapidaService()
chat_processor = ChatProcessor()
openai_service = OpenAIService()

# Dicionário para armazenar histórico de conversas temporárias
# Estrutura: { 'session_id': { 'history': [], 'travel_info': {} } }
conversation_store = {}

# Rota principal
@app.route('/')
def index():
    return render_template('index.html', title='Avi - Assistente de Viagens Inteligente')

# API para chat
@app.route('/api/chat', methods=['POST'])
def chat():
    """Processa mensagens do chat"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        mode = data.get('mode', 'quick-search')
        session_id = data.get('session_id', str(uuid.uuid4()))
        client_history = data.get('history', [])

        if not message:
            return jsonify({"error": True, "message": "Mensagem vazia"})
            
        # Inicializa ou recupera a sessão do usuário
        if session_id not in conversation_store:
            conversation_store[session_id] = {
                'history': [],
                'travel_info': {}
            }
        
        # Usa o histórico armazenado no servidor, ou o enviado pelo cliente se disponível
        history = conversation_store[session_id]['history']
        if not history and client_history:
            history = client_history
            
        # Adiciona a mensagem atual ao histórico
        history.append({'user': message})

        if mode == 'quick-search':
            # Recuperar travel_info anterior, se existir
            current_travel_info = conversation_store[session_id].get('travel_info', {})
            
            # Transformar o histórico no formato esperado pelo OpenAI Service
            openai_history = []
            for msg in history:
                if 'user' in msg:
                    openai_history.append({'is_user': True, 'content': msg['user']})
                elif 'assistant' in msg:
                    openai_history.append({'is_user': False, 'content': msg['assistant']})
            
            # Análise do estágio atual do fluxo de conversação
            # 1. Se estamos extraindo informações inicialmente
            # 2. Se estamos confirmando os detalhes
            # 3. Se estamos buscando e apresentando resultados
            
            # Definir o contexto de sistema para a API do GPT com base no estágio
            step = current_travel_info.get('step', 0)
            
            # Extrair informações da mensagem antes para enriquecer o contexto
            travel_info = chat_processor.extract_travel_info(message)
            if travel_info:
                current_travel_info.update(travel_info)
                
            # Determinar se já temos informações suficientes para busca
            has_sufficient_info = False
            errors = chat_processor.validate_travel_info(current_travel_info)
            if not errors:
                has_sufficient_info = True
            
            # Preparar sistema de contexto específico para o GPT baseado no estágio
            system_context = ""
            
            if step == 0:  # Etapa de extração de informações
                # Informar o ChatGPT sobre o que já sabemos para ele focar no que falta
                missing_info = []
                for key, error in errors.items() if errors else {}:
                    missing_info.append(f"- {error}")
                
                if missing_info:
                    system_context = f"""
                    Estamos na etapa de coleta de informações para busca de voos.
                    As seguintes informações ainda precisam ser obtidas:
                    {chr(10).join(missing_info)}
                    
                    Solicite ao usuário essas informações de forma natural e conversacional.
                    NÃO SIMULE resultados de busca ou preços - não temos essas informações ainda.
                    """
                else:
                    # Temos todas as informações, vamos para a confirmação
                    current_travel_info['step'] = 1
                    step = 1
                    
                    # Formatar as informações para confirmar
                    summary = chat_processor.format_travel_info_summary(current_travel_info)
                    system_context = f"""
                    Temos todas as informações necessárias para busca:
                    {summary}
                    
                    Confirme estes detalhes com o usuário de forma natural antes de realizar a busca.
                    NÃO SIMULE resultados de busca ou preços - não temos essas informações ainda.
                    """
                    
            elif step == 1:  # Etapa de confirmação
                # Verificar se o usuário confirmou
                confirmation = False
                if "sim" in message.lower() or "confirmo" in message.lower() or "pode buscar" in message.lower() or "ok" in message.lower():
                    confirmation = True
                    
                if confirmation:
                    # Usuário confirmou, vamos buscar os voos
                    current_travel_info['confirmed'] = True
                    current_travel_info['step'] = 2
                    step = 2
                    system_context = """
                    O usuário confirmou as informações. Informe que você está buscando voos reais
                    através da API da Amadeus. Não forneça resultados simulados, apenas explique
                    que está consultando os dados reais.
                    """
                else:
                    # Continuar na etapa de confirmação
                    summary = chat_processor.format_travel_info_summary(current_travel_info)
                    system_context = f"""
                    Precisamos confirmar estas informações para busca:
                    {summary}
                    
                    Confirme estes detalhes com o usuário de forma natural antes de realizar a busca.
                    NÃO SIMULE resultados de busca ou preços - não temos essas informações ainda.
                    """
                    
            elif step == 2:  # Etapa de busca e apresentação de resultados
                # Se já buscamos antes, apenas continuar a conversa
                if current_travel_info.get('search_results'):
                    system_context = """
                    Já temos resultados de busca de voos. Responda às perguntas do usuário
                    usando apenas os dados reais que já foram obtidos.
                    """
                else:
                    # Forçar resposta fixa para busca na API
                    # Este é o ponto crítico: não permitimos que o GPT gere qualquer conteúdo
                    # Usamos uma resposta fixa e padronizada que será substituída pelos dados reais
                    gpt_response = "BUSCANDO_DADOS_REAIS_NA_API_AMADEUS"
                    gpt_result = {"response": gpt_response}
                    
                    # Pular o resto do processamento e ir direto para a busca real
                    skip_gpt_call = True
            
            # Verificar se devemos pular a chamada do GPT
            skip_gpt_call = locals().get('skip_gpt_call', False)
            
            if not skip_gpt_call:
                # Obter resposta do GPT com o contexto específico do estágio
                gpt_result = openai_service.travel_assistant(message, openai_history, system_context)
            
            # Inicializar gpt_result se ainda não existir (caso skip_gpt_call seja True)
            if not 'gpt_result' in locals():
                gpt_result = {"response": "BUSCANDO_DADOS_REAIS_NA_API_AMADEUS"}
            
            if 'error' in gpt_result:
                logging.error(f"Erro ao processar com GPT: {gpt_result['error']}")
                # Fallback para processamento direto
                current_context = {
                    'step': step,
                    'travel_info': current_travel_info,
                    'search_results': current_travel_info.get('search_results'),
                    'error': None
                }
                updated_context, response_text = busca_rapida_service.process_message(message, current_context)
            else:
                # O GPT ajudou a entender e estruturar a interação
                # Verifica se existe a chave 'response' no gpt_result
                if 'response' in gpt_result:
                    gpt_response = gpt_result['response']
                else:
                    # Se não existir, usa o valor padrão
                    gpt_response = "BUSCANDO_DADOS_REAIS_NA_API_AMADEUS"
                
                # Se estamos na etapa 2 e confirmado, realizar a busca real agora
                if step == 2 and current_travel_info.get('confirmed') and not current_travel_info.get('search_results'):
                    # Buscar voos reais da API
                    search_results = None
                    try:
                        # Detectar o tipo de busca necessária (data específica ou período)
                        if current_travel_info.get('date_range_start') and current_travel_info.get('date_range_end'):
                            # Busca de período flexível
                            search_params = {
                                'originLocationCode': current_travel_info.get('origin'),
                                'destinationLocationCode': current_travel_info.get('destination'),
                                'departureDate': current_travel_info.get('date_range_start'),
                                'returnDate': current_travel_info.get('date_range_end'),
                                'adults': current_travel_info.get('adults', 1),
                                'currencyCode': 'BRL',
                                'max_dates_to_check': 3
                            }
                            search_results = amadeus_service.search_best_prices(search_params)
                        else:
                            # Busca de data específica
                            search_params = {
                                'originLocationCode': current_travel_info.get('origin'),
                                'destinationLocationCode': current_travel_info.get('destination'),
                                'departureDate': current_travel_info.get('departure_date'),
                                'adults': current_travel_info.get('adults', 1),
                                'currencyCode': 'BRL',
                                'max': 5
                            }
                            
                            # Adicionar data de retorno se disponível
                            if current_travel_info.get('return_date'):
                                search_params['returnDate'] = current_travel_info.get('return_date')
                                
                            search_results = amadeus_service.search_flights(search_params)
                        
                        # Armazenar resultados da busca
                        current_travel_info['search_results'] = search_results
                        
                        # SOLUÇÃO DEFINITIVA:
                        # NÃO usamos o GPT para formatar a resposta, usamos apenas dados reais 
                        # controlados por nós através do ChatProcessor
                        
                        # Gerar introdução amigável para os resultados (sem dados simulados)
                        friendly_intro = chat_processor.get_flight_search_intro(
                            origin=current_travel_info.get('origin'),
                            destination=current_travel_info.get('destination')
                        )
                        
                        if 'error' in search_results:
                            # Formatar mensagem de erro usando o ChatProcessor (sem GPT)
                            error_message = chat_processor.format_error_message(search_results['error'])
                            response_text = f"{friendly_intro}\n\n{error_message}"
                        else:
                            # Formatar resultados reais de voos usando o BuscaRapidaService
                            flight_results = busca_rapida_service._format_search_results(search_results)
                            
                            # Montar resposta final com introdução + dados reais (sem GPT)
                            response_text = f"{friendly_intro}\n\n{flight_results}"
                    except Exception as e:
                        logging.error(f"Erro na busca de voos: {str(e)}")
                        response_text = f"{gpt_response}\n\nDesculpe, tive um problema técnico ao buscar voos: {str(e)}"
                else:
                    # Etapas 0 ou 1, ou sem confirmação - usar apenas a resposta do GPT
                    response_text = gpt_response
                
                # Atualizar o contexto
                updated_context = {
                    'step': step,
                    'travel_info': current_travel_info,
                    'search_results': current_travel_info.get('search_results'),
                    'error': None,
                    'gpt_response': gpt_response
                }
            
            # Armazena a resposta no histórico
            history.append({'assistant': response_text})
            
            # Atualizar travel_info com o contexto atualizado
            current_travel_info['step'] = updated_context['step']
            if updated_context.get('search_results'):
                current_travel_info['search_results'] = updated_context['search_results']
            
            # Construir a resposta
            response = {"response": response_text, "error": False}
            
            # Atualiza o armazenamento
            conversation_store[session_id]['history'] = history
            conversation_store[session_id]['travel_info'] = current_travel_info
            
            # Adiciona session_id na resposta
            response['session_id'] = session_id
            
            return jsonify(response)
        else:
            # Implementar lógica para planejamento completo
            response = {"response": "Modo de planejamento completo em desenvolvimento."}
            history.append({'assistant': response['response']})
            conversation_store[session_id]['history'] = history
            response['session_id'] = session_id
            
            return jsonify(response)

    except Exception as e:
        print(f"Erro na API de chat: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": True, "message": "Erro ao processar a solicitação"})

# API para busca
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
                            "price": f"{currency} {price}",
                            "departure": {
                                "airport": first_segment['departure']['iataCode'],
                                "time": first_segment['departure']['at']
                            },
                            "arrival": {
                                "airport": last_segment['arrival']['iataCode'],
                                "time": last_segment['arrival']['at']
                            },
                            "duration": itinerary['duration'],
                            "segments": len(itinerary['segments'])
                        }
                        flights.append(flight)
                    except (KeyError, IndexError) as e:
                        logging.error(f"Erro ao processar oferta de voo: {str(e)}")

            return jsonify({"flights": flights})

        elif search_type == 'hotels':
            # Chamar a API da Amadeus
            result = amadeus_service.search_hotels(search_params)

            if 'error' in result:
                logging.error(f"Erro na busca de hotéis: {result['error']}")
                return jsonify({
                    "error": "Não foi possível buscar hotéis no momento",
                    "details": result['error']
                }), 500

            # Formatar os resultados da API
            hotels = []
            if 'data' in result:
                for hotel in result['data']:
                    try:
                        hotel_info = {
                            "id": hotel['hotelId'],
                            "name": hotel['name'],
                            "address": hotel.get('address', {}).get('lines', ["Endereço não disponível"])[0],
                            "city": hotel.get('address', {}).get('cityName', ""),
                            "country": hotel.get('address', {}).get('countryCode', "")
                        }
                        hotels.append(hotel_info)
                    except KeyError as e:
                        logging.error(f"Erro ao processar hotel: {str(e)}")

            return jsonify({"hotels": hotels})

        else:
            return jsonify({"error": "Tipo de busca não suportado"}), 400

    except Exception as e:
        logging.error(f"Erro na API de busca: {str(e)}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

# Rota para criar banco de dados (setup inicial)
@app.route('/setup', methods=['GET'])
def setup():
    try:
        db.create_all()
        return jsonify({"message": "Banco de dados inicializado com sucesso"})
    except Exception as e:
        return jsonify({"error": f"Erro ao inicializar banco de dados: {str(e)}"}), 500

# Rotas para API de conversas
@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    try:
        # Para testes, usar ID fixo de usuário
        user_id = 1
        conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.created_at.desc()).all()

        result = []
        for conv in conversations:
            result.append({
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat()
            })

        return jsonify({"conversations": result})
    except Exception as e:
        logging.error(f"Erro ao buscar conversas: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Rota para obter uma conversa específica
@app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    try:
        conversation = Conversation.query.get(conversation_id)

        if not conversation:
            return jsonify({"error": "Conversa não encontrada"}), 404

        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()

        messages_list = []
        for msg in messages:
            messages_list.append({
                "id": msg.id,
                "content": msg.content,
                "is_user": msg.is_user,
                "timestamp": msg.timestamp.isoformat()
            })

        return jsonify({
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "messages": messages_list
        })
    except Exception as e:
        logging.error(f"Erro ao buscar conversa: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
def get_conversations_login_required():
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

@app.route('/api/plan/<int:plan_id>/pdf')
@login_required
def download_plan_pdf(plan_id):
    from services.pdf_service import PDFService
    from flask import send_file

    plan = TravelPlan.query.filter_by(id=plan_id, user_id=current_user.id).first()

    if not plan:
        return jsonify({"error": "Plano não encontrado"}), 404

    # Preparar dados para o PDF
    plan_data = {
        "id": plan.id,
        "title": plan.title,
        "destination": plan.destination,
        "start_date": plan.start_date.isoformat() if plan.start_date else None,
        "end_date": plan.end_date.isoformat() if plan.end_date else None,
        "details": plan.details,
        "flights": [],
        "accommodations": []
    }

    # Adicionar voos
    for flight in plan.flights:
        plan_data["flights"].append({
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

    # Adicionar acomodações
    for acc in plan.accommodations:
        plan_data["accommodations"].append({
            "id": acc.id,
            "name": acc.name,
            "location": acc.location,
            "check_in": acc.check_in.isoformat() if acc.check_in else None,
            "check_out": acc.check_out.isoformat() if acc.check_out else None,
            "price_per_night": acc.price_per_night,
            "currency": acc.currency,
            "stars": acc.stars
        })

    # Verificar se o usuário é premium
    is_premium = False  # Implementação futura

    # Gerar PDF básico ou premium
    if is_premium:
        pdf_path = PDFService.generate_premium_pdf(plan_data, current_user)
    else:
        pdf_path = PDFService.generate_basic_pdf(plan_data, current_user)

    if not pdf_path:
        return jsonify({"error": "Erro ao gerar PDF"}), 500

    # Enviar o arquivo para download
    try:
        return send_file(
            pdf_path,
            download_name=f"plano_viagem_{plan.id}.pdf",
            as_attachment=True,
            mimetype='application/pdf'
        )
    finally:
        # Remover o arquivo temporário após envio
        import threading
        threading.Timer(60, PDFService.delete_pdf, args=[pdf_path]).start()

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
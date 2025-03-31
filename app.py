import os
import logging
import json
import uuid
import re
import time
import sqlalchemy.exc
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

# Importar o blueprint de rotas da API
from app_routes import api_blueprint

# Importação dos serviços e modelos
from services.amadeus_sdk_service import AmadeusSDKService
from services.busca_rapida_service import BuscaRapidaService
from services.chat_processor import ChatProcessor
from services.openai_service import OpenAIService
from services.pdf_service import PDFService
from models import db, User, Conversation, Message, TravelPlan, FlightBooking, Accommodation, PriceMonitor, PriceHistory, PriceAlert

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Funções auxiliares para lidar com erros de banco de dados
def db_operation_with_retry(operation_func, max_retries=3, retry_delay=0.5):
    """
    Executa uma operação de banco de dados com tentativas de reconexão
    em caso de erros de conexão SSL ou outros problemas de conexão.

    Args:
        operation_func: Função que executa a operação de banco de dados
        max_retries: Número máximo de tentativas
        retry_delay: Tempo de espera entre tentativas (em segundos)

    Returns:
        O resultado da operação ou None se falhar em todas as tentativas
    """
    import time
    from sqlalchemy.exc import OperationalError, SQLAlchemyError
    import psycopg2

    retries = 0
    last_error = None

    while retries < max_retries:
        try:
            return operation_func()
        except (OperationalError, psycopg2.OperationalError) as e:
            # Identificar erros específicos de conexão SSL
            error_msg = str(e)
            if "SSL connection has been closed unexpectedly" in error_msg or "connection already closed" in error_msg:
                retries += 1
                last_error = e
                logger.warning(f"Erro de conexão SSL ({retries}/{max_retries}): {error_msg}")

                # Pequena pausa antes de tentar novamente
                time.sleep(retry_delay)

                # Tentar limpar a sessão atual
                try:
                    db.session.remove()
                    logger.info("Sessão de banco de dados removida para reconexão")
                except Exception as session_error:
                    logger.error(f"Erro ao remover sessão: {str(session_error)}")
            else:
                # Outros erros operacionais
                logger.error(f"Erro operacional do banco de dados: {error_msg}")
                raise
        except SQLAlchemyError as e:
            # Outros erros do SQLAlchemy
            logger.error(f"Erro do SQLAlchemy: {str(e)}")
            raise
        except Exception as e:
            # Capturar erros genéricos
            logger.error(f"Erro inesperado no banco de dados: {str(e)}")
            raise

    # Se chegou aqui, todas as tentativas falharam
    logger.error(f"Todas as {max_retries} tentativas de conexão falharam. Último erro: {str(last_error)}")
    return None

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.config["DEBUG"] = True

# Registrar o blueprint da API
app.register_blueprint(api_blueprint)

# Configure database
# Ajustar a URI do banco de dados para incluir parâmetros SSL e reconexão
database_url = os.environ.get("DATABASE_URL", "sqlite:///flai.db")

# Adicionar parâmetros específicos para PostgreSQL para melhorar a estabilidade da conexão
if database_url.startswith('postgresql'):
    # Verificar se sslmode já está definido na URL
    if 'sslmode=' not in database_url:
        # Se já tiver parâmetros, adicionar mais, senão, iniciar com o caractere '?'
        separator = '&' if '?' in database_url else '?'
        database_url = f"{database_url}{separator}sslmode=require"

    # Certificar-se de que os outros parâmetros de conexão estão presentes
    needed_params = {
        'connect_timeout': '10', 
        'keepalives': '1', 
        'keepalives_idle': '30', 
        'keepalives_interval': '10', 
        'keepalives_count': '5'
    }

    for param, value in needed_params.items():
        if f"{param}=" not in database_url:
            database_url = f"{database_url}&{param}={value}"

    logger.info(f"Database URL configurada com parâmetros de conexão SSL")
    # Log para debug, mas omitindo detalhes sensíveis
    safe_url = re.sub(r"postgresql://[^:]+:[^@]+@", "postgresql://user:***@", database_url)
    logger.debug(f"URL do banco de dados (sensível): {safe_url}")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configurações de pool de conexões para evitar problemas de SSL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,  # Verifica se a conexão está ativa antes de usá-la
    "pool_recycle": 300,    # Recicla conexões após 5 minutos
    "pool_timeout": 30,     # Timeout para obter uma conexão do pool
    "pool_size": 10,        # Tamanho máximo do pool
    "max_overflow": 15      # Conexões adicionais permitidas além do pool_size
}

# Inicializar o banco de dados com as novas configurações
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
        client_history = data.get('history', [])
        
        # Tentar obter session_id do cookie primeiro
        session_id = request.cookies.get('flai_session_id')
        
        # Se não existir cookie, criar novo ID
        if not session_id:
            session_id = str(uuid.uuid4())
            app.logger.info(f"Criando nova sessão: {session_id}")
        else:
            app.logger.info(f"Usando sessão existente do cookie: {session_id}")

        if not message:
            return jsonify({"error": True, "message": "Mensagem vazia"})

        # Inicializa ou recupera a sessão do usuário
        if session_id not in conversation_store:
            conversation_store[session_id] = {
                'history': [],
                'travel_info': {}
            }
            app.logger.info(f"Inicializando nova sessão no servidor: {session_id}")
        else:
            app.logger.info(f"Sessão existente encontrada no servidor: {session_id}")

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
                    # Converter datas relativas em datas exatas para apresentação
                    # Clonar o dicionário para não modificar o original
                    presentation_info = current_travel_info.copy()

                    # Formatar para mostrar data completa formatada
                    if 'departure_date' in presentation_info:
                        try:
                            date_obj = datetime.strptime(presentation_info['departure_date'], '%Y-%m-%d')
                            # Adicionar dia da semana à apresentação
                            dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
                            dia_semana = dias_semana[date_obj.weekday()]
                            presentation_info['departure_date_formatted'] = f"{date_obj.strftime('%d/%m/%Y')} ({dia_semana})"
                        except Exception as e:
                            logger.error(f"Erro ao formatar data de partida: {str(e)}")

                    if 'return_date' in presentation_info:
                        try:
                            date_obj = datetime.strptime(presentation_info['return_date'], '%Y-%m-%d')
                            # Adicionar dia da semana à apresentação
                            dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
                            dia_semana = dias_semana[date_obj.weekday()]
                            presentation_info['return_date_formatted'] = f"{date_obj.strftime('%d/%m/%Y')} ({dia_semana})"
                        except Exception as e:
                            logger.error(f"Erro ao formatar data de retorno: {str(e)}")

                    summary = chat_processor.format_travel_info_summary(presentation_info)

                    system_context = f"""
                    Temos todas as informações necessárias para busca:
                    {summary}

                    Confirme estes detalhes com o usuário de forma natural antes de realizar a busca.
                    IMPORTANTE: Mostre exatamente as datas formatadas como estão no resumo acima.
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
                # IMPLEMENTAÇÃO DO PLANO DE AÇÃO: SEPARAÇÃO TOTAL DA BUSCA

                # Se já buscamos antes, apenas continuar a conversa
                if current_travel_info.get('search_results'):
                    system_context = """
                    Já temos resultados de busca de voos. Responda às perguntas do usuário
                    usando apenas os dados reais que já foram obtidos.
                    """
                else:
                    # SOLUÇÃO DEFINITIVA: Pular completamente o ChatGPT neste ponto
                    # Quando estamos na etapa de busca (step 2), não precisamos do ChatGPT
                    # Os dados reais virão diretamente da API Amadeus

                    # Forçar a flag para pular ChatGPT imediatamente
                    logger.warning("🚫 ETAPA 2 DETECTADA: PULANDO GPT COMPLETAMENTE")
                    skip_gpt_call = True

            # INTERCEPÇÃO CRÍTICA: VERIFICAR QUALQUER ESTÁGIO DE BUSCA
            # Aqui detectamos qualquer condição que indique que devemos realizar uma busca real
            # Isso impede COMPLETAMENTE que o GPT seja chamado para simulações
            skip_gpt_call = False

            # Caso 1: Estamos na etapa 2 (busca) e o usuário já confirmou
            if step == 2 and current_travel_info.get('confirmed') and not current_travel_info.get('search_results'):
                logger.warning("⚠️ INTERCEPÇÃO DO FLUXO: Busca confirmada detectada, pulando ChatGPT completamente")
                skip_gpt_call = True

            # Caso 2: Se a mensagem contém alguma confirmação clara
            confirmation_phrases = ["sim", "confirmo", "pode buscar", "ok", "busque", "procure", "encontre"]
            if any(phrase in message.lower() for phrase in confirmation_phrases) and step == 1:
                logger.warning("⚠️ INTERCEPÇÃO DO FLUXO: Confirmação detectada na mensagem, pulando ChatGPT")
                skip_gpt_call = True
                # Forçar o avanço para etapa 2
                current_travel_info['step'] = 2
                current_travel_info['confirmed'] = True
                step = 2
            
            # ADICIONAL: Para garantir que o GPT nunca seja usado para gerar resultados de voos
            # independente de qualquer condição anterior
            if step == 2:
                logger.warning("🚫 INTERCEPÇÃO DE SEGURANÇA: Etapa de busca de voos, GPT será pulado obrigatoriamente")
                skip_gpt_call = True

            # Qualquer caso em que devemos pular o GPT:
            chat_context = {
                'step': step,
                'travel_info': current_travel_info
            }
            if skip_gpt_call:
                # Definir resposta padrão sem chamar OpenAI
                gpt_result = {
                    "response": "Estou consultando a API da Amadeus para encontrar as melhores opções reais de voos para sua viagem. Aguarde um momento..."
                }
                logger.warning("✅ Fluxo desviado com sucesso para API Amadeus direta")
            else:
                # Apenas para casos onde não estamos fazendo busca real
                logger.info(f"Chamando OpenAI normalmente para etapa {step} com session_id {session_id}")
                gpt_result = openai_service.travel_assistant(message, openai_history, system_context, session_id=session_id)

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
                    # IMPLEMENTAÇÃO DEFINITIVA: CONEXÃO DIRETA COM A API AMADEUS
                    # Apenas o flight_service_connector será utilizado para todas as buscas
                    # Este é o único ponto onde a busca real é feita
                    from services.flight_service_connector import flight_service_connector

                    # Log para rastrear este ponto crítico
                    logger.warning("🔍 BUSCA REAL: Chamando Amadeus API diretamente via flight_service_connector")

                    search_results = None
                    try:
                        # Garantir que o session_id seja persistido
                        if not session_id:
                            session_id = str(uuid.uuid4())
                            logger.warning(f"Gerado novo session_id: {session_id}")

                        # Adicionar log detalhado para os parâmetros de busca
                        logger.warning(f"PARÂMETROS DE BUSCA: Origem: {current_travel_info.get('origin')}, " + 
                                      f"Destino: {current_travel_info.get('destination')}, " +
                                      f"Data ida: {current_travel_info.get('departure_date')}, " +
                                      f"Data volta: {current_travel_info.get('return_date', 'N/A')}, " +
                                      f"Adultos: {current_travel_info.get('adults', 1)}")

                        # ÚNICO PONTO DE BUSCA REAL: using flight_service_connector
                        search_results = flight_service_connector.search_flights_from_chat(
                            travel_info=current_travel_info,
                            session_id=session_id
                        )

                        # Log detalhado sobre os resultados obtidos ou erros
                        if not search_results:
                            logger.error("❌ Busca direta retornou resultados vazios")
                            response_text = "Desculpe, não consegui encontrar voos para a sua busca. Poderia verificar as informações fornecidas?"
                            show_flight_results = False
                        elif 'error' in search_results:
                            logger.error(f"❌ Erro na busca direta: {search_results['error']}")
                            response_text = f"Ocorreu um erro ao buscar voos: {search_results['error']}"
                            show_flight_results = False
                        else:
                            flight_count = len(search_results.get('data', []))
                            logger.warning(f"✅ RESULTADOS OBTIDOS COM SUCESSO: {flight_count} voos encontrados")

                            # Armazenar resultados da busca no contexto atual
                            current_travel_info['search_results'] = search_results

                            # Adicionar o session_id aos resultados para referência
                            search_results['session_id'] = session_id

                            # Usar o formatador do conector para preparar a resposta
                            formatted_response = flight_service_connector.format_flight_results_for_chat(search_results)

                            # Extrair a mensagem e a flag para mostrar o painel
                            response_text = formatted_response.get('message', 'Encontrei algumas opções de voos para você! Confira no painel lateral.')

                            # IMPORTANTE: Forçar abertura do painel quando houver resultados
                            show_flight_results = True
                            logger.warning(f"📊 Painel de resultados será exibido com session_id: {session_id}")

                        # Preparar dados para resposta
                        current_travel_info['show_flight_results'] = show_flight_results
                        if show_flight_results:
                            current_travel_info['flight_session_id'] = session_id
                    except Exception as e:
                        logging.error(f"❌ Erro grave na busca de voos: {str(e)}")
                        # Mostrar rastreamento completo para depuração
                        import traceback
                        logging.error(traceback.format_exc())
                        response_text = "Desculpe, ocorreu um erro técnico ao buscar voos. Por favor, tente novamente."
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

            # FORÇAR EXIBIÇÃO DO PAINEL SEMPRE QUE TIVERMOS RESULTADOS DE BUSCA
            # Isso usa nosso novo provedor de dados de voo para garantir a exibição do painel
            if current_travel_info.get('show_flight_results', False):
                # Se temos resultados de busca, mostrar o painel
                response['show_flight_results'] = True

                # Passar o ID da sessão para o cliente
                if current_travel_info.get('flight_session_id'):
                    response['session_id'] = current_travel_info.get('flight_session_id')
                else:
                    response['session_id'] = session_id

                # Adicionar evento para que o JavaScript ative o mural
                response['trigger_flight_panel'] = True

                logging.info(f"Exibindo painel de voos para a sessão: {response.get('session_id')}")

            # Atualiza o armazenamento
            conversation_store[session_id]['history'] = history
            conversation_store[session_id]['travel_info'] = current_travel_info

            # Adiciona session_id na resposta para legado
            response['session_id'] = session_id

            # Criar resposta com cookie
            resp = make_response(jsonify(response))
            
            # Configurar cookie seguro com o session_id
            resp.set_cookie(
                'flai_session_id', 
                session_id, 
                httponly=True,       # Não acessível via JavaScript 
                secure=True,         # Só enviado em HTTPS
                samesite='Lax',      # Proteção contra CSRF
                max_age=86400        # Válido por 24 horas
            )
            
            app.logger.info(f"Cookie flai_session_id definido com valor: {session_id}")
            
            return resp
        else:
            # Implementar lógica para planejamento completo
            response = {"response": "Modo de planejamento completo em desenvolvimento."}
            history.append({'assistant': response['response']})
            conversation_store[session_id]['history'] = history
            response['session_id'] = session_id

            # Criar resposta com cookie
            resp = make_response(jsonify(response))
            
            # Configurar cookie seguro com o session_id
            resp.set_cookie(
                'flai_session_id', 
                session_id, 
                httponly=True,       # Não acessível via JavaScript 
                secure=True,         # Só enviado em HTTPS
                samesite='Lax',      # Proteção contra CSRF
                max_age=86400        # Válido por 24 horas
            )
            
            app.logger.info(f"Cookie flai_session_id definido com valor: {session_id}")
            
            return resp

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
    def fetch_conversations():
        """Função interna para buscar conversas (para uso com retry)"""
        conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.last_updated.desc()).all()
        return conversations

    try:
        # Usar o mecanismo de retry para buscar conversas
        user_conversations = db_operation_with_retry(fetch_conversations, max_retries=5, retry_delay=0.8)

        # Se todas as tentativas falharam, retornar uma lista vazia com uma mensagem amigável
        if user_conversations is None:
            logger.error("Falha ao recuperar conversas após múltiplas tentativas")
            return jsonify({
                "error": True,
                "message": "Não foi possível recuperar suas conversas no momento. Por favor, tente novamente.",
                "conversations": []
            })

        # Processar as conversas recuperadas com sucesso
        result = []
        for conv in user_conversations:
            result.append({
                "id": conv.id,
                "title": conv.title,
                "last_updated": conv.last_updated.strftime("%d/%m/%Y")
            })

        logger.info(f"Conversas recuperadas com sucesso: {len(result)}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Erro ao buscar conversas: {str(e)}")
        # Retornar uma resposta amigável ao usuário
        return jsonify({
            "error": True,
            "message": "Ocorreu um erro ao carregar suas conversas. Por favor, atualize a página e tente novamente."
        }), 500

@app.route('/api/conversation/<int:conversation_id>/messages')
@login_required
def get_conversation_messages(conversation_id):
    def fetch_conversation():
        """Função interna para buscar a conversa (para uso com retry)"""
        return Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()

    def fetch_messages():
        """Função interna para buscar as mensagens (para uso com retry)"""
        return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()

    try:
        # Buscar a conversa com retry
        conv = db_operation_with_retry(fetch_conversation, max_retries=5, retry_delay=0.5)

        if conv is None:
            logger.error(f"Não foi possível recuperar a conversa {conversation_id} após várias tentativas")
            return jsonify({
                "error": True, 
                "message": "Não foi possível recuperar esta conversa no momento. Por favor, tente novamente."
            }), 500

        if not conv:
            return jsonify({"error": "Conversa não encontrada"}), 404

        # Buscar as mensagens com retry
        messages = db_operation_with_retry(fetch_messages, max_retries=5, retry_delay=0.5)

        if messages is None:
            logger.error(f"Não foi possível recuperar as mensagens da conversa {conversation_id} após várias tentativas")
            return jsonify({
                "error": True,
                "message": "Não foi possível recuperar as mensagens desta conversa no momento. Por favor, tente novamente."
            }), 500

        # Processar os resultados com sucesso
        result = []
        for msg in messages:
            result.append({
                "id": msg.id,
                "is_user": msg.is_user,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            })

        logger.info(f"Recuperadas {len(result)} mensagens da conversa {conversation_id}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Erro ao recuperar mensagens da conversa {conversation_id}: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Ocorreu um erro ao carregar as mensagens. Por favor, tente novamente."
        }), 500


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
"""
Rotas da API para o painel de resultados de voos reais
Este módulo contém as rotas necessárias para fornecer dados reais 
da API TravelPayouts para exibição no frontend.

IMPORTANTE: Este módulo garante que apenas dados reais da API TravelPayouts
sejam retornados, nunca usando dados simulados ou falsos.
"""

import os
import json
import logging
import uuid
import traceback
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, render_template, make_response

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar os serviços necessários
from services.travelpayouts_service import TravelPayoutsService
from services.travelpayouts_connector import travelpayouts_connector

# Criar blueprint para as rotas da API de resultados de voos
api_blueprint = Blueprint('flight_results_api', __name__)

# Armazenamento em memória para sessões de busca (temporário)
# Na implementação final, isso seria movido para um banco de dados
flight_search_sessions = {}

@api_blueprint.route('/api/flight_results/<session_id>', methods=['GET'])
@api_blueprint.route('/api/flight_results', methods=['GET'])
def get_flight_results(session_id=None):
    """
    ENDPOINT DEFINITIVO PARA MURAL DE VOOS
    
    Obtém os resultados de voos reais da API TravelPayouts para uma sessão específica,
    usando exclusivamente o serviço travelpayouts_connector para garantir que
    apenas dados reais da API TravelPayouts sejam retornados.
    
    Este endpoint é o ÚNICO ponto de acesso para o painel lateral obter dados,
    eliminando qualquer caminho que possa mostrar dados não-reais.
    
    Args:
        session_id: ID da sessão do chat (opcional, pode vir do cookie)
    """
    # Tentar obter session_id do cookie se não foi fornecido na URL
    if not session_id:
        session_id = request.cookies.get('flai_session_id')
        logger.warning(f"🍪 Usando ID da sessão do cookie: {session_id}")
    
    # Mensagem clara de início de processamento para debug
    logger.warning(f"🛫 ENDPOINT REAL: Processando solicitação de voos para sessão {session_id}")
    
    # Validar session_id
    if not session_id or session_id == "undefined" or session_id == "null":
        logger.error("❌ Session ID inválido ou não fornecido")
        return jsonify({
            "error": "ID de sessão inválido. Por favor, inicie uma nova conversa.",
            "data": []
        }), 400
    
    try:
        # Verificar se temos resultados para esta sessão no cache
        if session_id in flight_search_sessions:
            logger.warning(f"✅ Usando resultados em CACHE para sessão {session_id}")
            
            # Verificar se os dados em cache são válidos (têm lista de voos)
            cached_results = flight_search_sessions[session_id]
            if cached_results and 'data' in cached_results and len(cached_results['data']) > 0:
                logger.warning(f"📊 Retornando {len(cached_results['data'])} voos do cache")
                
                # Inserir cabeçalho para debugging
                cached_results['source'] = 'cache'
                return jsonify(cached_results)
            else:
                logger.warning("⚠️ Dados em cache existem mas estão vazios ou inválidos")
        
        # Caso contrário, verificar se temos parâmetros de busca salvos
        from app import conversation_store
        
        # Verificar se a sessão existe no conversation_store
        if session_id not in conversation_store:
            logger.error(f"❌ Sessão {session_id} não encontrada no conversation_store")
            return jsonify({
                "error": "Sessão não encontrada. Por favor, inicie uma nova conversa.",
                "data": []
            }), 404
        
        logger.warning(f"📝 Encontrada sessão {session_id} no conversation_store")
        travel_info = conversation_store[session_id].get('travel_info', {})
        
        # Verificar se temos resultados já salvos
        if travel_info.get('search_results'):
            logger.warning(f"📊 Encontrados resultados salvos na travel_info da sessão {session_id}")
            
            # Validar se os resultados salvos têm dados
            saved_results = travel_info['search_results']
            if saved_results and 'data' in saved_results and len(saved_results['data']) > 0:
                logger.warning(f"📊 Retornando {len(saved_results['data'])} voos da travel_info")
                
                # Atualizar o cache e retornar
                flight_search_sessions[session_id] = saved_results
                
                # Inserir cabeçalho para debugging
                saved_results['source'] = 'travel_info'
                return jsonify(saved_results)
            else:
                logger.warning("⚠️ Resultados salvos existem mas estão vazios ou inválidos")
        
        # Verificar se temos parâmetros suficientes para realizar a busca
        if not (travel_info.get('origin') and travel_info.get('destination') and 
                (travel_info.get('departure_date') or travel_info.get('date_range_start'))):
            logger.error(f"❌ Parâmetros insuficientes para busca na sessão {session_id}")
            return jsonify({
                "error": "Informações insuficientes para realizar a busca. Forneça origem, destino e data.",
                "data": []
            }), 400
        
        # Usar o serviço TravelPayoutsConnector para buscar resultados novos
        logger.warning(f"🔄 Buscando NOVOS resultados reais da API TravelPayouts para sessão {session_id}")
        
        # Connector já está disponível no topo do arquivo
        
        # Realizar a busca com o conector direto
        search_results = travelpayouts_connector.search_flights_from_chat(
            travel_info=travel_info,
            session_id=session_id
        )
        
        # Validar os resultados
        if not search_results:
            logger.error(f"❌ Não foi possível obter resultados da API para sessão {session_id}")
            return jsonify({
                "error": "Falha na busca de resultados. Tente novamente com outros parâmetros.",
                "data": []
            }), 500
            
        if 'error' in search_results:
            logger.error(f"❌ Erro na busca de voos: {search_results['error']}")
            return jsonify({
                "error": search_results['error'],
                "data": []
            }), 500
        
        # Verificar se recebemos dados válidos
        if 'data' not in search_results or not search_results['data']:
            logger.error(f"❌ API retornou estrutura sem voos para sessão {session_id}")
            return jsonify({
                "error": "A API não retornou voos para sua busca. Tente com outros parâmetros.",
                "data": []
            }), 404
        
        # Adicionar metadados para diagnóstico
        search_results['source'] = 'api_direct'
        search_results['session_id'] = session_id
        search_results['timestamp'] = datetime.utcnow().isoformat()
        
        # Salvar os resultados em todos os lugares relevantes
        logger.warning(f"✅ Obtidos {len(search_results['data'])} voos novos. Salvando para sessão {session_id}")
        flight_search_sessions[session_id] = search_results
        travel_info['search_results'] = search_results
        
        return jsonify(search_results)
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro ao obter resultados de voos: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Ocorreu um erro ao buscar os resultados: {str(e)}",
            "data": []
        }), 500


# Rota para buscar diretamente pela API (usando o conector)
@api_blueprint.route('/api/flight_search', methods=['POST'])
def direct_flight_search():
    """
    Endpoint para busca direta de voos usando a API TravelPayouts.
    Este endpoint só usa o travelpayouts_connector para 
    garantir que apenas dados reais sejam retornados.
    """
    try:
        # Obter parâmetros da requisição
        data = request.json
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        logger.info(f"Busca direta de voos - Sessão: {session_id}")
        logger.debug(f"Parâmetros de busca: {json.dumps(data, default=str)}")
        
        # Validar parâmetros mínimos
        if not (data.get('origin') and data.get('destination') and 
                (data.get('departure_date') or data.get('date_range_start'))):
            return jsonify({
                "error": "Parâmetros insuficientes. Forneça origem, destino e data.",
                "data": []
            })
        
        # Realizar a busca com o conector
        search_results = travelpayouts_connector.search_flights_from_chat(
            travel_info=data,
            session_id=session_id
        )
        
        # Validar e retornar os resultados
        if not search_results or 'error' in search_results:
            error_msg = search_results.get('error', 'Falha na busca de resultados') if search_results else 'Sem resultados'
            logger.error(f"Erro na busca direta: {error_msg}")
            return jsonify({
                "error": error_msg,
                "data": []
            })
        
        # Cache e retorno dos resultados
        flight_search_sessions[session_id] = search_results
        logger.info(f"Busca direta concluída com sucesso: {len(search_results.get('data', []))} resultados")
        
        # Adicionar o ID da sessão na resposta
        search_results['session_id'] = session_id
        return jsonify(search_results)
    
    except Exception as e:
        logger.error(f"Erro na busca direta de voos: {str(e)}")
        return jsonify({
            "error": f"Erro ao processar a busca: {str(e)}",
            "data": []
        }), 500


# Página de resultados da API TravelPayouts
@api_blueprint.route('/travelpayouts-results', methods=['GET'])
@api_blueprint.route('/amadeus-results', methods=['GET'])  # Manter rota antiga para compatibilidade
def travelpayouts_results_page():
    """
    Renderiza a página de resultados de voos com base nos parâmetros fornecidos.
    Esta página é o destino do botão "Clique aqui para ver suas melhores opções"
    mostrado pela AVI após a coleta de informações.
    """
    try:
        # Tentar obter session_id do cookie
        session_id = request.cookies.get('flai_session_id')
        travel_info = {}
        
        # Se temos um ID de sessão, tentar obter informações da viagem
        if session_id:
            # Importar o conversation_store
            from app import conversation_store
            
            if session_id in conversation_store:
                # Carregar as informações salvas
                travel_info = conversation_store[session_id].get('travel_info', {})
                logger.warning(f"✅ Usando informações de viagem da sessão {session_id} para página de resultados")
            
        # Usar dados da conversa ou parâmetros da URL, sem valores padrão
        origin = travel_info.get('origin') or request.args.get('origin')
        destination = travel_info.get('destination') or request.args.get('destination')
        departure_date = travel_info.get('departure_date') or request.args.get('departure_date')
        adults = travel_info.get('adults') or request.args.get('adults')
        
        # Verificar se temos os parâmetros necessários - não usar padrões
        if not (origin and destination and departure_date):
            logger.warning(f"⚠️ ERRO: Parâmetros insuficientes para busca. Travel info: {travel_info}")
            
            # Log detalhado para depuração
            if travel_info:
                logger.warning(f"🔎 CONTEÚDO DE TRAVEL_INFO: {json.dumps(travel_info, default=str)}")
            else:
                logger.warning("❌ TRAVEL_INFO está vazio ou não existe")
                
            logger.warning(f"🔎 URL PARAMS: origin={request.args.get('origin')}, dest={request.args.get('destination')}, date={request.args.get('departure_date')}")
            
            # Se tivermos o objeto travel_info mas faltarem campos específicos
            missing = []
            if not origin: missing.append("origem")
            if not destination: missing.append("destino") 
            if not departure_date: missing.append("data de partida")
            
            return render_template(
                'error.html', 
                message=f"Parâmetros insuficientes: faltam {', '.join(missing)}. Por favor, forneça todas as informações necessárias na conversa com a AVI."
            )
        
        # Renderizar a página com os parâmetros obtidos
        resp = make_response(render_template(
            'amadeus_results.html',
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=adults
        ))
        
        # Verificar se precisamos definir um cookie de sessão
        if not session_id and travel_info:
            # Criar nova sessão
            session_id = str(uuid.uuid4())
            
            # Configurar cookie
            resp.set_cookie(
                'flai_session_id', 
                session_id, 
                httponly=True,       # Não acessível via JavaScript 
                secure=True,         # Só enviado em HTTPS
                samesite='Lax',      # Proteção contra CSRF
                max_age=86400        # Válido por 24 horas
            )
            
            logger.warning(f"🍪 Definindo cookie flai_session_id com valor: {session_id}")
        
        return resp
    except Exception as e:
        logger.error(f"Erro ao renderizar página de resultados: {str(e)}")
        return render_template('error.html', message=f"Erro ao carregar resultados: {str(e)}")

# Endpoint de API para busca de voos para a página de resultados
@api_blueprint.route('/travelpayouts-test', methods=['GET'])
@api_blueprint.route('/amadeus-test', methods=['GET'])  # Manter rota antiga para compatibilidade
def travelpayouts_test():
    """
    Endpoint para buscar dados reais de voos da API TravelPayouts.
    Usado pela página de resultados para obter dados via JavaScript.
    """
    try:
        logger.warning("📡 TESTE TRAVELPAYOUTS: Iniciando teste de conexão direta")
        
        # Tentar obter session_id do cookie
        session_id = request.cookies.get('flai_session_id')
        
        # Se não existir cookie, criar um ID novo para o teste
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.warning(f"⚠️ Cookie flai_session_id não encontrado, usando ID temporário: {session_id}")
        else:
            logger.warning(f"✅ Encontrado cookie flai_session_id com valor: {session_id}")
            
            # Verificar se temos dados salvos da conversa para essa sessão
            from app import conversation_store
            if session_id in conversation_store:
                travel_info = conversation_store[session_id].get('travel_info', {})
                
                # Se temos dados salvos da conversa, usar eles
                if travel_info and (travel_info.get('origin') and travel_info.get('destination')):
                    logger.warning(f"✅ Usando informações de viagem da sessão {session_id}")
                    
                    # Verificar se já temos resultados guardados
                    if travel_info.get('search_results'):
                        logger.warning(f"📊 Retornando resultados já salvos para sessão {session_id}")
                        search_results = travel_info.get('search_results')
                        # Adicionar metadados
                        search_results['success'] = True
                        search_results['source'] = 'session_cache'
                        search_results['test_timestamp'] = datetime.utcnow().isoformat()
                        return jsonify(search_results)
                    
                    # Usar os dados da conversa para buscar novos resultados
                    search_data = {
                        "origin": travel_info.get('origin'),
                        "destination": travel_info.get('destination'),
                        "departure_date": travel_info.get('departure_date'),
                        "adults": travel_info.get('adults', 1),
                    }
                    
                    # Usar o travelpayouts_connector com a travel_info da sessão
                    logger.warning(f"🔍 Buscando voos com dados da sessão para {search_data['origin']} → {search_data['destination']}")
                    
                    search_results = travelpayouts_connector.search_flights_from_chat(
                        travel_info=travel_info,
                        session_id=session_id
                    )
                    
                    # Salvar resultados na sessão
                    if search_results and 'error' not in search_results:
                        travel_info['search_results'] = search_results
                    
                    return jsonify(search_results)
                    
        # Se não temos dados da sessão, usar apenas parâmetros da URL (sem valores padrão)
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        departure_date = request.args.get('departure_date')
        adults = request.args.get('adults')
        
        # Verificar se temos parâmetros suficientes
        if not (origin and destination and departure_date):
            logger.error("❌ TESTE TRAVELPAYOUTS: Parâmetros insuficientes para busca")
            return jsonify({
                "error": "Parâmetros insuficientes. Por favor, forneça origem, destino e data na conversa com a AVI.",
                "data": [],
                "success": False
            }), 400
        
        # Preparar dados para teste
        search_data = {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "adults": int(adults)
        }
        
        # Usar o travelpayouts_connector para buscar resultados reais
        logger.warning(f"🔍 Buscando voos com parâmetros diretos para {origin} → {destination}")
        search_results = travelpayouts_connector.search_flights_from_chat(
            travel_info=search_data,
            session_id=session_id
        )
        
        # Verificar resultados
        if not search_results or 'error' in search_results:
            error_msg = search_results.get('error', 'Erro desconhecido') if search_results else 'Sem resultados'
            logger.error(f"❌ TESTE TRAVELPAYOUTS: Falha na conexão - {error_msg}")
            return jsonify({
                "error": error_msg,
                "data": [],
                "success": False
            }), 500
        
        # Adicionar metadados para diagnóstico
        flight_count = len(search_results.get('data', []))
        search_results['success'] = True
        search_results['test_timestamp'] = datetime.utcnow().isoformat()
        search_results['flight_count'] = flight_count
        search_results['search_params'] = {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'adults': adults
        }
        
        logger.warning(f"✅ TESTE TRAVELPAYOUTS: Conexão bem-sucedida - {flight_count} voos encontrados")
        return jsonify(search_results)
        
    except Exception as e:
        logger.error(f"❌ TESTE TRAVELPAYOUTS: Erro durante o teste - {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Erro no teste: {str(e)}",
            "data": [],
            "success": False
        }), 500

"""
Rotas da API para o painel de resultados de voos reais
Este módulo contém as rotas necessárias para fornecer dados reais 
da API Amadeus para exibição no frontend.
"""
import logging
import json
import uuid
from flask import Blueprint, jsonify, request

# Importar os serviços necessários
from services.amadeus_sdk_service import AmadeusSDKService
from services.flight_service_connector import flight_service_connector

# Configurar logger
logger = logging.getLogger(__name__)

# Criar blueprint para as rotas da API de resultados de voos
api_blueprint = Blueprint('flight_results_api', __name__)

# Armazenamento em memória para sessões de busca (temporário)
# Na implementação final, isso seria movido para um banco de dados
flight_search_sessions = {}

@api_blueprint.route('/api/flight_results/<session_id>', methods=['GET'])
def get_flight_results(session_id):
    """
    ENDPOINT DEFINITIVO PARA MURAL DE VOOS
    
    Obtém os resultados de voos reais da API Amadeus para uma sessão específica,
    usando exclusivamente o serviço FlightServiceConnector para garantir que
    apenas dados reais da API Amadeus sejam retornados.
    
    Este endpoint é o ÚNICO ponto de acesso para o painel lateral obter dados,
    eliminando qualquer caminho que possa mostrar dados não-reais.
    
    Args:
        session_id: ID da sessão do chat
    """
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
        
        # Usar o serviço FlightServiceConnector para buscar resultados novos
        logger.warning(f"🔄 Buscando NOVOS resultados reais da API Amadeus para sessão {session_id}")
        
        # Importar o connector antes de usá-lo
        from services.flight_service_connector import flight_service_connector
        
        # Realizar a busca com o conector direto
        search_results = flight_service_connector.search_flights_from_chat(
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
        from datetime import datetime
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
    Endpoint para busca direta de voos usando a API Amadeus.
    Este endpoint só usar o flight_service_connector para 
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
        search_results = flight_service_connector.search_flights_from_chat(
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


# Endpoint de teste completamente removido para evitar qualquer uso acidental

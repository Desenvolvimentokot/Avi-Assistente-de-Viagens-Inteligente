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
    IMPLEMENTAÇÃO DO PLANO DE AÇÃO: ENDPOINT UNIFICADO PARA MURAL DE VOOS
    
    Obtém os resultados de voos reais da API Amadeus para uma sessão específica,
    usando exclusivamente o serviço FlightServiceConnector para garantir que
    apenas dados reais da API Amadeus sejam retornados.
    
    Este endpoint é o ÚNICO ponto de acesso para o painel lateral obter dados,
    eliminando qualquer caminho que possa mostrar dados não-reais.
    
    Args:
        session_id: ID da sessão do chat
    """
    # Mensagem clara de início de processamento para debug
    logger.warning(f"🛫 ENDPOINT ÚNICO PARA DADOS REAIS: Processando solicitação para sessão {session_id}")
    try:
        logger.info(f"Recebida solicitação para resultados de voos autênticos - Sessão: {session_id}")
        
        # SEGURANÇA CRÍTICA: Este endpoint NUNCA gera dados sintéticos
        # e sempre faz uma chamada direta e exclusiva ao conector Amadeus.
        
        # Verificar se temos resultados para esta sessão no cache
        if session_id in flight_search_sessions:
            logger.info(f"Retornando resultados REAIS em cache para sessão {session_id}")
            results = flight_search_sessions[session_id]
            
            # Log para facilitar debug
            if 'data' in results and results['data']:
                logger.info(f"Cache contém {len(results['data'])} resultados autênticos")
            else:
                logger.warning(f"Cache existe mas não contém dados válidos: {results}")
                
            return jsonify(results)
        
        # Caso contrário, verificar se temos parâmetros de busca salvos
        from app import conversation_store
        
        if session_id not in conversation_store:
            logger.warning(f"Sessão {session_id} não encontrada no conversation_store")
            return jsonify({
                "error": "Sessão não encontrada. Por favor, inicie uma nova conversa.",
                "data": []
            })
        
        travel_info = conversation_store[session_id].get('travel_info', {})
        
        # Verificar se temos resultados já salvos
        if travel_info.get('search_results'):
            logger.info(f"Retornando resultados armazenados em travel_info para sessão {session_id}")
            flight_search_sessions[session_id] = travel_info['search_results']
            return jsonify(travel_info['search_results'])
        
        # Verificar se temos parâmetros suficientes para realizar a busca
        if not (travel_info.get('origin') and travel_info.get('destination') and 
                (travel_info.get('departure_date') or travel_info.get('date_range_start'))):
            logger.warning(f"Parâmetros insuficientes para busca na sessão {session_id}")
            return jsonify({
                "error": "Informações insuficientes para realizar a busca. Forneça origem, destino e data.",
                "data": []
            })
        
        # Usar o serviço FlightServiceConnector para buscar resultados
        logger.info(f"Buscando resultados reais da API Amadeus para sessão {session_id}")
        logger.debug(f"Parâmetros de busca: {json.dumps(travel_info, default=str)}")
        
        # Realizar a busca com o conector de serviço de voos
        search_results = flight_service_connector.search_flights_from_chat(
            travel_info=travel_info,
            session_id=session_id
        )
        
        # Validar os resultados
        if not search_results:
            logger.error(f"Não foi possível obter resultados da API para sessão {session_id}")
            return jsonify({
                "error": "Falha na busca de resultados. Tente novamente com outros parâmetros.",
                "data": []
            })
            
        if 'error' in search_results:
            logger.error(f"Erro na busca de voos: {search_results['error']}")
            return jsonify({
                "error": search_results['error'],
                "data": []
            })
        
        # Salvar os resultados na sessão para futuras consultas
        logger.info(f"Resultados de voos obtidos com sucesso. Salvando para sessão {session_id}")
        flight_search_sessions[session_id] = search_results
        travel_info['search_results'] = search_results
        return jsonify(search_results)
            
        # Se chegamos aqui, não temos informações suficientes
        return jsonify({
            "error": "Não há resultados disponíveis para esta sessão. Realize uma busca primeiro."
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter resultados de voos: {str(e)}")
        return jsonify({
            "error": f"Ocorreu um erro ao buscar os resultados: {str(e)}"
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


@api_blueprint.route('/api/flight_results/test', methods=['GET'])
def test_flight_results():
    """
    Endpoint de teste para verificar a funcionalidade do painel lateral
    Este endpoint está desativado para garantir que apenas dados reais sejam mostrados
    """
    try:
        # Mensagem mais clara e informativa
        return jsonify({
            "error": "MODO DE TESTE DESATIVADO: O sistema Flai agora utiliza EXCLUSIVAMENTE dados reais da API Amadeus. Para ver resultados de voos, converse com a Avi e forneça detalhes sobre sua viagem.",
            "data": []
        })
    except Exception as e:
        logging.error(f"Erro ao processar solicitação de teste: {str(e)}")
        return jsonify({
            "error": f"Ocorreu um erro ao processar a solicitação: {str(e)}"
        }), 500

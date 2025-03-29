"""
Rotas da API para o painel de resultados de voos reais
"""
import logging
from flask import Blueprint, jsonify, request

# Importar os serviços necessários
from services.amadeus_sdk_service import AmadeusSDKService

# Criar blueprint para as rotas da API de resultados de voos
api_blueprint = Blueprint('flight_results_api', __name__)

# Armazenamento em memória para sessões de busca (temporário)
# Na implementação final, isso seria movido para um banco de dados
flight_search_sessions = {}

@api_blueprint.route('/api/flight_results/<session_id>', methods=['GET'])
def get_flight_results(session_id):
    """
    Obtém os resultados de voos reais da API Amadeus para uma sessão específica
    
    Args:
        session_id: ID da sessão do chat
    """
    try:
        # Verificar se temos resultados para esta sessão
        if session_id in flight_search_sessions:
            logging.info(f"Retornando resultados da sessão em cache para {session_id}")
            return jsonify(flight_search_sessions[session_id])
        
        # Caso contrário, verificar se temos parâmetros de busca salvos em outra estrutura
        from app import conversation_store
        
        # Log para debug
        logging.info(f"Sessão {session_id} - Verificando no conversation_store")
        
        if session_id in conversation_store:
            travel_info = conversation_store[session_id].get('travel_info', {})
            
            # Log para debug
            logging.info(f"Sessão {session_id} - Travel info: {travel_info}")
            
            # Verificar se temos resultados já salvos
            if travel_info.get('search_results'):
                # Já temos resultados salvos, retorná-los
                logging.info(f"Sessão {session_id} - Retornando resultados já salvos")
                flight_search_sessions[session_id] = travel_info['search_results']
                return jsonify(travel_info['search_results'])
            
            # Temos parâmetros suficientes para realizar a busca?
            if (travel_info.get('origin') and travel_info.get('destination') and 
                (travel_info.get('departure_date') or travel_info.get('date_range_start'))):
                
                logging.info(f"Sessão {session_id} - Iniciando busca com parâmetros: {travel_info}")
                
                # Inicializar o serviço Amadeus
                from services.amadeus_sdk_service import AmadeusSDKService
                amadeus_service = AmadeusSDKService()
                
                # Detectar o tipo de busca necessária (data específica ou período)
                search_results = None
                if travel_info.get('date_range_start') and travel_info.get('date_range_end'):
                    # Busca de período flexível
                    search_params = {
                        'originLocationCode': travel_info.get('origin'),
                        'destinationLocationCode': travel_info.get('destination'),
                        'departureDate': travel_info.get('date_range_start'),
                        'returnDate': travel_info.get('date_range_end'),
                        'adults': travel_info.get('adults', 1),
                        'currencyCode': 'BRL',
                        'max_dates_to_check': 3
                    }
                    logging.info(f"Realizando busca por período flexível: {search_params}")
                    search_results = amadeus_service.search_best_prices(search_params)
                else:
                    # Busca de data específica
                    search_params = {
                        'originLocationCode': travel_info.get('origin'),
                        'destinationLocationCode': travel_info.get('destination'),
                        'departureDate': travel_info.get('departure_date'),
                        'adults': travel_info.get('adults', 1),
                        'currencyCode': 'BRL',
                        'max': 5
                    }
                    
                    # Adicionar data de retorno se disponível
                    if travel_info.get('return_date'):
                        search_params['returnDate'] = travel_info.get('return_date')
                    
                    logging.info(f"Realizando busca por data específica: {search_params}")
                    search_results = amadeus_service.search_flights(search_params)
                    logging.info(f"Resultado da busca: {search_results}")
                
                # Salvar os resultados na sessão para futuras consultas
                if search_results:
                    # Verificar se temos dados válidos ou erro
                    if not isinstance(search_results, dict) or 'error' in search_results:
                        logging.error(f"Erro nos resultados da busca: {search_results}")
                        # Se houver erro, enviar uma resposta amigável
                        return jsonify({
                            "error": "Desculpe, ocorreu um erro na busca. Por favor, tente novamente.",
                            "details": search_results.get('error') if isinstance(search_results, dict) else str(search_results)
                        })
                    
                    logging.info(f"Sessão {session_id} - Resultados encontrados e salvos")
                    flight_search_sessions[session_id] = search_results
                    travel_info['search_results'] = search_results
                    return jsonify(search_results)
                else:
                    logging.warning(f"Sessão {session_id} - Nenhum resultado encontrado")
                    return jsonify({
                        "error": "Não foram encontrados voos para estes critérios de busca.",
                        "details": "Tente com outras datas ou destinos."
                    })
            
        # Se chegamos aqui, não temos informações suficientes
        logging.warning(f"Sessão {session_id} - Sem informações suficientes para busca")
        return jsonify({
            "error": "Não há resultados disponíveis para esta sessão. Realize uma busca primeiro."
        })
        
    except Exception as e:
        import traceback
        logging.error(f"Erro ao obter resultados de voos: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "error": f"Ocorreu um erro ao buscar os resultados. Por favor, tente novamente.",
            "details": str(e)
        }), 500


@api_blueprint.route('/api/flight_results/test', methods=['GET'])
def test_flight_results():
    """
    Endpoint de teste para verificar a funcionalidade do painel lateral
    Este endpoint gera dados de teste para diagnóstico do painel
    """
    try:
        # Gerar dados de teste para diagnosticar o painel
        from services.amadeus_service import AmadeusService
        
        amadeus_service = AmadeusService()
        # Usar mock data para teste
        amadeus_service.use_mock_data = True
        
        test_params = {
            'originLocationCode': 'GRU',
            'destinationLocationCode': 'MIA',
            'departureDate': '2025-05-01',
            'returnDate': '2025-05-10',
            'adults': 1,
            'currencyCode': 'BRL',
            'max': 5
        }
        
        # Obter dados simulados
        mock_results = amadeus_service._get_mock_flights(test_params)
        
        # Retornar para testes do painel
        return jsonify(mock_results)
    except Exception as e:
        logging.error(f"Erro ao processar solicitação de teste: {str(e)}")
        return jsonify({
            "error": f"Ocorreu um erro ao processar a solicitação: {str(e)}"
        }), 500

@api_blueprint.route('/api/test/create_session', methods=['POST'])
def create_test_session():
    """
    Endpoint de teste para criar uma sessão com dados predefinidos (apenas para diagnóstico)
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        session_data = data.get('data')
        
        if not session_id or not session_data:
            return jsonify({
                "success": False,
                "error": "session_id e data são obrigatórios"
            }), 400
            
        # Armazenar os dados na estrutura de sessão
        from app import conversation_store
        
        conversation_store[session_id] = session_data
        
        logging.info(f"Sessão de teste criada: {session_id} com dados: {session_data}")
        
        return jsonify({
            "success": True,
            "message": f"Sessão {session_id} criada com sucesso",
            "data": session_data
        })
        
    except Exception as e:
        logging.error(f"Erro ao criar sessão de teste: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro ao criar sessão de teste: {str(e)}"
        }), 500

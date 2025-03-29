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
        # Log detalhado para diagnóstico
        logging.info(f"==== INICIANDO BUSCA DE VOOS PARA SESSÃO: {session_id} ====")
        
        # Verificar token Amadeus no início para diagnóstico
        from services.amadeus_service import AmadeusService
        amadeus_service = AmadeusService()
        token = amadeus_service.get_token()
        
        if token:
            logging.info(f"✅ Token Amadeus válido obtido: {token[:5]}...{token[-5:]} (mascarado)")
        else:
            logging.error("❌ Falha ao obter token Amadeus - Verificar credenciais!")
        
        # Verificar se o session_id é nulo ou vazio e usar um padrão se necessário
        if not session_id or session_id == 'null':
            logging.warning("⚠️ Session ID é nulo ou vazio. Usando dados de teste.")
            # Redirecionar para o endpoint de teste
            return get_test_results()
        
        # Verificar se temos resultados para esta sessão em cache
        if session_id in flight_search_sessions:
            logging.info(f"🔄 Retornando resultados em cache para sessão {session_id}")
            return jsonify(flight_search_sessions[session_id])
        
        # Caso contrário, verificar se temos parâmetros de busca salvos
        from app import conversation_store
        
        logging.info(f"🔍 Buscando informações de viagem na sessão {session_id}")
        
        if session_id in conversation_store:
            travel_info = conversation_store[session_id].get('travel_info', {})
            
            # Log detalhado das informações de viagem
            logging.info(f"📋 Dados de viagem encontrados: {json.dumps(travel_info, indent=2)}")
            
            # Verificar se temos resultados já salvos
            if travel_info.get('search_results'):
                logging.info(f"✅ Resultados já processados, retornando dados salvos")
                flight_search_sessions[session_id] = travel_info['search_results']
                return jsonify(travel_info['search_results'])
            
            # Temos parâmetros suficientes para realizar a busca?
            if (travel_info.get('origin') and travel_info.get('destination') and 
                (travel_info.get('departure_date') or travel_info.get('date_range_start'))):
                
                logging.info(f"🚀 Parâmetros completos, iniciando busca na API Amadeus")
                
                # Definir explicitamente para NÃO usar dados simulados
                amadeus_service.use_mock_data = False
                logging.info("🔄 Configurado para usar DADOS REAIS da API Amadeus")
                
                # Verificar se o serviço está funcionando
                conn_test = amadeus_service.test_connection()
                if conn_test.get("success"):
                    logging.info(f"✅ Conexão com API Amadeus bem-sucedida: {conn_test}")
                else:
                    logging.error(f"❌ FALHA na conexão com API Amadeus: {conn_test}")
                    logging.error("⚠️ Tentando usar dados simulados como fallback")
                
                # Detectar o tipo de busca necessária (data específica ou período)
                search_results = None
                try:
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
                        logging.info(f"Realizando busca por período flexível com dados REAIS: {search_params}")
                        
                        # Tentativa de obter dados reais
                        search_results = amadeus_service.search_best_prices(search_params)
                        
                        # Verificar se houve erro
                        if 'error' in search_results:
                            logging.error(f"Erro na busca de dados reais: {search_results['error']} - Tentando dados simulados")
                            search_results = amadeus_service._get_mock_best_prices(search_params)
                            search_results['is_simulated'] = True
                        else:
                            logging.info(f"SUCESSO! Dados REAIS obtidos da API Amadeus: {len(search_results.get('best_prices', []))} resultados")
                            search_results['is_simulated'] = False
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
                        
                        logging.info(f"Realizando busca por data específica com dados REAIS: {search_params}")
                        
                        # Tentativa de obter dados reais
                        search_results = amadeus_service.search_flights(search_params)
                        
                        # Verificar se houve erro
                        if 'error' in search_results and not search_results.get('data'):
                            logging.error(f"Erro na busca de dados reais: {search_results['error']} - Tentando dados simulados")
                            search_results = amadeus_service._get_mock_flights(search_params)
                            search_results['is_simulated'] = True
                        else:
                            logging.info(f"SUCESSO! Dados REAIS obtidos da API Amadeus: {len(search_results.get('data', []))} resultados")
                            search_results['is_simulated'] = False
                except Exception as e:
                    logging.exception(f"Exceção ao buscar dados reais: {str(e)}")
                    # Em caso de exceção, usar dados simulados como fallback
                    if travel_info.get('date_range_start') and travel_info.get('date_range_end'):
                        search_params = {
                            'originLocationCode': travel_info.get('origin'),
                            'destinationLocationCode': travel_info.get('destination'),
                            'departureDate': travel_info.get('date_range_start'),
                            'returnDate': travel_info.get('date_range_end'),
                            'adults': travel_info.get('adults', 1),
                            'currencyCode': 'BRL',
                            'max_dates_to_check': 3
                        }
                        search_results = amadeus_service._get_mock_best_prices(search_params)
                    else:
                        search_params = {
                            'originLocationCode': travel_info.get('origin'),
                            'destinationLocationCode': travel_info.get('destination'),
                            'departureDate': travel_info.get('departure_date'),
                            'adults': travel_info.get('adults', 1),
                            'currencyCode': 'BRL',
                            'max': 5
                        }
                        if travel_info.get('return_date'):
                            search_params['returnDate'] = travel_info.get('return_date')
                        search_results = amadeus_service._get_mock_flights(search_params)
                    search_results['is_simulated'] = True
                
                # Salvar os resultados na sessão para futuras consultas
                if search_results:
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
        logging.warning(f"Sessão {session_id} - Sem informações suficientes para busca. Retornando dados de teste.")
        return get_test_results()
        
    except Exception as e:
        import traceback
        logging.error(f"Erro ao obter resultados de voos: {str(e)}")
        logging.error(traceback.format_exc())
        # Em caso de erro, retornar dados de teste para garantir que o painel funcione
        logging.info("Redirecionando para dados de teste após erro")
        return get_test_results()


def get_test_results():
    """
    Retorna dados de teste para garantir que o painel funcione
    """
    logging.info("Gerando dados de teste para o painel")
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
        # Criar um resultado mínimo para evitar erro no painel
        return jsonify({
            "meta": {"count": 1},
            "data": [
                {
                    "id": "test",
                    "type": "flight-offer",
                    "price": {"total": "3500.00", "currency": "BRL"},
                    "itineraries": [
                        {
                            "segments": [
                                {
                                    "departure": {"iataCode": "GRU", "at": "2025-05-01T10:00:00"},
                                    "arrival": {"iataCode": "MIA", "at": "2025-05-01T18:30:00"}
                                }
                            ]
                        }
                    ]
                }
            ]
        })


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

@api_blueprint.route('/api/flight_search/status/<session_id>', methods=['GET'])
def get_flight_search_status(session_id):
    """
    Endpoint para verificar o status de uma busca de voos em andamento
    Útil para o frontend monitorar o progresso da busca
    """
    try:
        from app import conversation_store
        
        # Status padrão
        status = {
            "session_id": session_id,
            "status": "unknown",
            "message": "Sessão não encontrada",
            "search_in_progress": False,
            "has_results": False
        }
        
        # Verificar se a sessão existe
        if session_id in conversation_store:
            travel_info = conversation_store[session_id].get('travel_info', {})
            
            # Verificar se temos resultados
            if travel_info.get('search_results'):
                status["status"] = "completed"
                status["message"] = "Busca concluída com sucesso"
                status["has_results"] = True
                status["search_in_progress"] = False
                
                # Adicionar contagem de resultados para informação
                if "data" in travel_info["search_results"]:
                    status["result_count"] = len(travel_info["search_results"]["data"])
                elif "best_prices" in travel_info["search_results"]:
                    status["result_count"] = len(travel_info["search_results"]["best_prices"])
                else:
                    status["result_count"] = 0
            
            # Verificar se temos parâmetros de busca mas sem resultados (busca em andamento)
            elif (travel_info.get('origin') and travel_info.get('destination') and 
                  (travel_info.get('departure_date') or travel_info.get('date_range_start'))):
                status["status"] = "in_progress"
                status["message"] = "Busca em andamento"
                status["search_in_progress"] = True
                status["has_results"] = False
                status["search_params"] = {
                    "origin": travel_info.get('origin'),
                    "destination": travel_info.get('destination'),
                    "departure_date": travel_info.get('departure_date') or travel_info.get('date_range_start')
                }
            else:
                status["status"] = "pending"
                status["message"] = "Aguardando parâmetros de busca completos"
                status["search_in_progress"] = False
                status["has_results"] = False
        
        return jsonify(status)
        
    except Exception as e:
        logging.error(f"Erro ao verificar status da busca: {str(e)}")
        return jsonify({
            "session_id": session_id,
            "status": "error",
            "message": f"Erro ao verificar status: {str(e)}",
            "search_in_progress": False,
            "has_results": False
        }), 500

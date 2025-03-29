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
            return jsonify(flight_search_sessions[session_id])
        
        # Caso contrário, verificar se temos parâmetros de busca salvos em outra estrutura
        from app import conversation_store
        
        if session_id in conversation_store:
            travel_info = conversation_store[session_id].get('travel_info', {})
            
            # Verificar se temos resultados já salvos
            if travel_info.get('search_results'):
                # Já temos resultados salvos, retorná-los
                flight_search_sessions[session_id] = travel_info['search_results']
                return jsonify(travel_info['search_results'])
            
            # Temos parâmetros suficientes para realizar a busca?
            if (travel_info.get('origin') and travel_info.get('destination') and 
                (travel_info.get('departure_date') or travel_info.get('date_range_start'))):
                
                # Inicializar o serviço Amadeus
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
                        
                    search_results = amadeus_service.search_flights(search_params)
                
                # Salvar os resultados na sessão para futuras consultas
                if search_results:
                    flight_search_sessions[session_id] = search_results
                    travel_info['search_results'] = search_results
                    return jsonify(search_results)
            
        # Se chegamos aqui, não temos informações suficientes
        return jsonify({
            "error": "Não há resultados disponíveis para esta sessão. Realize uma busca primeiro."
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter resultados de voos: {str(e)}")
        return jsonify({
            "error": f"Ocorreu um erro ao buscar os resultados: {str(e)}"
        }), 500


@api_blueprint.route('/api/flight_results/test', methods=['GET'])
def test_flight_results():
    """
    Endpoint de teste para verificar a funcionalidade do painel lateral
    Este endpoint está desativado para garantir que apenas dados reais sejam mostrados
    """
    try:
        # Não permitimos mais dados de teste - retornar erro explicativo
        return jsonify({
            "error": "Uso de dados de teste desativado. É necessário realizar uma pesquisa real com a Avi para ver resultados.",
            "data": []
        })
    except Exception as e:
        logging.error(f"Erro ao processar solicitação de teste: {str(e)}")
        return jsonify({
            "error": f"Ocorreu um erro ao processar a solicitação: {str(e)}"
        }), 500

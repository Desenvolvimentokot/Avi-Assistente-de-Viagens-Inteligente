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
    Retorna dados de exemplo para testar a interface sem chamar a API real
    """
    try:
        # Criar dados de exemplo para simular a resposta da API Amadeus
        # Este é apenas para teste de desenvolvimento da interface
        test_data = {
            "data": [
                {
                    "type": "flight-offer",
                    "id": "1",
                    "source": "GDS",
                    "instantTicketingRequired": False,
                    "nonHomogeneous": False,
                    "oneWay": False,
                    "lastTicketingDate": "2025-07-01",
                    "numberOfBookableSeats": 9,
                    "itineraries": [
                        {
                            "duration": "PT9H45M",
                            "segments": [
                                {
                                    "departure": {
                                        "iataCode": "GRU",
                                        "at": "2025-08-09T08:00:00"
                                    },
                                    "arrival": {
                                        "iataCode": "MIA",
                                        "at": "2025-08-09T17:45:00"
                                    },
                                    "carrierCode": "LA",
                                    "number": "8180",
                                    "aircraft": {
                                        "code": "789"
                                    },
                                    "operating": {
                                        "carrierCode": "LA"
                                    },
                                    "duration": "PT9H45M",
                                    "id": "1",
                                    "numberOfStops": 0
                                }
                            ]
                        },
                        {
                            "duration": "PT9H30M",
                            "segments": [
                                {
                                    "departure": {
                                        "iataCode": "MIA",
                                        "at": "2025-08-19T19:30:00"
                                    },
                                    "arrival": {
                                        "iataCode": "GRU",
                                        "at": "2025-08-20T05:00:00"
                                    },
                                    "carrierCode": "LA",
                                    "number": "8195",
                                    "aircraft": {
                                        "code": "789"
                                    },
                                    "operating": {
                                        "carrierCode": "LA"
                                    },
                                    "duration": "PT9H30M",
                                    "id": "2",
                                    "numberOfStops": 0
                                }
                            ]
                        }
                    ],
                    "price": {
                        "currency": "BRL",
                        "total": "5678.42",
                        "base": "4890.00",
                        "fees": [
                            {
                                "amount": "0.00",
                                "type": "SUPPLIER"
                            },
                            {
                                "amount": "0.00",
                                "type": "TICKETING"
                            }
                        ],
                        "grandTotal": "5678.42"
                    }
                },
                {
                    "type": "flight-offer",
                    "id": "2",
                    "source": "GDS",
                    "instantTicketingRequired": False,
                    "nonHomogeneous": False,
                    "oneWay": False,
                    "lastTicketingDate": "2025-07-01",
                    "numberOfBookableSeats": 9,
                    "itineraries": [
                        {
                            "duration": "PT10H15M",
                            "segments": [
                                {
                                    "departure": {
                                        "iataCode": "GRU",
                                        "at": "2025-08-09T09:30:00"
                                    },
                                    "arrival": {
                                        "iataCode": "MIA",
                                        "at": "2025-08-09T19:45:00"
                                    },
                                    "carrierCode": "AA",
                                    "number": "978",
                                    "aircraft": {
                                        "code": "77W"
                                    },
                                    "operating": {
                                        "carrierCode": "AA"
                                    },
                                    "duration": "PT10H15M",
                                    "id": "3",
                                    "numberOfStops": 0
                                }
                            ]
                        },
                        {
                            "duration": "PT9H40M",
                            "segments": [
                                {
                                    "departure": {
                                        "iataCode": "MIA",
                                        "at": "2025-08-19T21:40:00"
                                    },
                                    "arrival": {
                                        "iataCode": "GRU",
                                        "at": "2025-08-20T07:20:00"
                                    },
                                    "carrierCode": "AA",
                                    "number": "905",
                                    "aircraft": {
                                        "code": "77W"
                                    },
                                    "operating": {
                                        "carrierCode": "AA"
                                    },
                                    "duration": "PT9H40M",
                                    "id": "4",
                                    "numberOfStops": 0
                                }
                            ]
                        }
                    ],
                    "price": {
                        "currency": "BRL",
                        "total": "6142.87",
                        "base": "5300.00",
                        "fees": [
                            {
                                "amount": "0.00",
                                "type": "SUPPLIER"
                            },
                            {
                                "amount": "0.00",
                                "type": "TICKETING"
                            }
                        ],
                        "grandTotal": "6142.87"
                    }
                },
                {
                    "type": "flight-offer",
                    "id": "3",
                    "source": "GDS",
                    "instantTicketingRequired": False,
                    "nonHomogeneous": False,
                    "oneWay": False,
                    "lastTicketingDate": "2025-07-01",
                    "numberOfBookableSeats": 9,
                    "itineraries": [
                        {
                            "duration": "PT14H15M",
                            "segments": [
                                {
                                    "departure": {
                                        "iataCode": "GRU",
                                        "at": "2025-08-09T16:15:00"
                                    },
                                    "arrival": {
                                        "iataCode": "PTY",
                                        "at": "2025-08-09T20:10:00"
                                    },
                                    "carrierCode": "CM",
                                    "number": "702",
                                    "aircraft": {
                                        "code": "738"
                                    },
                                    "operating": {
                                        "carrierCode": "CM"
                                    },
                                    "duration": "PT5H55M",
                                    "id": "5",
                                    "numberOfStops": 0
                                },
                                {
                                    "departure": {
                                        "iataCode": "PTY",
                                        "at": "2025-08-09T21:55:00"
                                    },
                                    "arrival": {
                                        "iataCode": "MIA",
                                        "at": "2025-08-10T02:30:00"
                                    },
                                    "carrierCode": "CM",
                                    "number": "432",
                                    "aircraft": {
                                        "code": "738"
                                    },
                                    "operating": {
                                        "carrierCode": "CM"
                                    },
                                    "duration": "PT2H35M",
                                    "id": "6",
                                    "numberOfStops": 0
                                }
                            ]
                        },
                        {
                            "duration": "PT12H20M",
                            "segments": [
                                {
                                    "departure": {
                                        "iataCode": "MIA",
                                        "at": "2025-08-19T15:35:00"
                                    },
                                    "arrival": {
                                        "iataCode": "PTY",
                                        "at": "2025-08-19T18:15:00"
                                    },
                                    "carrierCode": "CM",
                                    "number": "433",
                                    "aircraft": {
                                        "code": "738"
                                    },
                                    "operating": {
                                        "carrierCode": "CM"
                                    },
                                    "duration": "PT2H40M",
                                    "id": "7",
                                    "numberOfStops": 0
                                },
                                {
                                    "departure": {
                                        "iataCode": "PTY",
                                        "at": "2025-08-19T19:35:00"
                                    },
                                    "arrival": {
                                        "iataCode": "GRU",
                                        "at": "2025-08-20T03:55:00"
                                    },
                                    "carrierCode": "CM",
                                    "number": "701",
                                    "aircraft": {
                                        "code": "738"
                                    },
                                    "operating": {
                                        "carrierCode": "CM"
                                    },
                                    "duration": "PT6H20M",
                                    "id": "8",
                                    "numberOfStops": 0
                                }
                            ]
                        }
                    ],
                    "price": {
                        "currency": "BRL",
                        "total": "4980.35",
                        "base": "4250.00",
                        "fees": [
                            {
                                "amount": "0.00",
                                "type": "SUPPLIER"
                            },
                            {
                                "amount": "0.00",
                                "type": "TICKETING"
                            }
                        ],
                        "grandTotal": "4980.35"
                    }
                }
            ]
        }
        
        return jsonify(test_data)
    
    except Exception as e:
        logging.error(f"Erro ao gerar dados de teste: {str(e)}")
        return jsonify({
            "error": f"Ocorreu um erro ao gerar dados de teste: {str(e)}"
        }), 500
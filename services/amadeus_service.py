# Primeira definição da classe removida para evitar duplicação
# O código começa com imports
#!/usr/bin/env python3
import os
import re
import logging
import requests
from datetime import datetime, timedelta
from amadeus import Client, ResponseError

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('amadeus_service')

class AmadeusService:
    """
    Serviço para integração com a API da Amadeus usando o SDK oficial
    """
    
    def __init__(self):
        """Inicializa o serviço Amadeus com credenciais das variáveis de ambiente"""
        self.api_key = os.environ.get('AMADEUS_API_KEY')
        self.api_secret = os.environ.get('AMADEUS_API_SECRET')
        self.client = None
        self.is_production = False
        self.base_url = "https://test.api.amadeus.com/v1"
        # Para compatibilidade com código existente
        self.use_mock_data = False
        
        # Inicializar o cliente
        if self.api_key and self.api_secret:
            try:
                self.client = Client(
                    client_id=self.api_key,
                    client_secret=self.api_secret,
                    logger=logger
                )
                logger.info(f"AmadeusService inicializado - Ambiente: {'Produção' if self.is_production else 'Teste'}")
                logger.info(f"URL Base: {self.base_url}")
                logger.info(f"API Key configurada:  {self.api_key[:3]}...{self.api_key[-4:]}")
                logger.info(f"API Secret configurada: {self.api_secret[:2]}...{self.api_secret[-2:]}")
            except Exception as e:
                logger.error(f"Erro ao inicializar cliente Amadeus: {str(e)}")
        else:
            logger.error("Credenciais da API Amadeus não encontradas. Verifique as variáveis de ambiente AMADEUS_API_KEY e AMADEUS_API_SECRET.")
    
    def get_token(self):
        """
        Verifica se o cliente está inicializado e retorna um token válido
        Essa função existe para manter compatibilidade com o código existente
        """
        if not self.client:
            logger.error("Cliente Amadeus não inicializado. Verifique as credenciais.")
            return None
        
        # O SDK gerencia automaticamente a obtenção e renovação do token
        # Esta função agora apenas verifica se o cliente foi inicializado corretamente
        try:
            logger.info("Renovando token de autenticação Amadeus")
            # Forçar a criação de um novo token
            token_response = self.client.auth.get_token()
            token = token_response[0].get('access_token')
            expires_in = token_response[0].get('expires_in')
            logger.debug(f"Resposta de autenticação: Status {token_response[1]}")
            
            if token:
                logger.info(f"Token obtido com sucesso. Expira em {expires_in} segundos.")
                # Mascarar o token ao exibir no log
                masked_token = f"{token[:5]}...{token[-5:]}" if len(token) > 10 else "***"
                return token
            else:
                logger.error("Falha ao obter token de autenticação")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter token de autenticação: {str(e)}")
            return None
    
    def search_flights(self, params):
        """
        Busca voos baseado nos parâmetros fornecidos
        
        Params:
        - originLocationCode: código IATA da origem (exemplo: "GRU")
        - destinationLocationCode: código IATA do destino (exemplo: "CDG")
        - departureDate: data de partida (formato YYYY-MM-DD)
        - returnDate: data de retorno (opcional, formato YYYY-MM-DD)
        - adults: número de adultos (default: 1)
        - currencyCode: moeda (default: "BRL")
        - max: número máximo de resultados (default: 10)
        """
        logger.info(f"Iniciando busca de voos: {params}")
        
        if not self.client:
            logger.error("Cliente Amadeus não inicializado. Verifique as credenciais.")
            return {"error": "Cliente Amadeus não inicializado", "data": []}
        
        # Verificar token antes de continuar
        if not self.get_token():
            logger.error("Não foi possível obter token de autenticação")
            return {"error": "Erro de autenticação", "data": []}
            
        try:
            # Extrair e validar os parâmetros
            origin = params.get('originLocationCode')
            destination = params.get('destinationLocationCode')
            departure_date = params.get('departureDate')
            return_date = params.get('returnDate')
            adults = int(params.get('adults', 1))
            currency = params.get('currencyCode', 'BRL')
            max_results = int(params.get('max', 10))
            
            if not origin or not destination or not departure_date:
                logger.error("Parâmetros obrigatórios faltando: origem, destino ou data de partida")
                return {"error": "Parâmetros incompletos", "data": []}
            
            # Verificar formato das datas
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', departure_date):
                logger.error(f"Formato de data inválido: {departure_date}")
                return {"error": "Formato de data inválido", "data": []}
            
            if return_date and not re.match(r'^\d{4}-\d{2}-\d{2}$', return_date):
                logger.error(f"Formato de data de retorno inválido: {return_date}")
                return {"error": "Formato de data de retorno inválido", "data": []}
            
            logger.debug(f"Enviando requisição GET para https://test.api.amadeus.com/v2/shopping/flight-offers")
            
            # Preparar parâmetros para o SDK
            sdk_params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults,
                'currencyCode': currency,
                'max': max_results
            }
            
            # Adicionar parâmetros opcionais
            if return_date:
                sdk_params['returnDate'] = return_date
            
            # Calcular tempo de início para log de performance
            start_time = datetime.now()
            
            try:
                # Fazer a chamada à API usando o SDK
                response = self.client.shopping.flight_offers_search.get(**sdk_params)
                
                # Calcular tempo de resposta
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Tempo de resposta: {elapsed:.2f}s")
                
                # Formatar a resposta
                if hasattr(response, 'data'):
                    logger.info(f"Busca bem-sucedida: {len(response.data)} voos encontrados")
                    
                    # Adicionar links de compra personalizados
                    for flight in response.data:
                        if not hasattr(flight, 'purchaseLinks'):
                            flight['purchaseLinks'] = self._generate_purchase_links(flight, params)
                    
                    result = {
                        "data": response.data,
                        "dictionaries": response.dictionaries if hasattr(response, 'dictionaries') else None,
                        "meta": response.meta if hasattr(response, 'meta') else None
                    }
                    
                    return result
                else:
                    logger.error("Resposta da API não contém dados")
                    return {"error": "Resposta da API não contém dados", "data": []}
                    
            except ResponseError as error:
                # Capturar erros específicos da API
                error_response = error.response
                status_code = error_response.status_code
                
                try:
                    error_data = error_response.data
                    errors = error_data.get('errors', [])
                    error_messages = [e.get('title', '') for e in errors]
                    error_details = [e.get('detail', '') for e in errors]
                    
                    logger.error(f"Erro na API ({status_code}): {error_response.body}")
                    
                    # Verificar erros específicos
                    if status_code == 401:
                        logger.error("Problema com permissões da API: A chave API não tem acesso a este endpoint")
                        return {"error": "Permissão de API insuficiente", "data": []}
                    elif status_code == 400:
                        logger.error(f"Erro nos parâmetros: {error_details}")
                        return {"error": f"Parâmetros inválidos: {', '.join(error_messages)}", "data": []}
                    else:
                        return {"error": f"Erro na API Amadeus: {', '.join(error_messages)}", "data": []}
                
                except Exception as e:
                    logger.error(f"Erro ao processar resposta de erro: {str(e)}")
                    return {"error": f"Erro na API Amadeus: {status_code}", "data": []}
        
        except Exception as e:
            logger.error(f"Erro ao buscar voos: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"Erro ao buscar voos: {str(e)}", "data": []}
    
    def _generate_purchase_links(self, flight_offer, params):
        """Gera links de compra para uma oferta de voo"""
        try:
            origin = params.get('originLocationCode', '')
            destination = params.get('destinationLocationCode', '')
            departure_date = params.get('departureDate', '')
            
            # Extrair informações da companhia aérea
            carrier_code = None
            if 'itineraries' in flight_offer and flight_offer['itineraries']:
                if 'segments' in flight_offer['itineraries'][0] and flight_offer['itineraries'][0]['segments']:
                    carrier_code = flight_offer['itineraries'][0]['segments'][0].get('carrierCode')
            
            # Gerar links de compra baseados na companhia aérea
            purchase_links = []
            
            # Link direto para a companhia aérea
            if carrier_code:
                if carrier_code == 'AF':  # Air France
                    url = f"https://www.airfrance.com.br/search?origin={origin}&destination={destination}&date={departure_date}&adult=1"
                    purchase_links.append({
                        "type": "direct",
                        "url": url,
                        "provider": "Air France"
                    })
                elif carrier_code == 'LH':  # Lufthansa
                    url = f"https://www.lufthansa.com/br/pt/homepage?travelFromCode={origin}&travelToCode={destination}&outwardDateDep={departure_date}&adult=1"
                    purchase_links.append({
                        "type": "direct",
                        "url": url,
                        "provider": "Lufthansa"
                    })
                elif carrier_code == 'LA':  # LATAM
                    url = f"https://www.latamairlines.com/br/pt/oferta-voos?origin={origin}&destination={destination}&outbound={departure_date}&adults=1"
                    purchase_links.append({
                        "type": "direct",
                        "url": url,
                        "provider": "LATAM"
                    })
            
            # Links para OTAs (Online Travel Agencies)
            # Decolar
            url_decolar = f"https://www.decolar.com/shop/flights/results/{origin}/{destination}/{departure_date}/1/0/0"
            purchase_links.append({
                "type": "agency",
                "url": url_decolar,
                "provider": "Decolar.com"
            })
            
            return purchase_links
            
        except Exception as e:
            logger.error(f"Erro ao gerar links de compra: {str(e)}")
            return []
    
    def search_hotels(self, params):
        """
        Busca hotéis baseado nos parâmetros fornecidos usando o SDK da Amadeus
        
        Params:
        - cityCode: código da cidade (exemplo: "PAR" para Paris)
        - radius: raio em KM (opcional)
        - radiusUnit: unidade do raio (KM ou MILE, opcional)
        """
        logger.info(f"Iniciando busca de hotéis: {params}")
        
        if not self.client:
            logger.error("Cliente Amadeus não inicializado. Verifique as credenciais.")
            return {"error": "Cliente Amadeus não inicializado", "data": []}
        
        # Verificar token antes de continuar
        if not self.get_token():
            logger.error("Não foi possível obter token de autenticação")
            return {"error": "Erro de autenticação", "data": []}
            
        try:
            # Extrair e validar os parâmetros
            city_code = params.get('cityCode')
            
            if not city_code:
                logger.error("Parâmetro obrigatório faltando: cityCode")
                return {"error": "Parâmetro cityCode obrigatório", "data": []}
            
            # Construir parâmetros para o SDK
            sdk_params = {
                'cityCode': city_code
            }
            
            # Adicionar parâmetros opcionais
            if 'radius' in params:
                sdk_params['radius'] = params['radius']
            
            if 'radiusUnit' in params:
                sdk_params['radiusUnit'] = params['radiusUnit']
            
            # Calcular tempo de início para log de performance
            start_time = datetime.now()
            
            try:
                # Fazer a chamada à API usando o SDK
                response = self.client.reference_data.locations.hotels.by_city.get(**sdk_params)
                
                # Calcular tempo de resposta
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Tempo de resposta: {elapsed:.2f}s")
                
                # Formatar a resposta
                if hasattr(response, 'data'):
                    logger.info(f"Busca bem-sucedida: {len(response.data)} hotéis encontrados")
                    
                    return {
                        "data": response.data,
                        "meta": response.meta if hasattr(response, 'meta') else None
                    }
                else:
                    logger.error("Resposta da API não contém dados")
                    return {"error": "Resposta da API não contém dados", "data": []}
                    
            except ResponseError as error:
                # Capturar erros específicos da API
                error_response = error.response
                status_code = error_response.status_code
                
                try:
                    error_data = error_response.data
                    errors = error_data.get('errors', [])
                    error_messages = [e.get('title', '') for e in errors]
                    
                    logger.error(f"Erro na API ({status_code}): {error_response.body}")
                    
                    return {"error": f"Erro na API Amadeus: {', '.join(error_messages)}", "data": []}
                
                except Exception as e:
                    logger.error(f"Erro ao processar resposta de erro: {str(e)}")
                    return {"error": f"Erro na API Amadeus: {status_code}", "data": []}
        
        except Exception as e:
            logger.error(f"Erro ao buscar hotéis: {str(e)}")
            return {"error": f"Erro ao buscar hotéis: {str(e)}", "data": []}
    
    def search_hotel_offers(self, params):
        """
        Busca ofertas de hotéis baseado nos parâmetros fornecidos usando o SDK da Amadeus
        
        Params:
        - hotelIds: lista de IDs de hotéis separados por vírgula
        - adults: número de adultos (default: 1)
        - checkInDate: data de check-in (formato YYYY-MM-DD)
        - checkOutDate: data de check-out (formato YYYY-MM-DD)
        - currency: moeda (default: "BRL")
        """
        logger.info(f"Iniciando busca de ofertas de hotéis: {params}")
        
        if not self.client:
            logger.error("Cliente Amadeus não inicializado. Verifique as credenciais.")
            return {"error": "Cliente Amadeus não inicializado", "data": []}
        
        # Verificar token antes de continuar
        if not self.get_token():
            logger.error("Não foi possível obter token de autenticação")
            return {"error": "Erro de autenticação", "data": []}
            
        try:
            # Extrair e validar os parâmetros
            hotel_ids = params.get('hotelIds')
            adults = params.get('adults', 1)
            check_in_date = params.get('checkInDate')
            check_out_date = params.get('checkOutDate')
            currency = params.get('currency', 'BRL')
            
            # Validar parâmetros obrigatórios
            if not hotel_ids:
                logger.error("Parâmetro obrigatório faltando: hotelIds")
                return {"error": "Parâmetro hotelIds obrigatório", "data": []}
                
            if not check_in_date or not check_out_date:
                logger.error("Parâmetros obrigatórios faltando: checkInDate ou checkOutDate")
                return {"error": "Parâmetros de data obrigatórios", "data": []}
            
            # Verificar formato das datas
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', check_in_date):
                logger.error(f"Formato de data de check-in inválido: {check_in_date}")
                return {"error": "Formato de data de check-in inválido", "data": []}
            
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', check_out_date):
                logger.error(f"Formato de data de check-out inválido: {check_out_date}")
                return {"error": "Formato de data de check-out inválido", "data": []}
            
            # Construir parâmetros para o SDK
            sdk_params = {
                'hotelIds': hotel_ids,
                'adults': adults,
                'checkInDate': check_in_date,
                'checkOutDate': check_out_date,
                'currency': currency
            }
            
            # Adicionar parâmetros opcionais
            if 'roomQuantity' in params:
                sdk_params['roomQuantity'] = params['roomQuantity']
            
            # Calcular tempo de início para log de performance
            start_time = datetime.now()
            
            try:
                # Fazer a chamada à API usando o SDK
                response = self.client.shopping.hotel_offers.get(**sdk_params)
                
                # Calcular tempo de resposta
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Tempo de resposta: {elapsed:.2f}s")
                
                # Formatar a resposta
                if hasattr(response, 'data'):
                    logger.info(f"Busca bem-sucedida: {len(response.data)} ofertas de hotéis encontradas")
                    
                    return {
                        "data": response.data,
                        "meta": response.meta if hasattr(response, 'meta') else None
                    }
                else:
                    logger.error("Resposta da API não contém dados")
                    return {"error": "Resposta da API não contém dados", "data": []}
                    
            except ResponseError as error:
                # Capturar erros específicos da API
                error_response = error.response
                status_code = error_response.status_code
                
                try:
                    error_data = error_response.data
                    errors = error_data.get('errors', [])
                    error_messages = [e.get('title', '') for e in errors]
                    
                    logger.error(f"Erro na API ({status_code}): {error_response.body}")
                    
                    return {"error": f"Erro na API Amadeus: {', '.join(error_messages)}", "data": []}
                
                except Exception as e:
                    logger.error(f"Erro ao processar resposta de erro: {str(e)}")
                    return {"error": f"Erro na API Amadeus: {status_code}", "data": []}
        
        except Exception as e:
            logger.error(f"Erro ao buscar ofertas de hotéis: {str(e)}")
            return {"error": f"Erro ao buscar ofertas de hotéis: {str(e)}", "data": []}
    
    def _get_mock_flights(self, params):
        """Retorna dados simulados de voos para desenvolvimento com links de compra"""
        origin = params.get('originLocationCode', 'GRU')
        destination = params.get('destinationLocationCode', 'CDG')
        departure_date = params.get('departureDate', '2024-12-10')
        
        # Obter códigos de aeroporto e companhias válidos
        origin_code = origin if len(origin) == 3 else 'GRU'
        destination_code = destination if len(destination) == 3 else 'CDG'
        
        # Criar URLs para compra com base nos códigos de aeroporto e datas
        purchase_url_airfrance = f"https://www.airfrance.com.br/search?origin={origin_code}&destination={destination_code}&date={departure_date}&adult=1"
        purchase_url_lufthansa = f"https://www.lufthansa.com/br/pt/homepage?travelFromCode={origin_code}&travelToCode={destination_code}&outwardDateDep={departure_date}&adult=1"
        
        mock_data = {
            "meta": {
                "count": 2
            },
            "data": [
                {
                    "id": "1",
                    "type": "flight-offer",
                    "price": {
                        "total": "3250.42",
                        "currency": "BRL"
                    },
                    "source": "GDS",
                    "instantTicketingRequired": False,
                    "nonHomogeneous": False,
                    "oneWay": False,
                    "lastTicketingDate": "2024-12-01",
                    "numberOfBookableSeats": 9,
                    "itineraries": [
                        {
                            "duration": "PT14H20M",
                            "segments": [
                                {
                                    "carrierCode": "AF",
                                    "number": "401",
                                    "departure": {
                                        "iataCode": origin_code,
                                        "at": f"{departure_date}T23:35:00"
                                    },
                                    "arrival": {
                                        "iataCode": destination_code,
                                        "at": f"{departure_date}T15:55:00"
                                    },
                                    "aircraft": {
                                        "code": "77W"
                                    },
                                    "operating": {
                                        "carrierCode": "AF"
                                    },
                                    "duration": "PT11H20M"
                                }
                            ]
                        }
                    ],
                    "price": {
                        "currency": "BRL",
                        "total": "3250.42",
                        "base": "2840.00",
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
                        "grandTotal": "3250.42",
                        "billingCurrency": "BRL"
                    },
                    "pricingOptions": {
                        "fareType": ["PUBLISHED"],
                        "includedCheckedBagsOnly": True
                    },
                    "validatingAirlineCodes": ["AF"],
                    "travelerPricings": [
                        {
                            "travelerId": "1",
                            "fareOption": "STANDARD",
                            "travelerType": "ADULT",
                            "price": {
                                "currency": "BRL",
                                "total": "3250.42"
                            }
                        }
                    ],
                    "purchaseLinks": [
                        {
                            "type": "direct",
                            "url": purchase_url_airfrance,
                            "provider": "Air France"
                        },
                        {
                            "type": "agency",
                            "url": "https://www.decolar.com",
                            "provider": "Decolar.com"
                        }
                    ]
                },
                {
                    "id": "2",
                    "type": "flight-offer",
                    "price": {
                        "total": "4120.18",
                        "currency": "BRL"
                    },
                    "source": "GDS",
                    "instantTicketingRequired": False,
                    "nonHomogeneous": False,
                    "oneWay": False,
                    "lastTicketingDate": "2024-12-01",
                    "numberOfBookableSeats": 5,
                    "itineraries": [
                        {
                            "duration": "PT13H15M",
                            "segments": [
                                {
                                    "carrierCode": "LH",
                                    "number": "507",
                                    "departure": {
                                        "iataCode": origin_code,
                                        "at": f"{departure_date}T18:15:00"
                                    },
                                    "arrival": {
                                        "iataCode": "FRA",
                                        "at": f"{departure_date}T10:30:00"
                                    },
                                    "aircraft": {
                                        "code": "748"
                                    },
                                    "operating": {
                                        "carrierCode": "LH"
                                    },
                                    "duration": "PT11H15M"
                                },
                                {
                                    "carrierCode": "LH",
                                    "number": "1040",
                                    "departure": {
                                        "iataCode": "FRA",
                                        "at": f"{departure_date}T12:45:00"
                                    },
                                    "arrival": {
                                        "iataCode": destination_code,
                                        "at": f"{departure_date}T14:00:00"
                                    },
                                    "aircraft": {
                                        "code": "32N"
                                    },
                                    "operating": {
                                        "carrierCode": "LH"
                                    },
                                    "duration": "PT1H15M"
                                }
                            ]
                        }
                    ],
                    "price": {
                        "currency": "BRL",
                        "total": "4120.18",
                        "base": "3750.00",
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
                        "grandTotal": "4120.18",
                        "billingCurrency": "BRL"
                    },
                    "pricingOptions": {
                        "fareType": ["PUBLISHED"],
                        "includedCheckedBagsOnly": True
                    },
                    "validatingAirlineCodes": ["LH"],
                    "travelerPricings": [
                        {
                            "travelerId": "1",
                            "fareOption": "STANDARD",
                            "travelerType": "ADULT",
                            "price": {
                                "currency": "BRL",
                                "total": "4120.18"
                            }
                        }
                    ],
                    "purchaseLinks": [
                        {
                            "type": "direct",
                            "url": purchase_url_lufthansa,
                            "provider": "Lufthansa"
                        },
                        {
                            "type": "agency",
                            "url": "https://www.submarinoviagens.com.br",
                            "provider": "Submarino Viagens"
                        }
                    ]
                }
            ]
        }
        
        return mock_data
    
    def _get_mock_hotels(self, params):
        """Retorna dados simulados de hotéis para desenvolvimento"""
        city_code = params.get('cityCode', 'PAR')
        
        mock_data = {
            "meta": {
                "count": 2
            },
            "data": [
                {
                    "hotelId": "HLLOR123",
                    "name": "Le Grand Hotel Paris",
                    "cityCode": city_code,
                    "address": {
                        "lines": ["15 Avenue des Champs-Élysées"],
                        "postalCode": "75008",
                        "cityName": "Paris",
                        "countryCode": "FR"
                    }
                },
                {
                    "hotelId": "HLMON456",
                    "name": "Montmartre Residence",
                    "cityCode": city_code,
                    "address": {
                        "lines": ["8 Rue des Abbesses"],
                        "postalCode": "75018",
                        "cityName": "Paris",
                        "countryCode": "FR"
                    }
                }
            ]
        }
        
        return mock_data
    
    def _get_mock_hotel_offers(self, params):
        """Retorna dados simulados de ofertas de hotéis para desenvolvimento"""
        hotel_ids = params.get('hotelIds', 'HLLOR123,HLMON456').split(',')
        
        mock_data = {
            "meta": {
                "count": len(hotel_ids)
            },
            "data": []
        }
        
        for i, hotel_id in enumerate(hotel_ids):
            hotel_name = "Hotel Desconhecido"
            if hotel_id == "HLLOR123":
                hotel_name = "Le Grand Hotel Paris"
            elif hotel_id == "HLMON456":
                hotel_name = "Montmartre Residence"
                
            price = 350 + (i * 100)
            
            hotel_offer = {
                "hotel": {
                    "hotelId": hotel_id,
                    "name": hotel_name,
                    "rating": "4"
                },
                "offers": [
                    {
                        "id": f"offer_{i+1}",
                        "price": {
                            "total": str(price),
                            "currency": "BRL"
                        }
                    }
                ]
            }
            
            mock_data["data"].append(hotel_offer)
        
        return mock_data
        
    def search_best_prices(self, params):
        """
        Busca melhores preços para um período flexível usando o SDK da Amadeus
        
        Params:
        - originLocationCode: código IATA da origem
        - destinationLocationCode: código IATA do destino
        - departureDate: data inicial para busca (formato YYYY-MM-DD)
        - returnDate: data final para busca (opcional, formato YYYY-MM-DD)
        - adults: número de adultos (default: 1)
        - currencyCode: moeda (default: "BRL")
        - max_dates_to_check: número máximo de datas a serem verificadas (para evitar muitas chamadas)
        """
        import random
        
        logger.info(f"Iniciando busca de melhores preços: {params}")
        
        if self.use_mock_data:
            return self._get_mock_best_prices(params)
            
        try:
            # Extrair parâmetros
            origin = params.get('originLocationCode')
            destination = params.get('destinationLocationCode')
            start_date = params.get('departureDate')
            end_date = params.get('returnDate')
            adults = params.get('adults', 1)
            currency = params.get('currencyCode', 'BRL')
            max_dates = params.get('max_dates_to_check', 5)  # Limitar o número de datas
            
            # Validar parâmetros
            if not origin or not destination or not start_date or not end_date:
                return {"error": "Parâmetros incompletos para busca de melhores preços"}
            
            # Converter datas para objetos datetime
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                return {"error": "Formato de data inválido, use YYYY-MM-DD"}
            
            # Gerar datas entre o início e fim para verificação
            date_range = []
            current_date = start_date_obj
            while current_date <= end_date_obj and len(date_range) < max_dates:
                date_range.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=7)  # Verificar semanalmente para eficiência
            
            # Buscar preços para cada data
            best_prices = []
            for departure_date in date_range:
                # Configurar busca para uma data específica
                search_params = {
                    'originLocationCode': origin,
                    'destinationLocationCode': destination,
                    'departureDate': departure_date,
                    'adults': adults,
                    'currencyCode': currency,
                    'max': 1  # Apenas a opção mais barata
                }
                
                # Fazer a busca
                flight_results = self.search_flights(search_params)
                
                # Verificar se a busca foi bem-sucedida
                if 'error' not in flight_results and flight_results.get('data', []):
                    flights = flight_results.get('data', [])
                    if flights:
                        # Obter o preço do primeiro voo (mais barato)
                        flight = flights[0]
                        price_info = flight.get('price', {})
                        price = price_info.get('total', '0')
                        
                        # Adicionar à lista de melhores preços
                        best_prices.append({
                            'date': departure_date,
                            'price': float(price),
                            'currency': currency,
                            'flight_id': flight.get('id', ''),
                            # Gerar um link de afiliado (exemplo)
                            'affiliate_link': f"https://example.com/flights?origin={origin}&destination={destination}&date={departure_date}"
                        })
            
            # Ordenar por preço
            best_prices.sort(key=lambda x: x['price'])
            
            return {
                "best_prices": best_prices,
                "currency": currency,
                "origin": origin,
                "destination": destination
            }
            
        except Exception as e:
            logging.error(f"Erro ao buscar melhores preços: {str(e)}")
            # Se ocorrer um erro, usar dados simulados
            self.use_mock_data = True
            return self._get_mock_best_prices(params)
            
    def _get_mock_best_prices(self, params):
        """Retorna dados simulados de melhores preços com dados de aeroportos reais"""
        import random
        from datetime import datetime, timedelta
        
        # Verificar e corrigir códigos de aeroporto
        origin_raw = params.get('originLocationCode', 'GRU')
        destination_raw = params.get('destinationLocationCode', 'MIA')
        
        # Mapear códigos de aeroporto válidos
        airport_map = {
            # Principais aeroportos brasileiros
            'GRU': {'code': 'GRU', 'name': 'São Paulo', 'full_name': 'Aeroporto de Guarulhos'},
            'CGH': {'code': 'CGH', 'name': 'São Paulo', 'full_name': 'Aeroporto de Congonhas'},
            'SDU': {'code': 'SDU', 'name': 'Rio de Janeiro', 'full_name': 'Aeroporto Santos Dumont'},
            'GIG': {'code': 'GIG', 'name': 'Rio de Janeiro', 'full_name': 'Aeroporto do Galeão'},
            'BSB': {'code': 'BSB', 'name': 'Brasília', 'full_name': 'Aeroporto de Brasília'},
            'SSA': {'code': 'SSA', 'name': 'Salvador', 'full_name': 'Aeroporto de Salvador'},
            'REC': {'code': 'REC', 'name': 'Recife', 'full_name': 'Aeroporto de Recife'},
            'FOR': {'code': 'FOR', 'name': 'Fortaleza', 'full_name': 'Aeroporto de Fortaleza'},
            'CWB': {'code': 'CWB', 'name': 'Curitiba', 'full_name': 'Aeroporto de Curitiba'},
            'POA': {'code': 'POA', 'name': 'Porto Alegre', 'full_name': 'Aeroporto de Porto Alegre'},
            'VCP': {'code': 'VCP', 'name': 'Campinas', 'full_name': 'Aeroporto de Viracopos'},
            'CNF': {'code': 'CNF', 'name': 'Belo Horizonte', 'full_name': 'Aeroporto de Confins'},
            
            # Principais destinos internacionais
            'MIA': {'code': 'MIA', 'name': 'Miami', 'full_name': 'Aeroporto de Miami'},
            'JFK': {'code': 'JFK', 'name': 'Nova York', 'full_name': 'Aeroporto JFK'},
            'LIS': {'code': 'LIS', 'name': 'Lisboa', 'full_name': 'Aeroporto de Lisboa'},
            'MAD': {'code': 'MAD', 'name': 'Madri', 'full_name': 'Aeroporto de Madri'},
            'CDG': {'code': 'CDG', 'name': 'Paris', 'full_name': 'Aeroporto Charles de Gaulle'},
            'LHR': {'code': 'LHR', 'name': 'Londres', 'full_name': 'Aeroporto de Heathrow'},
            'FCO': {'code': 'FCO', 'name': 'Roma', 'full_name': 'Aeroporto de Fiumicino'},
            'EZE': {'code': 'EZE', 'name': 'Buenos Aires', 'full_name': 'Aeroporto de Ezeiza'},
            'SCL': {'code': 'SCL', 'name': 'Santiago', 'full_name': 'Aeroporto de Santiago'},
        }
        
        # Nome amigável para os destinos
        name_to_code = {
            'são paulo': 'GRU',
            'sp': 'GRU', 
            'guarulhos': 'GRU',
            'congonhas': 'CGH',
            'rio': 'GIG',
            'rio de janeiro': 'GIG',
            'galeão': 'GIG',
            'santos dumont': 'SDU',
            'brasília': 'BSB',
            'brasilia': 'BSB',
            'salvador': 'SSA',
            'bahia': 'SSA',
            'recife': 'REC',
            'fortaleza': 'FOR',
            'curitiba': 'CWB',
            'porto alegre': 'POA',
            'campinas': 'VCP',
            'belo horizonte': 'CNF',
            
            'miami': 'MIA',
            'nova york': 'JFK',
            'new york': 'JFK',
            'lisboa': 'LIS',
            'madri': 'MAD',
            'madrid': 'MAD',
            'paris': 'CDG',
            'londres': 'LHR',
            'london': 'LHR',
            'roma': 'FCO',
            'rome': 'FCO',
            'buenos aires': 'EZE',
            'santiago': 'SCL',
        }
        
        # Tentar obter códigos válidos
        if len(origin_raw) == 3 and origin_raw.upper() in airport_map:
            origin = origin_raw.upper()
            origin_info = airport_map[origin]
        else:
            origin_lower = origin_raw.lower()
            if origin_lower in name_to_code:
                origin = name_to_code[origin_lower]
                origin_info = airport_map[origin]
            else:
                # Usar um padrão para testes
                origin = 'GRU'
                origin_info = airport_map[origin]
                
        if len(destination_raw) == 3 and destination_raw.upper() in airport_map:
            destination = destination_raw.upper()
            destination_info = airport_map[destination]
        else:
            destination_lower = destination_raw.lower()
            if destination_lower in name_to_code:
                destination = name_to_code[destination_lower]
                destination_info = airport_map[destination]
            else:
                # Se o usuário mencionar Miami, usar esse código
                if "miami" in destination_lower or "mia" in destination_lower:
                    destination = 'MIA'
                # Caso contrário, usar um destino padrão
                else:
                    destination = 'MIA'
                destination_info = airport_map[destination]
                
        start_date = params.get('departureDate', '2024-12-01')
        end_date = params.get('returnDate', '2024-12-31')
        currency = params.get('currencyCode', 'BRL')
        
        # Gerar datas no período solicitado
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Gerar até 5 datas aleatórias dentro do período
        date_range = []
        days_total = (end_date_obj - start_date_obj).days
        
        if days_total > 0:
            for _ in range(min(5, days_total)):
                random_days = random.randint(0, days_total)
                date = start_date_obj + timedelta(days=random_days)
                if date.strftime('%Y-%m-%d') not in date_range:
                    date_range.append(date.strftime('%Y-%m-%d'))
        else:
            date_range.append(start_date)
        
        # Ordenar datas
        date_range.sort()
        
        # Gerar preços para cada data
        best_prices = []
        base_price = 950  # Preço base para São Paulo -> Salvador
        
        for date in date_range:
            # Variação de preço de +/- 20%
            price_variation = random.uniform(0.8, 1.2)
            price = round(base_price * price_variation, 2)
            
            # Selecionar um link de afiliado para este voo
            affiliate_links = [
                {
                    "provider": "Decolar",
                    "url": f"https://www.decolar.com/shop/flights/results/{origin}/{destination}/{date}/1/0/0"
                },
                {
                    "provider": "Submarino Viagens",
                    "url": f"https://www.submarinoviagens.com.br/Passagem/{origin}/{destination}/{date}/{date}/1/0/0/1/Economica"
                },
                {
                    "provider": "ViajaNet",
                    "url": f"https://www.viajanet.com.br/busca/passagens/{origin}/{destination}/{date}/1/0/0/Economy/-/-/-"
                }
            ]
            
            # Escolher um provedor aleatório
            selected_affiliate = random.choice(affiliate_links)
            
            # Companhias preferenciais para diferentes rotas
            preferred_airlines = {
                'MIA': ['LATAM', 'American Airlines', 'GOL'],
                'JFK': ['LATAM', 'American Airlines', 'Delta'],
                'LIS': ['TAP Portugal', 'LATAM'],
                'MAD': ['Iberia', 'Air Europa'],
                'CDG': ['Air France', 'LATAM'],
                'LHR': ['British Airways', 'LATAM'],
                'FCO': ['Alitalia', 'LATAM'],
                'EZE': ['Aerolíneas Argentinas', 'LATAM'],
                'SCL': ['LATAM', 'Sky Airline'],
            }
            
            # Aeroportos de conexão comuns
            common_connections = {
                'MIA': ['GRU', 'PTY', 'BOG'],  # São Paulo, Panamá, Bogotá
                'JFK': ['GRU', 'ATL', 'MIA'],  # São Paulo, Atlanta, Miami
                'LIS': ['GRU', 'MAD'],         # São Paulo, Madri
                'MAD': ['GRU', 'LIS'],         # São Paulo, Lisboa
                'CDG': ['GRU', 'LIS', 'MAD'],  # São Paulo, Lisboa, Madri
                'LHR': ['GRU', 'CDG', 'MAD'],  # São Paulo, Paris, Madri
                'FCO': ['GRU', 'LIS', 'CDG'],  # São Paulo, Lisboa, Paris
                'EZE': ['GRU'],                # São Paulo
                'SCL': ['GRU'],                # São Paulo
            }
            
            # Selecionar companhia aérea preferencial para o destino
            if destination in preferred_airlines:
                airlines = preferred_airlines[destination]
                airline = random.choice(airlines)
            else:
                airlines = ['LATAM', 'GOL', 'Azul', 'American Airlines']
                airline = random.choice(airlines)
                
            # Calcular duração do voo (baseado em distâncias reais aproximadas)
            durations = {
                'MIA': '8h 25m',
                'JFK': '9h 50m',
                'LIS': '10h 15m',
                'MAD': '10h 30m',
                'CDG': '11h 20m',
                'LHR': '11h 50m',
                'FCO': '12h 10m',
                'EZE': '3h 45m',
                'SCL': '4h 30m',
            }
            
            flight_duration = durations.get(destination, '8h 30m')
            
            # Calcular horários de partida e chegada
            departure_datetime = datetime.strptime(f"{date} 10:00:00", '%Y-%m-%d %H:%M:%S')
            arrival_datetime = departure_datetime + timedelta(hours=int(flight_duration.split('h')[0]), 
                                                           minutes=int(flight_duration.split('h ')[1].replace('m', '')))
            
            # Verificar se há conexão
            has_connection = random.choice([True, False])
            connection_airport = None
            connection_time = None
            
            if has_connection and destination in common_connections and common_connections[destination]:
                connection_airport = random.choice(common_connections[destination])
                connection_time = f"{random.randint(1, 3)}h {random.randint(10, 59)}m"
            
            # Número do voo (padrão IATA)
            flight_number = f"{random.randint(100, 9999)}"
            
            # Adicionar detalhas do voo nos resultados
            best_prices.append({
                'date': date,
                'price': price,
                'currency': currency,
                'flight_id': f"mock-{origin}-{destination}-{date}",
                'is_simulated': True,
                'affiliate_link': selected_affiliate["url"],
                'provider': selected_affiliate["provider"],
                'origin_info': origin_info,
                'destination_info': destination_info,
                'airline': airline,
                'flight_number': flight_number,
                'departure_time': departure_datetime.strftime('%H:%M'),
                'arrival_time': arrival_datetime.strftime('%H:%M'),
                'duration': flight_duration,
                'has_connection': has_connection,
                'connection_airport': connection_airport,
                'connection_time': connection_time,
                'baggage_allowance': '1 bagagem de mão + 1 bagagem despachada',
                'aircraft': random.choice(['Boeing 777', 'Boeing 787', 'Airbus A330', 'Airbus A350']),
                'departure_date': date,
                'departure_datetime': departure_datetime.strftime('%Y-%m-%d %H:%M'),
                'arrival_datetime': arrival_datetime.strftime('%Y-%m-%d %H:%M'),
                'flight_details': {
                    'airline_code': airline[:2],
                    'meal_service': True,
                    'entertainment': True,
                    'wifi': random.choice([True, False]),
                    'power_outlets': True,
                    'seat_pitch': f"{random.randint(29, 34)} polegadas",
                }
            })
        
        # Ordenar por preço
        best_prices.sort(key=lambda x: x['price'])
        
        return {
            "best_prices": best_prices,
            "currency": currency,
            "origin": origin,
            "destination": destination,
            "is_simulated": True
        }
    
    def test_connection(self):
        """Testa a conexão com a API do Amadeus e retorna um diagnóstico"""
        results = {
            "success": False,
            "credentials_set": bool(self.api_key and self.api_secret),
            "token": None,
            "error": None,
            "using_mock_data": self.use_mock_data
        }
        
        try:
            token = self.get_token()
            results["token"] = bool(token)
            
            if token:
                # Teste simples com uma API que não precisa de parâmetros complexos
                url = "https://test.api.amadeus.com/v1/reference-data/locations/cities"
                headers = {
                    "Authorization": f"Bearer {token}"
                }
                params = {
                    "keyword": "PAR",
                    "max": 1
                }
                
                response = requests.get(url, headers=headers, params=params)
                results["status_code"] = response.status_code
                
                if response.status_code == 200:
                    results["success"] = True
                else:
                    results["error"] = response.text
            else:
                results["error"] = "Falha ao obter token de autenticação"
                
        except Exception as e:
            results["error"] = str(e)
            
        return results

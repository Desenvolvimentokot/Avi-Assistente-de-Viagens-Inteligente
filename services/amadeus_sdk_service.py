#!/usr/bin/env python3
"""
Serviço Amadeus baseado no SDK oficial da Amadeus
https://github.com/amadeus4dev/amadeus-python
"""
import os
import logging
from datetime import datetime, timedelta
from amadeus import Client, ResponseError

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('amadeus_service')

class AmadeusSDKService:
    """
    Implementação oficial do SDK da Amadeus para serviços de viagem
    """
    
    def __init__(self):
        """Inicializa o serviço Amadeus com credenciais"""
        self.api_key = os.environ.get('AMADEUS_API_KEY')
        self.api_secret = os.environ.get('AMADEUS_API_SECRET')
        self.client = None
        
        # Inicializar o cliente Amadeus com o SDK oficial
        if self.api_key and self.api_secret:
            try:
                self.client = Client(
                    client_id=self.api_key,
                    client_secret=self.api_secret,
                    logger=logger
                )
                logger.info(f"Amadeus SDK inicializado com sucesso")
                logger.info(f"API Key configurada: {self.api_key[:3]}...{self.api_key[-4:]}")
                logger.info(f"API Secret configurada: {self.api_secret[:2]}...{self.api_secret[-2:]}")
            except Exception as e:
                logger.error(f"Erro ao inicializar cliente Amadeus SDK: {str(e)}")
        else:
            logger.error("Credenciais da API Amadeus não encontradas nas variáveis de ambiente")
    
    def search_flights(self, params):
        """
        Busca voos com o SDK oficial da Amadeus
        
        Params:
        - originLocationCode: código IATA da origem (exemplo: "GRU")
        - destinationLocationCode: código IATA do destino (exemplo: "CDG")
        - departureDate: data de partida (formato YYYY-MM-DD)
        - returnDate: data de retorno (opcional, formato YYYY-MM-DD)
        - adults: número de adultos (default: 1)
        - currencyCode: moeda (default: "BRL")
        - max: número máximo de resultados (default: 10)
        """
        logger.info(f"Buscando voos com Amadeus SDK: {params}")
        
        if not self.client:
            logger.error("Cliente Amadeus SDK não inicializado")
            return {"error": "Cliente Amadeus não inicializado", "data": []}
        
        try:
            # Extrair parâmetros da requisição
            origin = params.get('originLocationCode')
            destination = params.get('destinationLocationCode')
            departure_date = params.get('departureDate')
            return_date = params.get('returnDate')
            adults = int(params.get('adults', 1))
            currency = params.get('currencyCode', 'BRL')
            max_results = int(params.get('max', 10))
            
            # Verificar parâmetros obrigatórios
            if not origin or not destination or not departure_date:
                logger.error("Parâmetros obrigatórios faltando")
                return {"error": "Parâmetros incompletos: é necessário informar origem, destino e data de partida", "data": []}
            
            # Construir parâmetros para a busca usando SDK
            search_params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults,
                'currencyCode': currency,
                'max': max_results
            }
            
            # Adicionar data de retorno se fornecida
            if return_date:
                search_params['returnDate'] = return_date
            
            # Realizar a busca com o SDK
            response = self.client.shopping.flight_offers_search.get(**search_params)
            
            # Processar os resultados
            if hasattr(response, 'data'):
                flights_data = response.data
                logger.info(f"Busca bem-sucedida: {len(flights_data)} voos encontrados")
                
                # Adicionar links de compra e formatar dados
                for flight in flights_data:
                    if 'purchaseLinks' not in flight:
                        flight['purchaseLinks'] = self._generate_purchase_links(flight, params)
                
                result = {
                    "data": flights_data,
                    "dictionaries": response.dictionaries if hasattr(response, 'dictionaries') else None,
                    "meta": response.meta if hasattr(response, 'meta') else None
                }
                
                return result
            else:
                logger.warning("Resultado da busca não contém dados")
                return {"error": "Nenhum resultado encontrado", "data": []}
                
        except ResponseError as error:
            # Tratar erros específicos da API Amadeus
            error_response = error.response
            status_code = error_response.status_code
            
            try:
                error_data = error_response.data
                errors = error_data.get('errors', [])
                error_messages = [e.get('title', '') for e in errors]
                error_details = [e.get('detail', '') for e in errors]
                
                logger.error(f"Erro na API Amadeus ({status_code}): {error_messages}")
                
                if status_code == 401:
                    return {"error": "Erro de autenticação com a API Amadeus", "data": []}
                elif status_code == 400:
                    detailed_error = ", ".join(error_details) if error_details else ", ".join(error_messages)
                    return {"error": f"Parâmetros inválidos: {detailed_error}", "data": []}
                else:
                    return {"error": f"Erro na API Amadeus: {', '.join(error_messages)}", "data": []}
            
            except Exception as e:
                logger.error(f"Erro ao processar resposta de erro: {str(e)}")
                return {"error": f"Erro na API Amadeus: {status_code}", "data": []}
        
        except Exception as e:
            logger.error(f"Erro ao buscar voos: {str(e)}")
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
        Busca hotéis baseado nos parâmetros fornecidos usando o SDK
        
        Params:
        - cityCode: código da cidade (exemplo: "PAR" para Paris)
        - radius: raio em KM (opcional)
        - radiusUnit: unidade do raio (KM ou MILE, opcional)
        """
        logger.info(f"Buscando hotéis com Amadeus SDK: {params}")
        
        if not self.client:
            logger.error("Cliente Amadeus SDK não inicializado")
            return {"error": "Cliente Amadeus não inicializado", "data": []}
            
        try:
            # Extrair parâmetros da requisição
            city_code = params.get('cityCode')
            
            if not city_code:
                logger.error("Parâmetro cityCode obrigatório não fornecido")
                return {"error": "Parâmetro cityCode é obrigatório", "data": []}
            
            # Construir parâmetros para a API
            sdk_params = {
                'cityCode': city_code
            }
            
            # Adicionar parâmetros opcionais
            if 'radius' in params:
                sdk_params['radius'] = params['radius']
            
            if 'radiusUnit' in params:
                sdk_params['radiusUnit'] = params['radiusUnit']
            
            # Realizar a busca com o SDK
            response = self.client.reference_data.locations.hotels.by_city.get(**sdk_params)
            
            # Processar os resultados
            if hasattr(response, 'data'):
                hotels_data = response.data
                logger.info(f"Busca bem-sucedida: {len(hotels_data)} hotéis encontrados")
                
                result = {
                    "data": hotels_data,
                    "meta": response.meta if hasattr(response, 'meta') else None
                }
                
                return result
            else:
                logger.warning("Resultado da busca não contém dados")
                return {"error": "Nenhum hotel encontrado", "data": []}
                
        except ResponseError as error:
            # Tratar erros específicos da API Amadeus
            error_response = error.response
            status_code = error_response.status_code
            
            try:
                error_data = error_response.data
                errors = error_data.get('errors', [])
                error_messages = [e.get('title', '') for e in errors]
                
                logger.error(f"Erro na API Amadeus ({status_code}): {error_messages}")
                
                return {"error": f"Erro na API Amadeus: {', '.join(error_messages)}", "data": []}
            
            except Exception as e:
                logger.error(f"Erro ao processar resposta de erro: {str(e)}")
                return {"error": f"Erro na API Amadeus: {status_code}", "data": []}
        
        except Exception as e:
            logger.error(f"Erro ao buscar hotéis: {str(e)}")
            return {"error": f"Erro ao buscar hotéis: {str(e)}", "data": []}
    
    def search_hotel_offers(self, params):
        """
        Busca ofertas de hotéis baseado nos parâmetros fornecidos usando o SDK
        
        Params:
        - hotelIds: lista de IDs de hotéis separados por vírgula
        - adults: número de adultos (default: 1)
        - checkInDate: data de check-in (formato YYYY-MM-DD)
        - checkOutDate: data de check-out (formato YYYY-MM-DD)
        - currency: moeda (default: "BRL")
        """
        logger.info(f"Buscando ofertas de hotéis com Amadeus SDK: {params}")
        
        if not self.client:
            logger.error("Cliente Amadeus SDK não inicializado")
            return {"error": "Cliente Amadeus não inicializado", "data": []}
            
        try:
            # Extrair parâmetros da requisição
            hotel_ids = params.get('hotelIds')
            adults = params.get('adults', 1)
            check_in_date = params.get('checkInDate')
            check_out_date = params.get('checkOutDate')
            currency = params.get('currency', 'BRL')
            
            # Verificar parâmetros obrigatórios
            if not hotel_ids:
                logger.error("Parâmetro hotelIds obrigatório não fornecido")
                return {"error": "Parâmetro hotelIds é obrigatório", "data": []}
                
            if not check_in_date or not check_out_date:
                logger.error("Parâmetros de data obrigatórios não fornecidos")
                return {"error": "Parâmetros checkInDate e checkOutDate são obrigatórios", "data": []}
            
            # Construir parâmetros para a API
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
            
            # Realizar a busca com o SDK
            response = self.client.shopping.hotel_offers.get(**sdk_params)
            
            # Processar os resultados
            if hasattr(response, 'data'):
                offers_data = response.data
                logger.info(f"Busca bem-sucedida: {len(offers_data)} ofertas de hotéis encontradas")
                
                result = {
                    "data": offers_data,
                    "meta": response.meta if hasattr(response, 'meta') else None
                }
                
                return result
            else:
                logger.warning("Resultado da busca não contém dados")
                return {"error": "Nenhuma oferta de hotel encontrada", "data": []}
                
        except ResponseError as error:
            # Tratar erros específicos da API Amadeus
            error_response = error.response
            status_code = error_response.status_code
            
            try:
                error_data = error_response.data
                errors = error_data.get('errors', [])
                error_messages = [e.get('title', '') for e in errors]
                
                logger.error(f"Erro na API Amadeus ({status_code}): {error_messages}")
                
                return {"error": f"Erro na API Amadeus: {', '.join(error_messages)}", "data": []}
            
            except Exception as e:
                logger.error(f"Erro ao processar resposta de erro: {str(e)}")
                return {"error": f"Erro na API Amadeus: {status_code}", "data": []}
        
        except Exception as e:
            logger.error(f"Erro ao buscar ofertas de hotéis: {str(e)}")
            return {"error": f"Erro ao buscar ofertas de hotéis: {str(e)}", "data": []}
    
    def search_best_prices(self, params):
        """
        Busca melhores preços para diferentes datas usando o SDK
        
        Params:
        - originLocationCode: código IATA da origem
        - destinationLocationCode: código IATA do destino
        - departureDate: data inicial para busca (formato YYYY-MM-DD)
        - returnDate: data final para busca (opcional, formato YYYY-MM-DD)
        - adults: número de adultos (default: 1)
        - currencyCode: moeda (default: "BRL")
        - max_dates_to_check: número máximo de datas a verificar (default: 5)
        """
        logger.info(f"Buscando melhores preços com Amadeus SDK: {params}")
        
        if not self.client:
            logger.error("Cliente Amadeus SDK não inicializado")
            return {"error": "Cliente Amadeus não inicializado", "data": []}
        
        try:
            # Extrair parâmetros principais da requisição
            origin = params.get('originLocationCode')
            destination = params.get('destinationLocationCode')
            departure_date = params.get('departureDate')
            return_date = params.get('returnDate')
            adults = int(params.get('adults', 1))
            currency = params.get('currencyCode', 'BRL')
            max_dates = int(params.get('max_dates_to_check', 5))
            
            # Verificar parâmetros obrigatórios
            if not origin or not destination or not departure_date:
                logger.error("Parâmetros obrigatórios faltando")
                return {"error": "Parâmetros incompletos: é necessário informar origem, destino e data de partida", "data": []}
            
            # Calcular intervalo de datas a verificar
            start_date = datetime.strptime(departure_date, "%Y-%m-%d")
            if return_date:
                end_date = datetime.strptime(return_date, "%Y-%m-%d")
            else:
                end_date = start_date + timedelta(days=30)  # Buscar preços para 30 dias se não especificado
            
            # Limitar o número de datas para não sobrecarregar a API
            total_days = (end_date - start_date).days + 1
            
            # Construir lista de datas para verificar, limitado pelo max_dates
            if total_days <= max_dates:
                # Se o intervalo for menor que o máximo, verificar todas as datas
                delta = end_date - start_date
                dates_to_check = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]
            else:
                # Caso contrário, distribuir as datas ao longo do intervalo
                step = total_days / max_dates
                dates_to_check = []
                for i in range(max_dates):
                    day = int(i * step)
                    date = start_date + timedelta(days=day)
                    dates_to_check.append(date.strftime("%Y-%m-%d"))
                    
                # Garantir que as datas de início e fim estejam incluídas
                if departure_date not in dates_to_check:
                    dates_to_check.append(departure_date)
                if return_date and return_date not in dates_to_check:
                    dates_to_check.append(return_date)
                
                # Ordenar datas cronologicamente
                dates_to_check.sort()
            
            # Buscar preços para cada data
            best_prices = []
            logger.info(f"Verificando preços para {len(dates_to_check)} datas")
            
            for date in dates_to_check:
                # Para cada data, buscar a oferta de voo mais barata
                logger.info(f"Buscando preço para {date}")
                flight_params = {
                    'originLocationCode': origin,
                    'destinationLocationCode': destination,
                    'departureDate': date,
                    'adults': adults,
                    'currencyCode': currency,
                    'max': 1  # Apenas o melhor preço
                }
                
                try:
                    # Realizar a busca de voo para esta data específica
                    response = self.client.shopping.flight_offers_search.get(**flight_params)
                    
                    if hasattr(response, 'data') and response.data:
                        flight = response.data[0]  # Pegar apenas o primeiro resultado (mais barato)
                        
                        # Extrair preço da oferta
                        price = float(flight['price']['total'])
                        
                        # Construir objeto com informações do voo
                        flight_info = {
                            'date': date,
                            'price': price,
                            'airline': '',
                            'flight_number': '',
                            'departure_time': '',
                            'arrival_time': '',
                            'duration': '',
                            'origin': origin,
                            'destination': destination,
                            'origin_info': None,
                            'destination_info': None,
                            'provider': 'Amadeus API',
                            'details': flight
                        }
                        
                        # Extrair detalhes adicionais do voo
                        if 'itineraries' in flight and flight['itineraries']:
                            itinerary = flight['itineraries'][0]
                            
                            # Extrair duração do voo
                            if 'duration' in itinerary:
                                duration_str = itinerary['duration']
                                
                                # Converter formato PT10H30M para 10h 30min
                                hours_match = duration_str.find('H')
                                minutes_match = duration_str.find('M')
                                
                                if hours_match > 0:
                                    hours = duration_str[2:hours_match]
                                    minutes = '0'
                                    if minutes_match > 0:
                                        minutes = duration_str[hours_match+1:minutes_match]
                                    flight_info['duration'] = f"{hours}h {minutes}min"
                            
                            # Extrair informações dos segmentos do voo
                            if 'segments' in itinerary and itinerary['segments']:
                                segment = itinerary['segments'][0]
                                
                                if 'carrierCode' in segment:
                                    flight_info['airline'] = segment['carrierCode']
                                
                                if 'number' in segment:
                                    flight_info['flight_number'] = segment['number']
                                
                                if 'departure' in segment and 'at' in segment['departure']:
                                    departure_datetime = segment['departure']['at']
                                    # Extrair hora da data completa (formato: 2023-10-25T10:30:00)
                                    if 'T' in departure_datetime:
                                        departure_time = departure_datetime.split('T')[1][:5]
                                        flight_info['departure_time'] = departure_time
                                
                                if 'arrival' in segment and 'at' in segment['arrival']:
                                    arrival_datetime = segment['arrival']['at']
                                    # Extrair hora da data completa
                                    if 'T' in arrival_datetime:
                                        arrival_time = arrival_datetime.split('T')[1][:5]
                                        flight_info['arrival_time'] = arrival_time
                        
                        # Adicionar links de compra
                        flight_info['purchaseLinks'] = self._generate_purchase_links(flight, flight_params)
                        
                        # Adicionar à lista de melhores preços
                        best_prices.append(flight_info)
                        logger.info(f"Preço encontrado para {date}: {price} {currency}")
                    else:
                        logger.warning(f"Nenhuma oferta encontrada para {date}")
                
                except ResponseError as error:
                    logger.warning(f"Erro ao buscar preço para {date}: {error}")
                    continue
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar resultado para {date}: {str(e)}")
                    continue
            
            # Ordenar por preço
            if best_prices:
                best_prices.sort(key=lambda x: x['price'])
                
                # Adicionar informações de aeroportos (isto seria implementado separadamente)
                # Aqui poderíamos buscar informações dos aeroportos e adicionar aos resultados
                
                # Construir resultado final
                result = {
                    "origin": origin,
                    "destination": destination,
                    "currency": currency,
                    "best_prices": best_prices
                }
                
                return result
            else:
                logger.warning("Nenhum preço encontrado para as datas solicitadas")
                return {"error": "Não foi possível encontrar preços para as datas solicitadas", "data": []}
        
        except Exception as e:
            logger.error(f"Erro ao buscar melhores preços: {str(e)}")
            return {"error": f"Erro ao buscar melhores preços: {str(e)}", "data": []}
            
    def _get_airport_info(self, airport_codes):
        """
        Busca informações detalhadas sobre aeroportos pelo código IATA
        """
        if not self.client:
            logger.error("Cliente Amadeus SDK não inicializado")
            return {}
            
        airport_info = {}
        
        for code in airport_codes:
            try:
                # Buscar informações do aeroporto usando o SDK
                response = self.client.reference_data.locations.get(
                    keyword=code,
                    subType='AIRPORT'
                )
                
                if hasattr(response, 'data') and response.data:
                    for location in response.data:
                        if location['iataCode'] == code:
                            airport_info[code] = {
                                'code': code,
                                'name': location.get('name', ''),
                                'city': location.get('address', {}).get('cityName', ''),
                                'country': location.get('address', {}).get('countryName', '')
                            }
                            break
            except Exception as e:
                logger.warning(f"Não foi possível obter informações para o aeroporto {code}: {str(e)}")
                # Adicionar informações básicas para não interromper o fluxo
                airport_info[code] = {
                    'code': code,
                    'name': code,
                    'city': '',
                    'country': ''
                }
                
        return airport_info
        
    def test_connection(self):
        """
        Testa a conexão com a API Amadeus
        Retorna um diagnóstico detalhado
        """
        if not self.client:
            logger.error("Cliente Amadeus SDK não inicializado")
            return {
                "success": False,
                "error": "Cliente Amadeus não inicializado. Verifique as credenciais."
            }
            
        try:
            # Testar conexão com uma API simples
            response = self.client.reference_data.locations.get(
                keyword='LON',
                subType='CITY'
            )
            
            if hasattr(response, 'data'):
                logger.info("Conexão com Amadeus API bem-sucedida")
                return {
                    "success": True,
                    "message": "Conexão com Amadeus API bem-sucedida"
                }
            else:
                logger.error("Resposta da API não contém dados")
                return {
                    "success": False,
                    "error": "Resposta da API não contém dados"
                }
                
        except ResponseError as error:
            logger.error(f"Erro na API Amadeus: {error}")
            return {
                "success": False,
                "error": f"Erro na API Amadeus: {error}"
            }
            
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {str(e)}")
            return {
                "success": False,
                "error": f"Erro ao testar conexão: {str(e)}"
            }
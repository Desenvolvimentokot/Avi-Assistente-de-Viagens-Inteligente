
import os
import requests
import logging
import json
from datetime import datetime

class SkyscannerService:
    def __init__(self):
        # Credenciais da API Skyscanner
        self.account_sid = "IRHRCerDjfGB6142175YvFpgXdE5wSp6P1"
        self.auth_token = "W_TRSD7aw.iBVsC9HGQvAENiDfihdHLC"
        self.base_url = "https://partners.api.skyscanner.net/apiservices"
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
    
    def search_flights(self, params):
        """
        Busca voos usando a API do Skyscanner
        
        Params:
        - origin: código IATA da origem (exemplo: "GRU")
        - destination: código IATA do destino (exemplo: "MIA")
        - departure_date: data de partida (formato YYYY-MM-DD)
        - return_date: data de retorno (opcional, formato YYYY-MM-DD)
        - adults: número de adultos (default: 1)
        - currency: moeda (default: "BRL")
        """
        try:
            self.logger.info(f"Buscando voos com parâmetros: {params}")
            
            # Formatação dos parâmetros conforme necessário pela API Skyscanner
            origin = params.get('origin')
            destination = params.get('destination')
            departure_date = params.get('departure_date')
            return_date = params.get('return_date')
            adults = params.get('adults', 1)
            currency = params.get('currency', 'BRL')
            
            # URL para a busca de voos (endpoint específico do Skyscanner)
            url = f"{self.base_url}/v3/flights/live/search/create"
            
            # Cabeçalhos de autenticação
            headers = {
                "x-api-key": self.account_sid,
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Montar o payload para a requisição
            payload = {
                "query": {
                    "market": "BR",
                    "locale": "pt-BR",
                    "currency": currency,
                    "queryLegs": [
                        {
                            "originPlaceId": {"iata": origin},
                            "destinationPlaceId": {"iata": destination},
                            "date": {"year": int(departure_date[:4]), 
                                    "month": int(departure_date[5:7]), 
                                    "day": int(departure_date[8:10])}
                        }
                    ],
                    "adults": adults,
                    "childrenAges": []
                }
            }
            
            # Adicionar trecho de retorno, se aplicável
            if return_date:
                return_leg = {
                    "originPlaceId": {"iata": destination},
                    "destinationPlaceId": {"iata": origin},
                    "date": {"year": int(return_date[:4]), 
                            "month": int(return_date[5:7]), 
                            "day": int(return_date[8:10])}
                }
                payload["query"]["queryLegs"].append(return_leg)
            
            # Fazer a requisição à API
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Processar e retornar os resultados
            result = response.json()
            
            # Formatação do resultado para o formato padronizado da aplicação
            return self._format_flights_response(result)
        
        except Exception as e:
            self.logger.error(f"Erro ao buscar voos via Skyscanner: {str(e)}")
            return {"error": f"Erro na busca de voos: {str(e)}"}
    
    def _format_flights_response(self, api_response):
        """
        Formata a resposta da API do Skyscanner para o formato padronizado da aplicação
        """
        try:
            formatted_flights = []
            
            # Extrair itinerários e preços da resposta da API
            if 'content' in api_response and 'results' in api_response['content']:
                itineraries = api_response['content'].get('itineraries', {})
                legs = api_response['content'].get('legs', {})
                segments = api_response['content'].get('segments', {})
                places = api_response['content'].get('places', {})
                carriers = api_response['content'].get('carriers', {})
                
                # Processar cada itinerário
                for itinerary_id, itinerary in itineraries.items():
                    price_options = itinerary.get('priceOptions', [])
                    if price_options:
                        # Usar o preço mais baixo disponível
                        price_option = price_options[0]
                        price = price_option.get('price', {}).get('amount', 0)
                        currency = price_option.get('price', {}).get('unit', 'BRL')
                        
                        # Obter informações sobre os trechos (legs)
                        leg_ids = itinerary.get('legIds', [])
                        if leg_ids:
                            leg_id = leg_ids[0]
                            leg = legs.get(leg_id, {})
                            
                            # Origem e destino
                            origin_place_id = leg.get('originPlaceId')
                            destination_place_id = leg.get('destinationPlaceId')
                            
                            origin = places.get(origin_place_id, {}).get('iata')
                            destination = places.get(destination_place_id, {}).get('iata')
                            
                            # Horários
                            departure_time = leg.get('departureDateTime', {})
                            departure_str = f"{departure_time.get('year')}-{departure_time.get('month'):02d}-{departure_time.get('day'):02d}T{departure_time.get('hour'):02d}:{departure_time.get('minute'):02d}:00"
                            
                            arrival_time = leg.get('arrivalDateTime', {})
                            arrival_str = f"{arrival_time.get('year')}-{arrival_time.get('month'):02d}-{arrival_time.get('day'):02d}T{arrival_time.get('hour'):02d}:{arrival_time.get('minute'):02d}:00"
                            
                            # Duração em minutos
                            duration = leg.get('durationInMinutes', 0)
                            
                            # Informações da companhia aérea
                            segment_ids = leg.get('segmentIds', [])
                            airlines = []
                            for segment_id in segment_ids:
                                segment = segments.get(segment_id, {})
                                carrier_id = segment.get('marketingCarrierId')
                                if carrier_id and carrier_id in carriers:
                                    airlines.append(carriers[carrier_id].get('name', ''))
                            
                            airline = airlines[0] if airlines else 'Desconhecida'
                            
                            # Gerar link de afiliado do Skyscanner
                            affiliate_link = self._generate_affiliate_link(origin, destination, departure_str[:10], arrival_str[:10])
                            
                            # Formatar o voo
                            flight = {
                                "id": itinerary_id,
                                "price": f"{price}",
                                "currency": currency,
                                "departure": {
                                    "airport": origin,
                                    "time": departure_str
                                },
                                "arrival": {
                                    "airport": destination,
                                    "time": arrival_str
                                },
                                "duration": f"PT{duration}M",
                                "segments": len(segment_ids),
                                "airline": airline,
                                "affiliate_link": affiliate_link
                            }
                            
                            formatted_flights.append(flight)
            
            return {"flights": formatted_flights}
        
        except Exception as e:
            self.logger.error(f"Erro ao formatar resposta da API Skyscanner: {str(e)}")
            return {"error": f"Erro ao processar resultados: {str(e)}"}
    
    def _generate_affiliate_link(self, origin, destination, departure_date, return_date=None):
        """
        Gera um link de afiliado do Skyscanner
        """
        # Base do link de afiliado do Skyscanner
        base_url = "https://www.skyscanner.com.br/transporte/voos"
        
        # Formatação do link
        if return_date:
            link = f"{base_url}/{origin}/{destination}/{departure_date}/{return_date}/?adults=1&ref=IRHRCerDjfGB6142175YvFpgXdE5wSp6P1"
        else:
            link = f"{base_url}/{origin}/{destination}/{departure_date}/?adults=1&ref=IRHRCerDjfGB6142175YvFpgXdE5wSp6P1"
        
        return link
    
    def get_best_price_options(self, origin, destination, date_range_start, date_range_end):
        """
        Obtém as melhores opções de preço para um intervalo de datas
        
        Params:
        - origin: código IATA da origem
        - destination: código IATA do destino
        - date_range_start: data inicial do intervalo (YYYY-MM-DD)
        - date_range_end: data final do intervalo (YYYY-MM-DD)
        """
        try:
            self.logger.info(f"Buscando melhores preços para {origin} → {destination} entre {date_range_start} e {date_range_end}")
            
            # URL para a busca de preços por datas (endpoint específico do Skyscanner)
            url = f"{self.base_url}/v3/flights/indicative/browse/daily/v2"
            
            # Cabeçalhos de autenticação
            headers = {
                "x-api-key": self.account_sid,
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Montar o payload para a requisição
            payload = {
                "query": {
                    "market": "BR",
                    "locale": "pt-BR",
                    "currency": "BRL",
                    "queryLegs": [
                        {
                            "originPlace": {
                                "queryPlace": {
                                    "iata": origin
                                }
                            },
                            "destinationPlace": {
                                "queryPlace": {
                                    "iata": destination
                                }
                            },
                            "dateRange": {
                                "startDate": {
                                    "year": int(date_range_start[:4]),
                                    "month": int(date_range_start[5:7]),
                                    "day": int(date_range_start[8:10])
                                },
                                "endDate": {
                                    "year": int(date_range_end[:4]),
                                    "month": int(date_range_end[5:7]),
                                    "day": int(date_range_end[8:10])
                                }
                            }
                        }
                    ],
                    "adults": 1,
                    "childrenAges": []
                }
            }
            
            # Fazer a requisição à API
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Processar e retornar os resultados
            result = response.json()
            
            # Formatação do resultado para o formato padronizado da aplicação
            return self._format_best_prices_response(result, origin, destination)
        
        except Exception as e:
            self.logger.error(f"Erro ao buscar melhores preços via Skyscanner: {str(e)}")
            return {"error": f"Erro na busca de melhores preços: {str(e)}"}
    
    def _format_best_prices_response(self, api_response, origin, destination):
        """
        Formata a resposta da API de melhores preços do Skyscanner
        """
        try:
            best_prices = []
            
            # Extrair informações de preços por data
            if 'content' in api_response and 'quotes' in api_response['content']:
                quotes = api_response['content']['quotes']
                
                for quote in quotes:
                    price = quote.get('price', {}).get('amount')
                    departure_date = quote.get('outboundLeg', {}).get('departureDateTime', {})
                    
                    if price and departure_date:
                        date_str = f"{departure_date.get('year')}-{departure_date.get('month'):02d}-{departure_date.get('day'):02d}"
                        
                        # Gerar link de afiliado
                        affiliate_link = self._generate_affiliate_link(origin, destination, date_str)
                        
                        best_prices.append({
                            "date": date_str,
                            "price": price,
                            "currency": quote.get('price', {}).get('unit', 'BRL'),
                            "affiliate_link": affiliate_link
                        })
            
            # Ordenar por preço (do mais barato para o mais caro)
            best_prices.sort(key=lambda x: x['price'])
            
            return {"best_prices": best_prices}
        
        except Exception as e:
            self.logger.error(f"Erro ao formatar resposta de melhores preços: {str(e)}")
            return {"error": f"Erro ao processar resultados de melhores preços: {str(e)}"}

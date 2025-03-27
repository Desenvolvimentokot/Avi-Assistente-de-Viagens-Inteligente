
import os
import logging
import requests
import json
from datetime import datetime, timedelta

class SkyscannerService:
    def __init__(self):
        self.account_sid = os.environ.get('SKYSCANNER_ACCOUNT_SID', 'IRHRCerDjfGB6142175YvFpgXdE5wSp6P1')
        self.auth_token = os.environ.get('SKYSCANNER_AUTH_TOKEN', 'W_TRSD7aw.iBVsC9HGQvAENiDfihdHLC')
        self.base_url = 'https://partners.api.skyscanner.net/apiservices'
        self.headers = {
            'x-api-key': self.account_sid,
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
        # Log configuration
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def search_flights(self, params):
        """
        Busca voos no Skyscanner com base nos parâmetros fornecidos
        
        Parâmetros:
        - params: dicionário com parâmetros como:
          - origin: código IATA do aeroporto de origem
          - destination: código IATA do aeroporto de destino
          - departureDate: data de partida (YYYY-MM-DD)
          - returnDate: data de retorno (YYYY-MM-DD), opcional
          - adults: número de adultos (padrão: 1)
          - children: número de crianças (padrão: 0)
          - infants: número de bebês (padrão: 0)
          - cabinClass: classe da cabine (economy, premiumeconomy, business, first)
          - currency: moeda (padrão: BRL)
        """
        try:
            # Construir URL para busca
            url = f"{self.base_url}/v3/flights/live/search/create"
            
            # Preparar payload da requisição
            payload = self._build_search_payload(params)
            
            # Log do payload
            self.logger.info(f"Enviando requisição para Skyscanner: {json.dumps(payload)[:200]}...")
            
            # Fazer requisição à API
            response = requests.post(url, headers=self.headers, json=payload)
            
            # Verificar resposta
            if response.status_code == 200 or response.status_code == 201:
                session_token = response.json().get('sessionToken')
                # Buscar resultados usando o token de sessão
                return self._poll_search_results(session_token)
            else:
                self.logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
                return {"error": f"Erro na requisição: {response.status_code}", "details": response.text}
                
        except Exception as e:
            self.logger.exception(f"Erro ao buscar voos: {str(e)}")
            return {"error": f"Erro ao buscar voos: {str(e)}"}
    
    def _build_search_payload(self, params):
        """Constrói o payload para a requisição de busca"""
        origin = params.get('origin')
        destination = params.get('destination')
        departure_date = params.get('departureDate')
        return_date = params.get('returnDate')
        adults = int(params.get('adults', 1))
        children = int(params.get('children', 0))
        infants = int(params.get('infants', 0))
        cabin_class = params.get('cabinClass', 'economy')
        currency = params.get('currency', 'BRL')
        
        # Validar parâmetros obrigatórios
        if not all([origin, destination, departure_date]):
            raise ValueError("Parâmetros obrigatórios: origin, destination, departureDate")
        
        # Construir payload
        payload = {
            "query": {
                "market": "BR",
                "locale": "pt-BR",
                "currency": currency,
                "queryLegs": [
                    {
                        "originPlaceId": {"iata": origin},
                        "destinationPlaceId": {"iata": destination},
                        "date": {
                            "year": int(departure_date.split('-')[0]),
                            "month": int(departure_date.split('-')[1]),
                            "day": int(departure_date.split('-')[2])
                        }
                    }
                ],
                "adults": adults,
                "childrenAges": [10] * children,  # Idade padrão para crianças
                "cabinClass": cabin_class.upper()
            }
        }
        
        # Adicionar voo de volta se houver
        if return_date:
            payload["query"]["queryLegs"].append({
                "originPlaceId": {"iata": destination},
                "destinationPlaceId": {"iata": origin},
                "date": {
                    "year": int(return_date.split('-')[0]),
                    "month": int(return_date.split('-')[1]),
                    "day": int(return_date.split('-')[2])
                }
            })
        
        return payload
    
    def _poll_search_results(self, session_token, max_attempts=5):
        """Busca resultados de uma sessão de busca"""
        url = f"{self.base_url}/v3/flights/live/search/poll/{session_token}"
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Buscando resultados (tentativa {attempt+1}/{max_attempts})...")
                response = requests.post(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    
                    if status == 'COMPLETED':
                        self.logger.info("Busca concluída com sucesso")
                        return self._process_search_results(data)
                    elif status == 'FAILED':
                        self.logger.error(f"Falha na busca: {data}")
                        return {"error": "Falha na busca de voos", "details": data}
                    
                    # Se ainda não concluiu, espera e tenta novamente
                    import time
                    time.sleep(2)
                else:
                    self.logger.error(f"Erro ao buscar resultados: {response.status_code} - {response.text}")
                    return {"error": f"Erro ao buscar resultados: {response.status_code}", "details": response.text}
            
            except Exception as e:
                self.logger.exception(f"Erro ao buscar resultados: {str(e)}")
                return {"error": f"Erro ao buscar resultados: {str(e)}"}
        
        return {"error": f"Tempo excedido ao buscar resultados após {max_attempts} tentativas"}
    
    def _process_search_results(self, data):
        """Processa os resultados da busca"""
        try:
            results = {
                "flights": [],
                "min_price": None,
                "max_price": None,
                "avg_price": None,
                "currency": data.get("query", {}).get("currency", "BRL")
            }
            
            # Obter itinerários
            itineraries = data.get("content", {}).get("results", {}).get("itineraries", {})
            legs = data.get("content", {}).get("results", {}).get("legs", {})
            segments = data.get("content", {}).get("results", {}).get("segments", {})
            places = data.get("content", {}).get("results", {}).get("places", {})
            carriers = data.get("content", {}).get("results", {}).get("carriers", {})
            
            prices = []
            
            # Processar cada itinerário
            for itinerary_id, itinerary in itineraries.items():
                leg_ids = itinerary.get("legIds", [])
                price_options = itinerary.get("pricingOptions", [])
                
                if not price_options:
                    continue
                
                # Pegar a opção de preço mais barata
                best_price_option = min(price_options, key=lambda x: x.get("price", {}).get("amount", float('inf')))
                price = best_price_option.get("price", {}).get("amount")
                price_amount = float(price) if price else 0
                prices.append(price_amount)
                
                # Verificar se há link de afiliado disponível
                deep_link = best_price_option.get("items", [{}])[0].get("deepLink", "")
                deeplink_data = {
                    "agent_name": best_price_option.get("agentIds", ["Unknown"])[0],
                    "url": deep_link
                }
                
                # Processar informações dos legs (voos)
                flight_info = []
                for leg_id in leg_ids:
                    leg = legs.get(leg_id, {})
                    segment_ids = leg.get("segmentIds", [])
                    
                    departure_place_id = leg.get("originPlaceId")
                    arrival_place_id = leg.get("destinationPlaceId")
                    
                    departure_place = places.get(departure_place_id, {}).get("name", "")
                    arrival_place = places.get(arrival_place_id, {}).get("name", "")
                    
                    departure_time = leg.get("departureDateTime", {})
                    arrival_time = leg.get("arrivalDateTime", {})
                    
                    # Formatar datas e horários
                    dep_datetime = f"{departure_time.get('year', 0)}-{departure_time.get('month', 0)}-{departure_time.get('day', 0)}T{departure_time.get('hour', 0)}:{departure_time.get('minute', 0)}:00"
                    arr_datetime = f"{arrival_time.get('year', 0)}-{arrival_time.get('month', 0)}-{arrival_time.get('day', 0)}T{arrival_time.get('hour', 0)}:{arrival_time.get('minute', 0)}:00"
                    
                    # Informações sobre segmentos (escalas)
                    segment_info = []
                    for segment_id in segment_ids:
                        segment = segments.get(segment_id, {})
                        carrier_id = segment.get("marketingCarrierId")
                        carrier_name = carriers.get(carrier_id, {}).get("name", "")
                        flight_number = segment.get("marketingFlightNumber", "")
                        
                        segment_info.append({
                            "carrier": carrier_name,
                            "flight_number": flight_number,
                            "departure": segment.get("departureDateTime"),
                            "arrival": segment.get("arrivalDateTime")
                        })
                    
                    flight_info.append({
                        "departure": {
                            "airport": departure_place,
                            "time": dep_datetime
                        },
                        "arrival": {
                            "airport": arrival_place,
                            "time": arr_datetime
                        },
                        "duration": leg.get("durationInMinutes"),
                        "stops": len(segment_ids) - 1,
                        "segments": segment_info
                    })
                
                # Adicionar informação completa do voo
                results["flights"].append({
                    "id": itinerary_id,
                    "price": price_amount,
                    "currency": results["currency"],
                    "legs": flight_info,
                    "deeplink": deeplink_data
                })
            
            # Calcular estatísticas de preço
            if prices:
                results["min_price"] = min(prices)
                results["max_price"] = max(prices)
                results["avg_price"] = sum(prices) / len(prices)
            
            # Ordenar por preço
            results["flights"] = sorted(results["flights"], key=lambda x: x["price"])
            
            return results
        
        except Exception as e:
            self.logger.exception(f"Erro ao processar resultados: {str(e)}")
            return {"error": f"Erro ao processar resultados: {str(e)}"}
    
    def generate_affiliate_link(self, destination, departure_date=None, return_date=None):
        """
        Gera um link de afiliado para um destino específico
        
        Parâmetros:
        - destination: código IATA do destino ou nome da cidade
        - departure_date: data de partida (opcional)
        - return_date: data de retorno (opcional)
        """
        try:
            # Base do link de afiliado do Skyscanner
            base_url = "https://www.skyscanner.com.br/transport/flights"
            
            # Padrão: origem é o Brasil (para o mercado brasileiro)
            origin = "BR"
            
            # Parâmetros para o link
            params = []
            
            # Adicionar data de ida, se fornecida
            if departure_date:
                # Formatar data como YYMMDD
                try:
                    date_obj = datetime.strptime(departure_date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%y%m%d")
                    params.append(formatted_date)
                except:
                    # Se falhar, não incluir a data
                    params.append("")
            else:
                # Data não especificada
                params.append("")
            
            # Adicionar data de volta, se fornecida
            if return_date:
                try:
                    date_obj = datetime.strptime(return_date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%y%m%d")
                    params.append(formatted_date)
                except:
                    # Se falhar, não incluir a data
                    params.append("")
            
            # Construir URL
            if params:
                param_str = "/".join(params)
                affiliate_url = f"{base_url}/{origin}/{destination}/{param_str}/?preferDirects=false&adults=1"
            else:
                affiliate_url = f"{base_url}/{origin}/{destination}/?preferDirects=false&adults=1"
            
            # Adicionar parâmetro de afiliado
            affiliate_url += f"&associateid={self.account_sid}"
            
            return affiliate_url
            
        except Exception as e:
            self.logger.exception(f"Erro ao gerar link de afiliado: {str(e)}")
            return None
    
    def get_mock_flights(self, params):
        """
        Retorna dados simulados para desenvolvimento e teste
        quando a API não está disponível ou para não consumir créditos
        """
        origin = params.get('origin', 'GRU')
        destination = params.get('destination', 'MIA')
        departure_date = params.get('departureDate', datetime.now().strftime('%Y-%m-%d'))
        currency = params.get('currency', 'BRL')
        
        try:
            # Converter para objeto datetime para manipulação
            dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
            
            # Algumas opções de companhias e preços para simulação
            airlines = [
                {"code": "LA", "name": "LATAM Airlines"},
                {"code": "AA", "name": "American Airlines"},
                {"code": "G3", "name": "Gol Linhas Aéreas"},
                {"code": "AD", "name": "Azul Linhas Aéreas"},
                {"code": "DL", "name": "Delta Air Lines"}
            ]
            
            # Gerar preços simulados
            base_price = 3500 if destination == "MIA" else 4200
            price_variations = [0.85, 0.9, 1.0, 1.05, 1.15]
            
            flights = []
            for i in range(5):
                # Selecionar companhia aleatória
                import random
                airline = airlines[i % len(airlines)]
                
                # Calcular preço com variação
                price = base_price * price_variations[i]
                
                # Gerar horários simulados
                departure_hours = [8, 10, 14, 18, 22]
                departure_hour = departure_hours[i]
                flight_duration = 480 if destination == "MIA" else 720  # 8h ou 12h em minutos
                
                # Calcular chegada
                arr_datetime = dep_date + timedelta(minutes=flight_duration)
                
                # Formatar datas
                dep_formatted = f"{dep_date.year}-{dep_date.month:02d}-{dep_date.day:02d}T{departure_hour:02d}:00:00"
                arr_formatted = arr_datetime.strftime('%Y-%m-%dT%H:%M:00')
                
                # Gerar link de afiliado falso
                deeplink = self.generate_affiliate_link(destination, departure_date)
                
                # Adicionar voo
                flights.append({
                    "id": f"flight_{i+1}",
                    "price": round(price, 2),
                    "currency": currency,
                    "legs": [
                        {
                            "departure": {
                                "airport": origin,
                                "time": dep_formatted
                            },
                            "arrival": {
                                "airport": destination,
                                "time": arr_formatted
                            },
                            "duration": flight_duration,
                            "stops": i % 2,  # Alternar entre direto e com escala
                            "segments": [
                                {
                                    "carrier": airline["name"],
                                    "flight_number": f"{airline['code']}1{i+1}23",
                                    "departure": dep_formatted,
                                    "arrival": arr_formatted
                                }
                            ]
                        }
                    ],
                    "deeplink": {
                        "agent_name": f"Agência {i+1}",
                        "url": deeplink
                    }
                })
            
            # Calcular estatísticas
            prices = [f["price"] for f in flights]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            
            # Ordenar por preço
            flights = sorted(flights, key=lambda x: x["price"])
            
            return {
                "flights": flights,
                "min_price": min_price,
                "max_price": max_price,
                "avg_price": avg_price,
                "currency": currency,
                "_mock": True  # Indicar que são dados simulados
            }
            
        except Exception as e:
            self.logger.exception(f"Erro ao gerar dados simulados: {str(e)}")
            return {"error": f"Erro ao gerar dados simulados: {str(e)}"}

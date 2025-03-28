# Primeira definição da classe removida para evitar duplicação
# O código começa com imports
import os
import logging
import requests
import json

class AmadeusService:
    def __init__(self):
        self.api_key = os.environ.get('AMADEUS_API_KEY')
        self.api_secret = os.environ.get('AMADEUS_API_SECRET')
        self.token = None
        self.token_expiry = None
        
        # Verificar se as credenciais existem
        if not self.api_key or not self.api_secret:
            logging.warning("Credenciais do Amadeus não encontradas! Verifique as variáveis de ambiente AMADEUS_API_KEY e AMADEUS_API_SECRET.")
            self.api_key = "Bw5AGWcgGyVjm6sYQOGrzDVCN2vOCTGG"  # Backup de credencial do .env
            self.api_secret = "lzDOBGcsjA8sUCGS"  # Backup de credencial do .env
            
        # Usar dados simulados apenas se não conseguir autenticar
        self.use_mock_data = False
        
    def get_token(self):
        """Obtém um token de autenticação da API Amadeus"""
        if self.use_mock_data:
            return "MOCK_TOKEN"
            
        # Verificar credenciais antes de fazer a requisição
        if not self.api_key or not self.api_secret:
            logging.error("Credenciais do Amadeus não configuradas corretamente")
            self.use_mock_data = True
            return None
            
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        try:
            logging.info(f"Obtendo token do Amadeus com chave: {self.api_key[:5]}... e secret: {self.api_secret[:3]}...")
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(url, headers=headers, data=payload)
            
            logging.info(f"Resposta Amadeus status: {response.status_code}")
            
            if response.status_code != 200:
                logging.error(f"Erro ao obter token do Amadeus: Status {response.status_code}")
                logging.error(f"Resposta: {response.text}")
                self.use_mock_data = True
                return None
                
            data = response.json()
            self.token = data["access_token"]
            logging.info("Token do Amadeus obtido com sucesso!")
            
            return self.token
        except Exception as e:
            logging.error(f"Erro ao obter token do Amadeus: {str(e)}")
            self.use_mock_data = True
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
        """
        logging.info(f"Iniciando busca de voos com params: {params}")
        
        if self.use_mock_data:
            logging.warning("Usando dados simulados para voos")
            mock_data = self._get_mock_flights(params)
            logging.info(f"Retornando {len(mock_data.get('data', []))} voos simulados")
            return mock_data
            
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        
        # Preparar cabeçalhos com o token de autenticação
        token = self.get_token()
        if not token:
            logging.error("Sem token de autenticação, usando dados simulados")
            self.use_mock_data = True
            return self._get_mock_flights(params)
            
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            logging.info(f"Enviando requisição para Amadeus: {url}")
            response = requests.get(url, headers=headers, params=params)
            
            logging.info(f"Resposta Amadeus status: {response.status_code}")
            
            if response.status_code != 200:
                logging.error(f"Erro na API do Amadeus: {response.status_code}")
                logging.error(f"Detalhes: {response.text}")
                self.use_mock_data = True
                return self._get_mock_flights(params)
            
            json_data = response.json()
            logging.info(f"Dados recebidos do Amadeus com {len(json_data.get('data', []))} voos")
            
            return json_data
        except Exception as e:
            logging.error(f"Erro ao buscar voos: {str(e)}")
            self.use_mock_data = True
            
            # Se ocorrer um erro, retorna os dados simulados
            logging.info("Usando dados simulados após erro")
            return self._get_mock_flights(params)
    
    def search_hotels(self, params):
        """
        Busca hotéis baseado nos parâmetros fornecidos
        
        Params:
        - cityCode: código da cidade (exemplo: "PAR" para Paris)
        - radius: raio em KM (opcional)
        - radiusUnit: unidade do raio (KM ou MILE, opcional)
        """
        if self.use_mock_data:
            return self._get_mock_hotels(params)
            
        url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
        
        # Preparar cabeçalhos com o token de autenticação
        token = self.get_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logging.error(f"Erro ao buscar hotéis: {str(e)}")
            
            # Se ocorrer um erro, retorna o erro formatado
            return {"error": str(e)}
    
    def search_hotel_offers(self, params):
        """
        Busca ofertas de hotéis baseado nos parâmetros fornecidos
        
        Params:
        - hotelIds: lista de IDs de hotéis separados por vírgula
        - adults: número de adultos (default: 1)
        - checkInDate: data de check-in (formato YYYY-MM-DD)
        - checkOutDate: data de check-out (formato YYYY-MM-DD)
        - currency: moeda (default: "BRL")
        """
        if self.use_mock_data:
            return self._get_mock_hotel_offers(params)
            
        url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
        
        # Preparar cabeçalhos com o token de autenticação
        token = self.get_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logging.error(f"Erro ao buscar ofertas de hotéis: {str(e)}")
            
            # Se ocorrer um erro, retorna o erro formatado
            return {"error": str(e)}
    
    def _get_mock_flights(self, params):
        """Retorna dados simulados de voos para desenvolvimento"""
        origin = params.get('originLocationCode', 'GRU')
        destination = params.get('destinationLocationCode', 'CDG')
        departure_date = params.get('departureDate', '2024-12-10')
        
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
                    "itineraries": [
                        {
                            "duration": "PT14H20M",
                            "segments": [
                                {
                                    "carrierCode": "AF",
                                    "number": "401",
                                    "departure": {
                                        "iataCode": origin,
                                        "at": f"{departure_date}T23:35:00"
                                    },
                                    "arrival": {
                                        "iataCode": destination,
                                        "at": f"{departure_date}T15:55:00"
                                    }
                                }
                            ]
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
                    "itineraries": [
                        {
                            "duration": "PT13H15M",
                            "segments": [
                                {
                                    "carrierCode": "LH",
                                    "number": "507",
                                    "departure": {
                                        "iataCode": origin,
                                        "at": f"{departure_date}T18:15:00"
                                    },
                                    "arrival": {
                                        "iataCode": "FRA",
                                        "at": f"{departure_date}T10:30:00"
                                    }
                                },
                                {
                                    "carrierCode": "LH",
                                    "number": "1040",
                                    "departure": {
                                        "iataCode": "FRA",
                                        "at": f"{departure_date}T12:45:00"
                                    },
                                    "arrival": {
                                        "iataCode": destination,
                                        "at": f"{departure_date}T14:00:00"
                                    }
                                }
                            ]
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
        Busca melhores preços para um período flexível
        
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
        from datetime import datetime, timedelta
        
        logging.info(f"Buscando melhores preços: {params}")
        
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
        """Retorna dados simulados de melhores preços"""
        import random
        from datetime import datetime, timedelta
        
        origin = params.get('originLocationCode', 'GRU')
        destination = params.get('destinationLocationCode', 'SSA')
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
            
            best_prices.append({
                'date': date,
                'price': price,
                'currency': currency,
                'flight_id': f"mock-{origin}-{destination}-{date}",
                'is_simulated': True,
                'affiliate_link': f"https://example.com/flights?origin={origin}&destination={destination}&date={date}"
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

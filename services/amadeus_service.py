import os
import requests
import json
import logging
from datetime import datetime, timedelta

class AmadeusService:
    def __init__(self):
        self.api_key = os.environ.get('AMADEUS_API_KEY')
        self.api_secret = os.environ.get('AMADEUS_API_SECRET')
        self.base_url = 'https://test.api.amadeus.com/v1'
        self.token = None
        self.token_expires = None
        
    def get_token(self):
        """Obtém ou renova o token de autenticação OAuth2"""
        now = datetime.now()
        
        # Se já temos um token válido, retorna ele
        if self.token and self.token_expires and now < self.token_expires:
            return self.token
            
        # Caso contrário, solicita um novo token
        url = f"{self.base_url}/security/oauth2/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()  # Lança exceção para códigos de erro HTTP
            
            result = response.json()
            self.token = result.get('access_token')
            expires_in = result.get('expires_in', 1800)  # Padrão 30 minutos
            self.token_expires = now + timedelta(seconds=expires_in)
            
            return self.token
        except Exception as e:
            logging.error(f"Erro ao obter token Amadeus: {str(e)}")
            return None
    
    def search_flights(self, params):
        """
        Busca voos usando a API Flight Offers Search
        
        Parâmetros:
        - params: dicionário com parâmetros da busca como:
          - originLocationCode: código IATA do aeroporto de origem
          - destinationLocationCode: código IATA do aeroporto de destino
          - departureDate: data de partida (YYYY-MM-DD)
          - returnDate: data de retorno (YYYY-MM-DD)
          - adults: número de adultos
          - children: número de crianças
          - infants: número de bebês
          - travelClass: classe de viagem (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
          - currencyCode: moeda (ex: BRL)
          - max: número máximo de ofertas a retornar
        """
        token = self.get_token()
        if not token:
            return {'error': 'Falha na autenticação com a API Amadeus'}
            
        url = f"{self.base_url}/shopping/flight-offers"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Erro na busca de voos: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Resposta da API: {e.response.text}")
            return {'error': f'Erro na busca de voos: {str(e)}'}
    
    def search_hotels(self, params):
        """
        Busca hotéis usando a API Hotel List
        
        Parâmetros:
        - params: dicionário com parâmetros como:
          - cityCode: código da cidade
          - radius: raio em KM
          - radiusUnit: unidade do raio (KM ou MILE)
          - hotelName: nome do hotel
          - amenities: comodidades
          - ratings: classificações
          - priceRange: faixa de preço
        """
        token = self.get_token()
        if not token:
            return {'error': 'Falha na autenticação com a API Amadeus'}
            
        url = f"{self.base_url}/reference-data/locations/hotels/by-city"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Erro na busca de hotéis: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Resposta da API: {e.response.text}")
            return {'error': f'Erro na busca de hotéis: {str(e)}'}
    
    def search_hotel_offers(self, params):
        """
        Busca ofertas de hotéis usando a API Hotel Offers
        
        Parâmetros:
        - params: dicionário com parâmetros como:
          - hotelIds: lista de IDs de hotéis
          - adults: número de adultos
          - checkInDate: data de check-in (YYYY-MM-DD)
          - checkOutDate: data de check-out (YYYY-MM-DD)
          - roomQuantity: quantidade de quartos
          - priceRange: faixa de preço
          - currency: moeda (ex: BRL)
        """
        token = self.get_token()
        if not token:
            return {'error': 'Falha na autenticação com a API Amadeus'}
            
        url = f"{self.base_url}/shopping/hotel-offers"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Erro na busca de ofertas de hotéis: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Resposta da API: {e.response.text}")
            return {'error': f'Erro na busca de ofertas de hotéis: {str(e)}'}
    
    def get_flight_price(self, flight_offer):
        """
        Verifica o preço atual de uma oferta de voo
        
        Parâmetros:
        - flight_offer: objeto com a oferta de voo
        """
        token = self.get_token()
        if not token:
            return {'error': 'Falha na autenticação com a API Amadeus'}
            
        url = f"{self.base_url}/shopping/flight-offers/pricing"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'data': {
                'type': 'flight-offers-pricing',
                'flightOffers': [flight_offer]
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Erro ao verificar preço do voo: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Resposta da API: {e.response.text}")
            return {'error': f'Erro ao verificar preço do voo: {str(e)}'}
    
    def get_hotel_offer(self, offer_id):
        """
        Obtém os detalhes de uma oferta específica de hotel
        
        Parâmetros:
        - offer_id: ID da oferta de hotel
        """
        token = self.get_token()
        if not token:
            return {'error': 'Falha na autenticação com a API Amadeus'}
            
        url = f"{self.base_url}/shopping/hotel-offers/{offer_id}"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Erro ao obter oferta de hotel: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Resposta da API: {e.response.text}")
            return {'error': f'Erro ao obter oferta de hotel: {str(e)}'}

# Exemplo de uso:
# amadeus = AmadeusService()
# params = {
#     'originLocationCode': 'GRU',
#     'destinationLocationCode': 'CDG',
#     'departureDate': '2023-12-01',
#     'adults': 1,
#     'currencyCode': 'BRL'
# }
# result = amadeus.search_flights(params)
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
            
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        try:
            logging.info(f"Obtendo token do Amadeus com chave: {self.api_key[:5]}... e secret: {self.api_secret[:3]}...")
            response = requests.post(url, data=payload)
            
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
        if self.use_mock_data:
            return self._get_mock_flights(params)
            
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        
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
            logging.error(f"Erro ao buscar voos: {str(e)}")
            
            # Se ocorrer um erro, retorna o erro formatado
            return {"error": str(e)}
    
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

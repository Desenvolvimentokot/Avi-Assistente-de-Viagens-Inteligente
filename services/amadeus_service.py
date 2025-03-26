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
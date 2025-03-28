#!/usr/bin/env python3
import os
import logging
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
        self.client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Inicializa o cliente Amadeus com as credenciais"""
        api_key = os.environ.get('AMADEUS_API_KEY')
        api_secret = os.environ.get('AMADEUS_API_SECRET')
        
        if not api_key or not api_secret:
            logger.warning("Credenciais da API Amadeus não encontradas nas variáveis de ambiente")
            return
        
        try:
            self.client = Client(
                client_id=api_key,
                client_secret=api_secret,
                logger=logger
            )
            logger.info("Cliente Amadeus inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Amadeus: {str(e)}")
    
    def test_connection(self):
        """Testa a conexão com a API do Amadeus e retorna um diagnóstico"""
        if not self.client:
            return {
                "status": "error",
                "message": "Cliente Amadeus não inicializado. Verifique as credenciais.",
                "details": None
            }
        
        try:
            # Testa a busca de voos com parâmetros simples
            tomorrow = datetime.now() + timedelta(days=1)
            response = self.client.shopping.flight_offers_search.get(
                originLocationCode='GRU',
                destinationLocationCode='CDG',
                departureDate=tomorrow.strftime('%Y-%m-%d'),
                adults=1,
                max=1
            )
            
            return {
                "status": "success",
                "message": "Conexão com a API Amadeus estabelecida com sucesso",
                "details": {
                    "flight_offers_count": len(response.data) if hasattr(response, 'data') else 0
                }
            }
            
        except ResponseError as e:
            error_details = e.response.result.get('errors', [{}])[0]
            return {
                "status": "error",
                "message": f"Erro na conexão com a API Amadeus: {error_details.get('title', '')}",
                "details": {
                    "status_code": e.response.status_code,
                    "error_detail": error_details.get('detail', ''),
                    "error_source": error_details.get('source', {})
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro inesperado na conexão com a API Amadeus: {str(e)}",
                "details": None
            }
    
    def search_flights(self, params):
        """
        Busca voos baseado nos parâmetros fornecidos
        
        Params:
        - originLocationCode: código IATA da origem (exemplo: "GRU")
        - destinationLocationCode: código IATA do destino (exemplo: "CDG")
        - departureDate: data de partida (formato YYYY-MM-DD)
        - returnDate: data de retorno (opcional, formato YYYY-MM-DD)
        - adults: número de adultos (default: 1)
        - children: número de crianças (opcional)
        - infants: número de bebês (opcional)
        - travelClass: classe de viagem (opcional, ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
        - currencyCode: moeda (default: "BRL")
        - max: número máximo de resultados (default: 10)
        """
        if not self.client:
            logger.error("Cliente Amadeus não inicializado")
            return {
                "status": "error",
                "message": "Cliente Amadeus não inicializado. Verifique as credenciais.",
                "data": None
            }
        
        try:
            # Extrair parâmetros com valores padrão
            origin = params.get('originLocationCode')
            destination = params.get('destinationLocationCode')
            departure_date = params.get('departureDate')
            return_date = params.get('returnDate')
            adults = params.get('adults', 1)
            children = params.get('children', 0)
            infants = params.get('infants', 0)
            travel_class = params.get('travelClass')
            currency = params.get('currencyCode', 'BRL')
            max_results = params.get('max', 10)
            
            logger.info(f"Buscando voos de {origin} para {destination} em {departure_date}")
            
            # Construir parâmetros para o SDK
            sdk_params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults,
                'currencyCode': currency,
                'max': max_results
            }
            
            # Adicionar parâmetros opcionais apenas se fornecidos
            if return_date:
                sdk_params['returnDate'] = return_date
                
            if children > 0:
                sdk_params['children'] = children
                
            if infants > 0:
                sdk_params['infants'] = infants
                
            if travel_class:
                sdk_params['travelClass'] = travel_class
            
            # Fazer a requisição à API
            response = self.client.shopping.flight_offers_search.get(**sdk_params)
            
            return {
                "status": "success",
                "message": f"Encontrados {len(response.data)} voos",
                "data": response.data
            }
            
        except ResponseError as e:
            error_details = e.response.result.get('errors', [{}])[0]
            logger.error(f"Erro na busca de voos: {error_details.get('title', '')}")
            
            return {
                "status": "error",
                "message": f"Erro na busca de voos: {error_details.get('title', '')}",
                "data": None,
                "error_details": {
                    "status_code": e.response.status_code,
                    "error_detail": error_details.get('detail', ''),
                    "error_source": error_details.get('source', {})
                }
            }
        except Exception as e:
            logger.error(f"Erro inesperado na busca de voos: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erro inesperado na busca de voos: {str(e)}",
                "data": None
            }
    
    def get_flight_price(self, flight_offer):
        """
        Verifica o preço atual de uma oferta de voo
        
        Parâmetros:
        - flight_offer: objeto com a oferta de voo
        """
        if not self.client:
            logger.error("Cliente Amadeus não inicializado")
            return None
        
        try:
            # Converte flight_offer para objeto Python se for string JSON
            if isinstance(flight_offer, str):
                import json
                flight_offer = json.loads(flight_offer)
            
            # Formata a oferta conforme esperado pela API
            flight_offers = [flight_offer]
            
            # Chama a API de preços
            response = self.client.shopping.flight_offers.pricing.post(
                flight_offers
            )
            
            return {
                "status": "success",
                "message": "Preço verificado com sucesso",
                "data": response.data
            }
            
        except ResponseError as e:
            error_details = e.response.result.get('errors', [{}])[0]
            logger.error(f"Erro ao verificar preço: {error_details.get('title', '')}")
            
            return {
                "status": "error",
                "message": f"Erro ao verificar preço: {error_details.get('title', '')}",
                "data": None
            }
        except Exception as e:
            logger.error(f"Erro inesperado ao verificar preço: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erro inesperado ao verificar preço: {str(e)}",
                "data": None
            }
    
    def search_hotels(self, params):
        """
        Busca hotéis baseado nos parâmetros fornecidos
        
        Params:
        - cityCode: código da cidade (exemplo: "PAR" para Paris)
        - radius: raio em KM (opcional)
        - radiusUnit: unidade do raio (KM ou MILE, opcional)
        - amenities: comodidades (opcional)
        - ratings: classificações (opcional)
        """
        if not self.client:
            logger.error("Cliente Amadeus não inicializado")
            return {
                "status": "error",
                "message": "Cliente Amadeus não inicializado. Verifique as credenciais.",
                "data": None
            }
            
        try:
            # Extrair parâmetros
            city_code = params.get('cityCode')
            
            # Construir parâmetros para o SDK
            sdk_params = {
                'cityCode': city_code,
            }
            
            # Adicionar parâmetros opcionais apenas se fornecidos
            if 'radius' in params:
                sdk_params['radius'] = params['radius']
                
            if 'radiusUnit' in params:
                sdk_params['radiusUnit'] = params['radiusUnit']
                
            if 'amenities' in params:
                sdk_params['amenities'] = params['amenities']
                
            if 'ratings' in params:
                sdk_params['ratings'] = params['ratings']
            
            # Fazer a requisição à API
            response = self.client.reference_data.locations.hotels.by_city.get(**sdk_params)
            
            return {
                "status": "success",
                "message": f"Encontrados {len(response.data)} hotéis",
                "data": response.data
            }
            
        except ResponseError as e:
            error_details = e.response.result.get('errors', [{}])[0]
            logger.error(f"Erro na busca de hotéis: {error_details.get('title', '')}")
            
            return {
                "status": "error",
                "message": f"Erro na busca de hotéis: {error_details.get('title', '')}",
                "data": None
            }
        except Exception as e:
            logger.error(f"Erro inesperado na busca de hotéis: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erro inesperado na busca de hotéis: {str(e)}",
                "data": None
            }
    
    def search_hotel_offers(self, params):
        """
        Busca ofertas de hotéis baseado nos parâmetros fornecidos
        
        Params:
        - hotelIds: lista de IDs de hotéis separados por vírgula
        - adults: número de adultos (default: 1)
        - checkInDate: data de check-in (formato YYYY-MM-DD)
        - checkOutDate: data de check-out (formato YYYY-MM-DD)
        - roomQuantity: quantidade de quartos (opcional)
        - currency: moeda (default: "BRL")
        """
        if not self.client:
            logger.error("Cliente Amadeus não inicializado")
            return {
                "status": "error",
                "message": "Cliente Amadeus não inicializado. Verifique as credenciais.",
                "data": None
            }
            
        try:
            # Extrair parâmetros
            hotel_ids = params.get('hotelIds')
            adults = params.get('adults', 1)
            check_in = params.get('checkInDate')
            check_out = params.get('checkOutDate')
            currency = params.get('currency', 'BRL')
            
            # Construir parâmetros para o SDK
            sdk_params = {
                'hotelIds': hotel_ids,
                'adults': adults,
                'checkInDate': check_in,
                'checkOutDate': check_out,
                'currency': currency
            }
            
            # Adicionar parâmetros opcionais apenas se fornecidos
            if 'roomQuantity' in params:
                sdk_params['roomQuantity'] = params['roomQuantity']
            
            # Fazer a requisição à API
            response = self.client.shopping.hotel_offers.get(**sdk_params)
            
            return {
                "status": "success",
                "message": f"Encontradas {len(response.data)} ofertas de hotéis",
                "data": response.data
            }
            
        except ResponseError as e:
            error_details = e.response.result.get('errors', [{}])[0]
            logger.error(f"Erro na busca de ofertas de hotéis: {error_details.get('title', '')}")
            
            return {
                "status": "error",
                "message": f"Erro na busca de ofertas de hotéis: {error_details.get('title', '')}",
                "data": None
            }
        except Exception as e:
            logger.error(f"Erro inesperado na busca de ofertas de hotéis: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erro inesperado na busca de ofertas de hotéis: {str(e)}",
                "data": None
            }
            
    def get_hotel_offer(self, offer_id):
        """
        Obtém os detalhes de uma oferta específica de hotel
        
        Parâmetros:
        - offer_id: ID da oferta de hotel
        """
        if not self.client:
            logger.error("Cliente Amadeus não inicializado")
            return None
            
        try:
            response = self.client.shopping.hotel_offer(offer_id).get()
            
            return {
                "status": "success",
                "message": "Detalhes da oferta obtidos com sucesso",
                "data": response.data
            }
            
        except ResponseError as e:
            error_details = e.response.result.get('errors', [{}])[0]
            logger.error(f"Erro ao obter detalhes da oferta: {error_details.get('title', '')}")
            
            return {
                "status": "error",
                "message": f"Erro ao obter detalhes da oferta: {error_details.get('title', '')}",
                "data": None
            }
        except Exception as e:
            logger.error(f"Erro inesperado ao obter detalhes da oferta: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erro inesperado ao obter detalhes da oferta: {str(e)}",
                "data": None
            }

import os
import requests
import logging
import json
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmadeusService:
    """
    Serviço para interagir com a API Amadeus para busca de voos e outras funcionalidades relacionadas a viagens.
    """
    
    def __init__(self):
        """
        Inicializa o serviço Amadeus com as credenciais e configurações básicas.
        """
        self.base_url = "https://test.api.amadeus.com"
        self.token_endpoint = "/v1/security/oauth2/token"
        self.flight_offers_endpoint = "/v2/shopping/flight-offers"
        
        # Obter credenciais do ambiente
        self.api_key = os.environ.get("AMADEUS_API_KEY")
        self.api_secret = os.environ.get("AMADEUS_API_SECRET")
        
        # Verificar se as credenciais estão configuradas
        if not self.api_key or not self.api_secret:
            logger.warning("Credenciais do Amadeus não configuradas. Configure AMADEUS_API_KEY e AMADEUS_API_SECRET nos Secrets do Replit.")
        
        # Inicialmente, não temos um token válido
        self.access_token = None
        self.token_expiry = None

    def _get_access_token(self):
        """
        Obtém um token de acesso OAuth 2.0 da API Amadeus.
        
        Returns:
            str: Token de acesso ou None se ocorrer um erro.
        """
        # Verificar se já temos um token válido
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            logger.info("Usando token Amadeus existente")
            return self.access_token
        
        try:
            logger.info("Solicitando novo token de acesso Amadeus")
            
            # Preparar os dados para a solicitação
            token_data = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret
            }
            
            # Fazer a solicitação para obter o token
            response = requests.post(
                f"{self.base_url}{self.token_endpoint}",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # Verificar se a resposta foi bem-sucedida
            response.raise_for_status()
            
            # Extrair o token da resposta
            token_info = response.json()
            self.access_token = token_info.get("access_token")
            
            # Calcular quando o token expira (subtraindo 5 minutos para segurança)
            expires_in = token_info.get("expires_in", 1800)  # Padrão de 30 minutos se não especificado
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
            
            logger.info(f"Token Amadeus obtido com sucesso, válido até {self.token_expiry}")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Erro ao obter token Amadeus: {str(e)}")
            self.access_token = None
            self.token_expiry = None
            return None

    def search_flight_offers(self, origin, destination, departure_date, return_date=None, adults=1, 
                            currency="BRL", max_results=25):
        """
        Busca ofertas de voos usando a API Amadeus.
        
        Args:
            origin (str): Código IATA do aeroporto de origem (ex: 'GRU' para Guarulhos)
            destination (str): Código IATA do aeroporto de destino (ex: 'JFK' para Nova York)
            departure_date (str): Data de partida no formato 'YYYY-MM-DD'
            return_date (str, opcional): Data de retorno no formato 'YYYY-MM-DD' para voos de ida e volta
            adults (int, opcional): Número de adultos, padrão é 1
            currency (str, opcional): Moeda para os valores, padrão é 'BRL'
            max_results (int, opcional): Número máximo de resultados, padrão é 25
        
        Returns:
            dict: Dados das ofertas de voos ou mensagem de erro
        """
        try:
            # Obter token de acesso
            token = self._get_access_token()
            if not token:
                return {"error": "Não foi possível obter autorização da API Amadeus"}
            
            # Montar os parâmetros da consulta
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "currencyCode": currency,
                "max": max_results
            }
            
            # Adicionar data de retorno se fornecida
            if return_date:
                params["returnDate"] = return_date
            
            # Configurar os cabeçalhos com o token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Buscando voos de {origin} para {destination} em {departure_date}")
            
            # Fazer a solicitação de busca de voos
            response = requests.get(
                f"{self.base_url}{self.flight_offers_endpoint}",
                params=params,
                headers=headers
            )
            
            # Verificar se a resposta foi bem-sucedida
            response.raise_for_status()
            
            # Retornar os dados da resposta
            flight_data = response.json()
            logger.info(f"Encontradas {len(flight_data.get('data', []))} ofertas de voos")
            return flight_data
            
        except requests.exceptions.HTTPError as e:
            # Tratamento específico para erros HTTP da API
            error_message = f"Erro HTTP na API Amadeus: {str(e)}"
            try:
                error_details = e.response.json()
                if "errors" in error_details and error_details["errors"]:
                    error_message = f"Erro da API Amadeus: {error_details['errors'][0].get('detail', str(e))}"
            except:
                pass
            
            logger.error(error_message)
            return {"error": error_message}
            
        except Exception as e:
            error_message = f"Erro ao buscar voos: {str(e)}"
            logger.error(error_message)
            return {"error": error_message}

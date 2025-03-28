#!/usr/bin/env python3
import os
import requests
import json
import logging
import time
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter

# Configurar logger específico para o módulo
logger = logging.getLogger('amadeus_service')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class AmadeusService:
    """Serviço otimizado para integração com a API do Amadeus"""
    
    def __init__(self):
        """Inicializa o serviço com configurações otimizadas"""
        # Obter credenciais de variáveis de ambiente
        self.api_key = os.environ.get('AMADEUS_API_KEY')
        self.api_secret = os.environ.get('AMADEUS_API_SECRET')
        
        # Configuração de ambiente
        self.is_production = os.environ.get('AMADEUS_PRODUCTION', 'false').lower() == 'true'
        self.base_url = 'https://api.amadeus.com/v1' if self.is_production else 'https://test.api.amadeus.com/v1'
        
        # Configurações de autenticação
        self.token = None
        self.token_expires = None
        self.token_buffer = 300  # 5 minutos de margem para expiração do token
        
        # Configurar sessão HTTP com timeouts adequados
        self.session = self._create_session()
        
        # Relatório inicial de configuração
        logger.info(f"AmadeusService inicializado - Ambiente: {'Produção' if self.is_production else 'Teste'}")
        logger.info(f"URL Base: {self.base_url}")
        
        # Logs de verificação de credenciais (ocultando valores sensíveis)
        if self.api_key:
            logger.info(f"API Key configurada: {self.api_key[:4]}...{self.api_key[-4:] if len(self.api_key) > 8 else ''}")
        else:
            logger.warning("API Key não configurada!")
            
        if self.api_secret:
            logger.info(f"API Secret configurada: {self.api_secret[:2]}...{self.api_secret[-2:] if len(self.api_secret) > 4 else ''}")
        else:
            logger.warning("API Secret não configurada!")

    def _create_session(self):
        """Cria uma sessão HTTP otimizada com timeouts adequados"""
        session = requests.Session()
        
        # Usando um adaptador simples - sem Retry para evitar dependências externas
        adapter = HTTPAdapter(max_retries=3)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def ensure_valid_token(self):
        """
        Garante que um token válido está disponível, renovando-o automaticamente quando necessário
        
        Returns:
            str: Token de autenticação válido
        """
        now = datetime.now()
        
        # Se temos um token e ele não está prestes a expirar, usar o existente
        if self.token and self.token_expires and now < (self.token_expires - timedelta(seconds=self.token_buffer)):
            logger.debug("Usando token existente")
            return self.token
            
        # Renovar o token
        logger.info("Renovando token de autenticação Amadeus")
        
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
            # Usar a sessão configurada sem autenticação Bearer
            response = self.session.post(
                url, 
                headers=headers, 
                data=data,
                timeout=(3.05, 10)  # 3.05s para conexão, 10s para leitura
            )
            
            # Log detalhado da resposta
            logger.debug(f"Resposta de autenticação: Status {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Falha na autenticação: {response.status_code} - {response.text}")
                return None
                
            # Processar resposta
            result = response.json()
            self.token = result.get('access_token')
            
            # Configurar tempo de expiração
            expires_in = result.get('expires_in', 1800)  # Padrão 30 minutos
            self.token_expires = now + timedelta(seconds=expires_in)
            
            logger.info(f"Token obtido com sucesso. Expira em {expires_in} segundos.")
            
            return self.token
            
        except requests.exceptions.ConnectTimeout:
            logger.error("Timeout na conexão durante autenticação")
            return None
        except requests.exceptions.ReadTimeout:
            logger.error("Timeout na leitura durante autenticação")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de requisição durante autenticação: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erro desconhecido durante autenticação: {str(e)}")
            return None

    def search_flights(self, params):
        """
        Busca voos usando a API Flight Offers Search com tratamento aprimorado de erros e logging
        
        Args:
            params (dict): Parâmetros da busca
                - originLocationCode: código IATA do aeroporto de origem
                - destinationLocationCode: código IATA do aeroporto de destino
                - departureDate: data de partida (YYYY-MM-DD)
                - returnDate: data de retorno (YYYY-MM-DD) (opcional)
                - adults: número de adultos
                - children: número de crianças (opcional)
                - infants: número de bebês (opcional)
                - travelClass: classe de viagem (opcional)
                - currencyCode: moeda (opcional)
                - max: número máximo de ofertas (opcional)
                
        Returns:
            dict: Resultados da API ou dicionário com erro
        """
        # Validar parâmetros essenciais
        required_params = ['originLocationCode', 'destinationLocationCode', 'departureDate', 'adults']
        for param in required_params:
            if param not in params:
                logger.error(f"Parâmetro obrigatório ausente: {param}")
                return {'error': f"Parâmetro obrigatório ausente: {param}"}
                
        # Logs detalhados dos parâmetros
        safe_params = {**params}
        logger.info(f"Iniciando busca de voos: {safe_params}")
        
        # Garantir token válido
        token = self.ensure_valid_token()
        if not token:
            return {'error': 'Falha na autenticação com a API Amadeus'}
            
        # Preparar requisição    
        url = f"{self.base_url}/shopping/flight-offers"
        if self.is_production:
            # Na produção, a versão mais recente é a v2
            url = f"{self.base_url.replace('/v1', '/v2')}/shopping/flight-offers"
            
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        # Métricas de tempo
        start_time = time.time()
        
        try:
            # Fazer requisição
            logger.debug(f"Enviando requisição GET para {url}")
            
            response = self.session.get(
                url, 
                headers=headers, 
                params=params,
                timeout=(3.05, 30)  # 3.05s para conexão, 30s para leitura
            )
            
            # Tempo total de resposta
            elapsed = time.time() - start_time
            logger.debug(f"Tempo de resposta: {elapsed:.2f}s")
            
            # Log de resposta
            logger.debug(f"Resposta obtida: Status {response.status_code}")
            
            # Verificar erros HTTP
            if response.status_code != 200:
                error_message = response.text
                logger.error(f"Erro na API ({response.status_code}): {error_message}")
                
                # Detecção de erros específicos do Amadeus
                if response.status_code == 401:
                    # Analisar o erro para verificar se é um problema de produto/permissão
                    if "InvalidAPICallAsNoApiProductMatchFound" in error_message:
                        logger.error("Problema com permissões da API: A chave API não tem acesso a este endpoint")
                        return {
                            'error': 'Permissão de API insuficiente',
                            'details': 'A chave API atual não tem acesso ao endpoint de flight-offers. ' +
                                      'Verifique as permissões da sua conta Amadeus e certifique-se de que ' +
                                      'o plano/assinatura inclui acesso à API de Flight Offers.',
                            'recommendation': 'Acesse https://developers.amadeus.com para verificar sua assinatura e permissões.',
                            'raw_error': error_message
                        }
                    else:
                        return {'error': 'Autenticação inválida', 'details': error_message}
                # Formatar diferentes tipos de erro
                elif response.status_code == 400:
                    return {'error': 'Parâmetros de busca inválidos', 'details': error_message}
                elif response.status_code == 403:
                    return {'error': 'Acesso não autorizado', 'details': error_message}
                elif response.status_code >= 500:
                    return {'error': 'Erro no servidor da API', 'details': error_message}
                else:
                    return {'error': f'Erro HTTP {response.status_code}', 'details': error_message}
            
            # Processar dados
            result = response.json()
            
            # Verificar se há resultados
            flights_count = len(result.get('data', []))
            logger.info(f"Busca concluída: {flights_count} voos encontrados")
            
            return result
            
        except requests.exceptions.ConnectTimeout:
            logger.error("Timeout na conexão durante busca de voos")
            return {"error": "Timeout de conexão"}
        except requests.exceptions.ReadTimeout:
            logger.error("Timeout na leitura durante busca de voos")
            return {"error": "Timeout de leitura"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de requisição durante busca de voos: {str(e)}")
            return {"error": f"Erro de requisição: {str(e)}"}
        except json.JSONDecodeError:
            logger.error("Erro ao decodificar resposta JSON")
            return {"error": "Resposta inválida da API"}
        except Exception as e:
            logger.error(f"Erro inesperado durante busca de voos: {str(e)}")
            return {"error": f"Erro inesperado: {str(e)}"}

    def search_hotels(self, params):
        """
        Busca hotéis usando a API Hotel List com tratamento aprimorado de erros
        
        Args:
            params (dict): Parâmetros da busca
                - cityCode: código da cidade
                - radius: raio em KM (opcional)
                - radiusUnit: unidade do raio (opcional)
                - hotelName: nome do hotel (opcional)
                - amenities: comodidades (opcional)
                - ratings: classificações (opcional)
                
        Returns:
            dict: Resultados da API ou dicionário com erro
        """
        # Validar parâmetros essenciais
        if 'cityCode' not in params:
            logger.error("Parâmetro obrigatório ausente: cityCode")
            return {'error': "Parâmetro obrigatório ausente: cityCode"}
            
        # Garantir token válido
        token = self.ensure_valid_token()
        if not token:
            return {'error': 'Falha na autenticação com a API Amadeus'}
            
        # Preparar requisição    
        url = f"{self.base_url}/reference-data/locations/hotels/by-city"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        logger.info(f"Iniciando busca de hotéis: {params}")
        
        try:
            # Fazer requisição
            response = self.session.get(
                url, 
                headers=headers, 
                params=params,
                timeout=(3.05, 20)  # 3.05s para conexão, 20s para leitura
            )
            
            # Verificar erros HTTP
            if response.status_code != 200:
                logger.error(f"Erro na API ({response.status_code}): {response.text}")
                return {'error': f'Erro HTTP {response.status_code}', 'details': response.text}
            
            # Processar dados
            result = response.json()
            
            # Verificar se há resultados
            hotels_count = len(result.get('data', []))
            logger.info(f"Busca concluída: {hotels_count} hotéis encontrados")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro durante busca de hotéis: {str(e)}")
            return {'error': f'Erro na busca de hotéis: {str(e)}'}

    def search_hotel_offers(self, params):
        """
        Busca ofertas de hotéis usando a API Hotel Offers
        
        Args:
            params (dict): Parâmetros da busca
                - hotelIds: lista de IDs de hotéis (opcional)
                - cityCode: código da cidade (opcional, usar se hotelIds não for fornecido)
                - adults: número de adultos
                - checkInDate: data de check-in (YYYY-MM-DD)
                - checkOutDate: data de check-out (YYYY-MM-DD)
                - roomQuantity: quantidade de quartos (opcional)
                - priceRange: faixa de preço (opcional)
                - currency: moeda (opcional)
                
        Returns:
            dict: Resultados da API ou dicionário com erro
        """
        # Validar parâmetros essenciais
        required_params = ['adults', 'checkInDate', 'checkOutDate']
        if 'hotelIds' not in params and 'cityCode' not in params:
            required_params.append('hotelIds ou cityCode')
            
        for param in required_params:
            if param not in params and param != 'hotelIds ou cityCode':
                logger.error(f"Parâmetro obrigatório ausente: {param}")
                return {'error': f"Parâmetro obrigatório ausente: {param}"}
                
        # Garantir token válido
        token = self.ensure_valid_token()
        if not token:
            return {'error': 'Falha na autenticação com a API Amadeus'}
            
        # Preparar requisição    
        url = f"{self.base_url}/shopping/hotel-offers"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        logger.info(f"Iniciando busca de ofertas de hotéis")
        
        try:
            # Fazer requisição
            response = self.session.get(
                url, 
                headers=headers, 
                params=params,
                timeout=(3.05, 30)  # 3.05s para conexão, 30s para leitura
            )
            
            # Verificar erros HTTP
            if response.status_code != 200:
                logger.error(f"Erro na API ({response.status_code}): {response.text}")
                return {'error': f'Erro HTTP {response.status_code}', 'details': response.text}
            
            # Processar dados
            result = response.json()
            
            # Verificar se há resultados
            offers_count = len(result.get('data', []))
            logger.info(f"Busca concluída: {offers_count} ofertas de hotéis encontradas")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro durante busca de ofertas de hotéis: {str(e)}")
            return {'error': f'Erro na busca de ofertas de hotéis: {str(e)}'}

    def test_connection(self):
        """
        Testa a conexão com a API do Amadeus e fornece diagnóstico detalhado
        
        Returns:
            dict: Resultado do teste de conexão
        """
        result = {
            "success": False,
            "credentials": {
                "api_key_set": bool(self.api_key),
                "api_secret_set": bool(self.api_secret),
                "valid": False
            },
            "connectivity": {
                "can_connect": False,
                "timeout_ms": None,
                "endpoint": None
            },
            "token": {
                "obtained": False,
                "value": None,
                "expires_in": None
            },
            "environment": "production" if self.is_production else "test",
            "base_url": self.base_url,
            "errors": []
        }
        
        # Testar obtenção de token
        logger.info("Testando conexão com Amadeus API...")
        
        try:
            start_time = time.time()
            token = self.ensure_valid_token()
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            result["connectivity"]["timeout_ms"] = elapsed_ms
            
            if token:
                result["success"] = True
                result["credentials"]["valid"] = True
                result["connectivity"]["can_connect"] = True
                result["token"]["obtained"] = True
                result["token"]["value"] = f"{token[:5]}...{token[-5:] if len(token) > 10 else ''}"
                
                if self.token_expires:
                    now = datetime.now()
                    expires_in_seconds = int((self.token_expires - now).total_seconds())
                    result["token"]["expires_in"] = expires_in_seconds
                    
                # Testar um endpoint simples
                test_url = f"{self.base_url}/reference-data/locations"
                try:
                    params = {"keyword": "PAR", "subType": "CITY", "page[limit]": 1}
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    endpoint_start = time.time()
                    response = self.session.get(test_url, headers=headers, params=params, timeout=(3.05, 10))
                    endpoint_elapsed_ms = int((time.time() - endpoint_start) * 1000)
                    
                    result["connectivity"]["endpoint"] = {
                        "url": test_url,
                        "status": response.status_code,
                        "timeout_ms": endpoint_elapsed_ms,
                        "success": response.status_code == 200
                    }
                    
                except Exception as endpoint_error:
                    result["connectivity"]["endpoint"] = {
                        "url": test_url,
                        "error": str(endpoint_error),
                        "success": False
                    }
                    result["errors"].append(f"Falha ao testar endpoint: {str(endpoint_error)}")
            else:
                result["errors"].append("Não foi possível obter token de autenticação")
                
        except Exception as e:
            result["errors"].append(f"Erro durante teste de conexão: {str(e)}")
            
        logger.info(f"Teste de conexão concluído: {'Sucesso' if result['success'] else 'Falha'}")
        return result

# Exemplo de uso:
# service = AmadeusService()
# test_result = service.test_connection()
# print(json.dumps(test_result, indent=2))
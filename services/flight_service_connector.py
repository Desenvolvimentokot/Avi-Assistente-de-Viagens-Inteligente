"""
Conector direto entre o chat e o serviço de busca de voos do Amadeus
Esse serviço simplifica a integração direta entre chat e busca de voos.
"""

import logging
import json
import requests
from datetime import datetime, timedelta

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlightServiceConnector:
    """
    Classe responsável por conectar o processador de chat diretamente 
    com o serviço de busca de voos do Amadeus, sem depender de GPT
    """
    
    def __init__(self):
        """Inicializa o conector de serviço de voos"""
        self.base_url = ""  # URL base é relativa pois estamos no mesmo servidor
    
    def search_flights_from_chat(self, travel_info, session_id):
        """
        Processa as informações extraídas do chat e envia diretamente 
        para a API do Amadeus para buscar resultados reais
        
        Args:
            travel_info: Dicionário com informações de viagem extraídas do chat
            session_id: ID da sessão do chat para rastreamento
            
        Returns:
            dict: Resultados da busca ou erro
        """
        try:
            logger.info(f"Iniciando busca de voos com session_id: {session_id}")
            logger.info(f"Informações de viagem: {travel_info}")
            
            # Verificar se temos informações suficientes
            if not travel_info.get('origin') or not travel_info.get('destination'):
                return {
                    "error": "Informações de origem ou destino não fornecidas",
                    "data": []
                }
            
            # Determinar o tipo de busca (data específica ou período)
            if travel_info.get('date_range_start') and travel_info.get('date_range_end'):
                # Busca de período flexível (melhores preços)
                return self._search_best_prices(travel_info, session_id)
            elif travel_info.get('departure_date'):
                # Busca de data específica (voos)
                return self._search_specific_flights(travel_info, session_id)
            else:
                return {
                    "error": "Data de viagem não fornecida",
                    "data": []
                }
                
        except Exception as e:
            logger.error(f"Erro na busca de voos: {str(e)}")
            return {
                "error": f"Erro ao buscar voos: {str(e)}",
                "data": []
            }
    
    def _search_specific_flights(self, travel_info, session_id):
        """
        Busca voos para data específica usando diretamente
        o endpoint do nosso buscador do Amadeus-test
        
        Args:
            travel_info: Informações da viagem
            session_id: ID da sessão
            
        Returns:
            dict: Resultados da busca
        """
        try:
            # Preparar dados para a requisição
            search_data = {
                "originLocationCode": travel_info.get('origin'),
                "destinationLocationCode": travel_info.get('destination'),
                "departureDate": travel_info.get('departure_date'),
                "adults": travel_info.get('adults', 1),
                "currencyCode": travel_info.get('currency', 'BRL')
            }
            
            # Adicionar data de retorno se disponível
            if travel_info.get('return_date'):
                search_data["returnDate"] = travel_info.get('return_date')
            
            # Fazer a requisição para o nosso endpoint de teste do Amadeus
            logger.info(f"Fazendo requisição direta para API Amadeus com {search_data}")
            
            # URL relativa para evitar problemas com portas
            url = "/api/amadeus/flights"
            logger.info(f"URL de conexão: {url}")
            
            response = requests.post(
                url,
                json=search_data,
                timeout=30
            )
            
            # Processar resposta
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Resultados obtidos com sucesso! {len(result.get('data', []))} voos encontrados")
                return result
            else:
                logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
                return {
                    "error": f"Erro ao buscar voos: {response.status_code}",
                    "data": []
                }
                
        except Exception as e:
            logger.error(f"Erro ao buscar voos específicos: {str(e)}")
            return {
                "error": f"Falha na busca: {str(e)}",
                "data": []
            }
    
    def _search_best_prices(self, travel_info, session_id):
        """
        Busca melhores preços para um período flexível
        
        Args:
            travel_info: Informações da viagem
            session_id: ID da sessão
            
        Returns:
            dict: Resultados da busca
        """
        try:
            # Preparar dados para a requisição
            search_data = {
                "originLocationCode": travel_info.get('origin'),
                "destinationLocationCode": travel_info.get('destination'),
                "departureDate": travel_info.get('date_range_start'),
                "returnDate": travel_info.get('date_range_end'),
                "adults": travel_info.get('adults', 1),
                "currencyCode": travel_info.get('currency', 'BRL')
            }
            
            # Fazer a requisição para o nosso endpoint de melhores preços do Amadeus
            logger.info(f"Fazendo requisição para API de melhores preços com {search_data}")
            
            # URL relativa para evitar problemas com portas
            url = "/api/amadeus/best-prices"
            logger.info(f"URL de conexão para melhores preços: {url}")
            
            response = requests.post(
                url,
                json=search_data,
                timeout=30
            )
            
            # Processar resposta
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Resultados de melhores preços obtidos com sucesso!")
                return result
            else:
                logger.error(f"Erro na requisição de melhores preços: {response.status_code} - {response.text}")
                return {
                    "error": f"Erro ao buscar melhores preços: {response.status_code}",
                    "data": []
                }
                
        except Exception as e:
            logger.error(f"Erro ao buscar melhores preços: {str(e)}")
            return {
                "error": f"Falha na busca de melhores preços: {str(e)}",
                "data": []
            }
    
    def format_flight_results_for_chat(self, results):
        """
        Formata os resultados da busca de voos para exibição no chat
        
        Args:
            results: Resultados da busca
            
        Returns:
            dict: Mensagem formatada e flag para mostrar painel lateral
        """
        try:
            if not results or 'error' in results:
                error_message = results.get('error', 'Não foi possível encontrar voos para sua busca.')
                return {
                    "message": f"Desculpe, tive um problema ao buscar voos: {error_message}",
                    "show_flight_results": False
                }
            
            # Contagem de voos encontrados
            flight_count = len(results.get('data', []))
            
            if flight_count == 0:
                return {
                    "message": "Não encontrei voos disponíveis para os critérios informados. Você poderia ajustar as datas ou destinos?",
                    "show_flight_results": False
                }
            
            # Mensagem para o chat informando sobre os resultados
            message = f"Encontrei {flight_count} opções de voos para sua viagem. "
            message += "Você pode ver todos os detalhes no painel lateral que acabei de abrir. "
            
            # Destacar algumas informações principais
            if flight_count > 0:
                try:
                    # Pegar o primeiro voo como exemplo
                    first_flight = results['data'][0]
                    price = first_flight['price']['total']
                    currency = first_flight['price']['currency']
                    
                    message += f"\n\nOs preços começam a partir de {currency} {price}. "
                    message += "Confira as opções no painel e me avise se tiver dúvidas ou quiser mais informações sobre algum voo específico."
                except Exception as e:
                    logger.error(f"Erro ao extrair detalhes do primeiro voo: {str(e)}")
            
            return {
                "message": message,
                "show_flight_results": True
            }
            
        except Exception as e:
            logger.error(f"Erro ao formatar resultados para chat: {str(e)}")
            return {
                "message": f"Encontrei alguns voos, mas tive um problema ao formatar os resultados: {str(e)}",
                "show_flight_results": True  # Ainda mostrar o painel mesmo com erro de formatação
            }

# Instância global para uso em outros módulos
flight_service_connector = FlightServiceConnector()
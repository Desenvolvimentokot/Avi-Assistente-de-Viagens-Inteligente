"""
Conector direto entre o chat e o serviço de busca de voos do TravelPayouts
Esse serviço simplifica a integração direta entre chat e busca de voos.
"""

import logging
import json
import requests
import os
from datetime import datetime, timedelta

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlightServiceConnector:
    """
    Classe responsável por conectar o processador de chat diretamente 
    com o serviço de busca de voos do TravelPayouts, sem depender de GPT
    """

    def __init__(self):
        """Inicializa o conector de serviço de voos"""
        self.base_url = ""  # URL base é relativa pois estamos no mesmo servidor

    def search_flights_from_chat(self, travel_info, session_id):
        """
        Processa as informações extraídas do chat e envia diretamente 
        para a API do TravelPayouts para buscar resultados reais

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
        o endpoint do nosso buscador do TravelPayouts

        Args:
            travel_info: Informações da viagem
            session_id: ID da sessão

        Returns:
            dict: Resultados da busca
        """
        try:
            # Logs de monitoramento detalhados para rastrear a busca
            logger.warning(f"⭐ BUSCA REAL: Iniciando busca para sessão {session_id}")

            # Validação dos parâmetros obrigatórios
            required_params = ['origin', 'destination', 'departure_date']
            for param in required_params:
                if not travel_info.get(param):
                    error_msg = f"Parâmetro obrigatório ausente: {param}"
                    logger.error(error_msg)
                    return {
                        "error": error_msg,
                        "data": []
                    }

            # Preparar dados para a requisição no formato da API TravelPayouts
            search_data = {
                "origin": travel_info.get('origin').upper(),
                "destination": travel_info.get('destination').upper(),
                "departure_date": travel_info.get('departure_date'),
                "return_date": travel_info.get('return_date'),
                "adults": travel_info.get('adults', 1),
                "currency": travel_info.get('currency', 'BRL'),
                "session_id": session_id
            }
            
            # Adicionar o session_id para rastreamento
            search_data["session_id"] = session_id

            # Fazer a requisição para o endpoint da API TravelPayouts
            logger.warning(f"📡 Requisitando dados reais da API TravelPayouts: {json.dumps(search_data)}")

            # URL relativa para acessar a API interna
            url = "/api/travelpayouts/flights"
            logger.warning(f"URL para API TravelPayouts: {url}")
            
            # Incluir cabeçalhos para a requisição
            headers = {
                "X-Session-ID": session_id,
                "X-Request-Source": "flight_service_connector",
                "Content-Type": "application/json"
            }

            # Registrar tempo de início para medição
            import time
            start_time = time.time()

            response = requests.post(
                url,
                headers=headers,
                json=search_data,
                timeout=30  # 30 segundos de timeout
            )

            # Calcular tempo de resposta
            elapsed_time = time.time() - start_time
            logger.warning(f"⏱️ Tempo de resposta da API: {elapsed_time:.2f} segundos")

            # Processar resposta
            if response.status_code == 200:
                result = response.json()
                flight_count = len(result.get('data', []))

                if flight_count > 0:
                    logger.warning(f"✅ SUCESSO! {flight_count} voos reais encontrados para sessão {session_id}")

                    # Adicionar session_id aos resultados
                    result['session_id'] = session_id

                    # Armazenar nos resultados quando foi feita a busca
                    from datetime import datetime
                    result['search_timestamp'] = datetime.utcnow().isoformat()

                    return result
                else:
                    logger.error(f"⚠️ API retornou 0 resultados para sessão {session_id}")
                    return {
                        "error": "Nenhum voo encontrado para os critérios informados",
                        "data": []
                    }
            else:
                logger.error(f"❌ Erro na requisição: {response.status_code} - {response.text}")
                return {
                    "error": f"Erro ao buscar voos: {response.status_code}",
                    "data": []
                }

        except Exception as e:
            logger.error(f"❌ Exceção ao buscar voos: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "error": f"Falha na busca: {str(e)}",
                "data": []
            }

    def _search_best_prices(self, travel_info, session_id):
        """
        Busca melhores preços para um período flexível usando a API TravelPayouts

        Args:
            travel_info: Informações da viagem
            session_id: ID da sessão

        Returns:
            dict: Resultados da busca
        """
        try:
            # Preparar dados para a requisição no formato da API TravelPayouts
            search_data = {
                "origin": travel_info.get('origin').upper(),
                "destination": travel_info.get('destination').upper(),
                "departure_date": travel_info.get('date_range_start'),
                "return_date": travel_info.get('date_range_end'),
                "adults": travel_info.get('adults', 1),
                "currency": travel_info.get('currency', 'BRL'),
                "flexible_dates": True,
                "session_id": session_id
            }
            
            # Adicionar o session_id para rastreamento
            search_data["session_id"] = session_id

            # Fazer a requisição para o endpoint da API TravelPayouts
            logger.info(f"Fazendo requisição para API de melhores preços TravelPayouts: {json.dumps(search_data)}")

            # URL relativa para evitar problemas com portas
            url = "/api/travelpayouts/best-prices"
            logger.info(f"URL de conexão para melhores preços: {url}")
            
            # Incluir cabeçalhos para a requisição
            headers = {
                "X-Session-ID": session_id,
                "X-Request-Source": "flight_service_connector",
                "Content-Type": "application/json"
            }
            
            # Registrar tempo de início para medição
            import time
            start_time = time.time()
            
            response = requests.post(
                url,
                headers=headers,
                json=search_data,
                timeout=30
            )
            
            # Calcular tempo de resposta
            elapsed_time = time.time() - start_time
            logger.warning(f"⏱️ Tempo de resposta da API: {elapsed_time:.2f} segundos")

            # Processar resposta
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Resultados de melhores preços obtidos com sucesso!")
                
                # Adicionar session_id aos resultados
                result['session_id'] = session_id
                
                return result
            else:
                logger.error(f"Erro na requisição de melhores preços: {response.status_code} - {response.text}")
                return {
                    "error": f"Erro ao buscar melhores preços: {response.status_code}",
                    "data": []
                }

        except Exception as e:
            logger.error(f"Erro ao buscar melhores preços: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
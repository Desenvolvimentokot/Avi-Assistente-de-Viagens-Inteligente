"""
Conector direto entre o chat e o serviço de busca de voos do TravelPayouts
Esse serviço simplifica a integração direta entre chat e busca de voos.
"""

import logging
import json
import requests
import os
from datetime import datetime, timedelta
from services.travelpayouts_service import TravelPayoutsService

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TravelPayoutsConnector:
    """
    Classe responsável por conectar o processador de chat diretamente 
    com o serviço de busca de voos do TravelPayouts, sem depender de GPT
    """

    def __init__(self):
        """Inicializa o conector de serviço de voos"""
        self.travelpayouts_service = TravelPayoutsService()

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
        Busca voos para data específica usando o serviço TravelPayouts

        Args:
            travel_info: Informações da viagem
            session_id: ID da sessão

        Returns:
            dict: Resultados da busca
        """
        try:
            # Logs de monitoramento detalhados para rastrear a busca
            logger.warning(f"⭐ BUSCA REAL: Iniciando busca para sessão {session_id} via TravelPayouts")

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

            # Preparar os parâmetros para o serviço TravelPayouts
            search_params = {
                'originLocationCode': travel_info.get('origin'),
                'destinationLocationCode': travel_info.get('destination'),
                'departureDate': travel_info.get('departure_date'),
                'adults': travel_info.get('adults', 1)
            }
            
            # Adicionar data de retorno se existir
            if travel_info.get('return_date'):
                search_params['returnDate'] = travel_info.get('return_date')
            
            # Registrar tempo de início para medição
            import time
            start_time = time.time()
            
            # Buscar voos usando o serviço TravelPayouts
            logger.warning(f"📡 Requisitando dados reais da API TravelPayouts: {json.dumps(search_params)}")
            flight_results = self.travelpayouts_service.search_flights(search_params)
            
            # Calcular tempo de resposta
            elapsed_time = time.time() - start_time
            logger.warning(f"⏱️ Tempo de resposta da API TravelPayouts: {elapsed_time:.2f} segundos")
            
            # Processar os resultados
            if flight_results:
                flight_count = len(flight_results)
                logger.warning(f"✅ SUCESSO! {flight_count} voos encontrados para sessão {session_id}")
                
                # Formatar a resposta no mesmo formato que o cliente espera
                formatted_response = {
                    "data": flight_results,
                    "session_id": session_id,
                    "search_timestamp": datetime.utcnow().isoformat(),
                    "meta": {
                        "origin": travel_info.get('origin'),
                        "destination": travel_info.get('destination'),
                        "departure_date": travel_info.get('departure_date'),
                        "return_date": travel_info.get('return_date'),
                        "currency": "BRL",
                        "source": "TravelPayouts"
                    }
                }
                
                return formatted_response
            else:
                logger.error(f"⚠️ API retornou 0 resultados para sessão {session_id}")
                return {
                    "error": "Nenhum voo encontrado para os critérios informados",
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
        Busca melhores preços para um período flexível usando TravelPayouts

        Args:
            travel_info: Informações da viagem
            session_id: ID da sessão

        Returns:
            dict: Resultados da busca
        """
        try:
            # Obter o mês a partir da data de início do período (YYYY-MM)
            date_parts = travel_info.get('date_range_start', '').split('-')
            if len(date_parts) >= 2:
                month = f"{date_parts[0]}-{date_parts[1]}"
            else:
                # Se não tiver data específica, usar mês atual
                month = datetime.now().strftime('%Y-%m')
            
            # Logging para debug
            logger.info(f"Buscando melhores preços para {travel_info.get('origin')} → {travel_info.get('destination')} em {month}")
            
            # Buscar melhores preços
            best_prices = self.travelpayouts_service.search_best_prices(
                origin=travel_info.get('origin'),
                destination=travel_info.get('destination'),
                depart_date=month
            )
            
            if best_prices:
                # Formatar a resposta para o formato esperado
                formatted_response = {
                    "data": best_prices,
                    "session_id": session_id,
                    "search_timestamp": datetime.utcnow().isoformat(),
                    "meta": {
                        "origin": travel_info.get('origin'),
                        "destination": travel_info.get('destination'),
                        "month": month,
                        "currency": "BRL",
                        "source": "TravelPayouts"
                    }
                }
                
                return formatted_response
            else:
                logger.error(f"⚠️ API retornou 0 resultados de melhores preços para sessão {session_id}")
                return {
                    "error": "Nenhum preço encontrado para os critérios informados",
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

            # Verificar se temos meta-informações
            meta = results.get('meta', {})
            origin = meta.get('origin', '???')
            destination = meta.get('destination', '???')
            departure_date = meta.get('departure_date', 'data especificada')
            currency = meta.get('currency', 'BRL')

            # Mensagem para o chat informando sobre os resultados
            message = f"Encontrei {flight_count} opções de voos para sua viagem de {origin} para {destination}. "
            
            # Se estamos usando redirecionamento, mostrar uma mensagem diferente
            is_redirect = False
            for flight in results.get('data', []):
                if flight.get('is_redirect', False):
                    is_redirect = True
                    break
            
            if is_redirect:
                message = f"Para sua viagem de {origin} para {destination} em {departure_date}, você pode ver todas as opções disponíveis clicando no botão abaixo:"
                return {
                    "message": message,
                    "show_flight_results": True,
                    "redirect_button": True,
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date
                }
            
            # Destacar algumas informações principais
            if flight_count > 0:
                try:
                    # Pegar o primeiro voo como exemplo
                    first_flight = results['data'][0]
                    price = first_flight['price']['total']
                    
                    message += f"\n\nOs preços começam a partir de {currency} {price}. "
                    
                    # Adicionar informações sobre o primeiro voo
                    first_departure = ""
                    first_arrival = ""
                    if first_flight.get('itineraries') and first_flight['itineraries'][0].get('segments'):
                        segment = first_flight['itineraries'][0]['segments'][0]
                        if segment.get('departure') and segment.get('arrival'):
                            first_departure = segment['departure'].get('at', '').split('T')[1][:5]
                            first_arrival = segment['arrival'].get('at', '').split('T')[1][:5]
                    
                    if first_departure and first_arrival:
                        message += f"Por exemplo, há um voo saindo às {first_departure} e chegando às {first_arrival}."
                
                except Exception as e:
                    logger.error(f"Erro ao formatar primeiro voo: {str(e)}")
            
            message += "\n\nClique no botão abaixo para ver todas as opções disponíveis:"
            
            # Retornar a mensagem e os parâmetros para o botão de redirecionamento
            return {
                "message": message,
                "show_flight_results": True,
                "redirect_button": True,
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date
            }
        
        except Exception as e:
            logger.error(f"Erro ao formatar resultados: {str(e)}")
            return {
                "message": "Encontrei algumas opções de voos, mas tive problemas ao formatar os resultados. Clique no botão abaixo para ver as opções disponíveis:",
                "show_flight_results": True
            }

    def get_partner_link(self, travel_info):
        """
        Gera um link de parceiro para redirecionamento direto para TravelPayouts
        
        Args:
            travel_info: Informações da viagem
            
        Returns:
            str: URL para redirecionamento
        """
        try:
            # Verificar informações essenciais
            if not travel_info.get('origin') or not travel_info.get('destination'):
                logger.error("Origem ou destino não fornecidos para link de parceiro")
                return None
                
            # Gerar link usando o serviço TravelPayouts
            return self.travelpayouts_service.get_partner_link(
                origin=travel_info.get('origin'),
                destination=travel_info.get('destination'),
                departure_date=travel_info.get('departure_date'),
                return_date=travel_info.get('return_date')
            )
        
        except Exception as e:
            logger.error(f"Erro ao gerar link de parceiro: {str(e)}")
            return None
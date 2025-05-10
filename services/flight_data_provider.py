"""
Serviço intermediário para fornecer dados reais de voos para o chat
Este serviço conecta o processador de chat às rotas de API TravelPayouts
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlightDataProvider:
    """
    Fornece dados de voos reais da API TravelPayouts para o sistema de chat
    """
    
    def __init__(self):
        """Inicializa o provedor de dados de voos"""
        self.base_url = "http://0.0.0.0:5000"  # URL base para as chamadas da API interna
        self.session_cache = {}  # Cache para armazenar resultados por sessão
    
    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, currency="BRL", session_id=None):
        """
        Busca voos disponíveis para os parâmetros fornecidos
        
        Args:
            origin: Código IATA do aeroporto de origem
            destination: Código IATA do aeroporto de destino
            departure_date: Data de partida (YYYY-MM-DD)
            return_date: Data de retorno (YYYY-MM-DD), opcional
            adults: Número de adultos
            currency: Código da moeda
            session_id: ID da sessão de chat para cache
            
        Returns:
            dict: Resultados da busca de voos
        """
        try:
            # Verificar se temos resultados em cache para esta sessão
            if session_id and session_id in self.session_cache:
                logger.info(f"Usando dados de voo em cache para sessão {session_id}")
                return self.session_cache[session_id]
            
            # Preparar parâmetros da requisição
            params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date,
                "adults": adults,
                "currencyCode": currency
            }
            
            # Adicionar data de retorno se fornecida
            if return_date:
                params["returnDate"] = return_date
            
            # Fazer a chamada à API interna
            logger.info(f"Buscando voos: {origin} -> {destination} em {departure_date}")
            url = f"{self.base_url}/api/travelpayouts/flights"
            response = requests.post(url, json=params)
            
            # Verificar se a requisição foi bem sucedida
            if response.status_code == 200:
                flight_data = response.json()
                
                # Se temos um session_id, armazenar em cache
                if session_id:
                    self.session_cache[session_id] = flight_data
                    # Atualizar o ID da sessão nos dados para futura referência
                    flight_data['session_id'] = session_id
                
                return flight_data
            else:
                logger.error(f"Erro na API de voos: {response.status_code}")
                logger.error(f"Detalhes: {response.text}")
                return {"error": f"Erro ao buscar voos: {response.status_code}", "details": response.text}
        
        except Exception as e:
            logger.error(f"Erro ao buscar voos: {str(e)}")
            return {"error": f"Erro ao buscar voos: {str(e)}"}
    
    def search_best_prices(self, origin, destination, date_range_start, date_range_end, 
                          adults=1, currency="BRL", max_dates=3, session_id=None):
        """
        Busca os melhores preços disponíveis para um período
        
        Args:
            origin: Código IATA do aeroporto de origem
            destination: Código IATA do aeroporto de destino
            date_range_start: Data inicial do período (YYYY-MM-DD)
            date_range_end: Data final do período (YYYY-MM-DD)
            adults: Número de adultos
            currency: Código da moeda
            max_dates: Número máximo de datas a verificar
            session_id: ID da sessão de chat para cache
            
        Returns:
            dict: Resultados da busca de melhores preços
        """
        try:
            # Verificar se temos resultados em cache para esta sessão
            cache_key = f"best_prices_{session_id}"
            if session_id and cache_key in self.session_cache:
                logger.info(f"Usando dados de melhores preços em cache para sessão {session_id}")
                return self.session_cache[cache_key]
            
            # Preparar parâmetros da requisição
            params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": date_range_start,
                "returnDate": date_range_end,
                "adults": adults,
                "currencyCode": currency,
                "max_dates_to_check": max_dates
            }
            
            # Fazer a chamada à API interna
            logger.info(f"Buscando melhores preços: {origin} -> {destination} entre {date_range_start} e {date_range_end}")
            url = f"{self.base_url}/api/travelpayouts/best-prices"
            response = requests.post(url, json=params)
            
            # Verificar se a requisição foi bem sucedida
            if response.status_code == 200:
                price_data = response.json()
                
                # Se temos um session_id, armazenar em cache
                if session_id:
                    self.session_cache[cache_key] = price_data
                    # Atualizar o ID da sessão nos dados para futura referência
                    price_data['session_id'] = session_id
                
                return price_data
            else:
                logger.error(f"Erro na API de melhores preços: {response.status_code}")
                logger.error(f"Detalhes: {response.text}")
                return {"error": f"Erro ao buscar melhores preços: {response.status_code}", "details": response.text}
        
        except Exception as e:
            logger.error(f"Erro ao buscar melhores preços: {str(e)}")
            return {"error": f"Erro ao buscar melhores preços: {str(e)}"}
    
    def clear_cache(self, session_id=None):
        """
        Limpa o cache de dados de voo
        
        Args:
            session_id: ID da sessão para limpar cache específico, ou None para limpar tudo
        """
        if session_id:
            if session_id in self.session_cache:
                del self.session_cache[session_id]
            if f"best_prices_{session_id}" in self.session_cache:
                del self.session_cache[f"best_prices_{session_id}"]
        else:
            self.session_cache.clear()
    
    def get_cached_data(self, session_id):
        """
        Obtém dados em cache para uma sessão específica
        
        Args:
            session_id: ID da sessão
            
        Returns:
            dict: Dados em cache ou None se não houver
        """
        if session_id in self.session_cache:
            return self.session_cache[session_id]
        return None
    
    def format_flight_results_for_chat(self, flight_data, best_prices_data=None):
        """
        Formata os resultados da API para exibição no chat
        
        Args:
            flight_data: Dados da busca de voos
            best_prices_data: Dados dos melhores preços, opcional
            
        Returns:
            dict: Mensagem formatada para o chat
        """
        try:
            # Verificar se temos dados válidos
            if not flight_data or "error" in flight_data:
                return {
                    "message": "Não foi possível obter dados de voos no momento. Por favor, tente novamente mais tarde.",
                    "show_flight_results": False
                }
            
            # Verificar se temos dados de voos
            if "data" not in flight_data or not flight_data["data"]:
                return {
                    "message": "Não encontrei voos disponíveis com esses critérios. Que tal tentar outras datas ou destinos?",
                    "show_flight_results": False
                }
            
            # Extrair dados básicos para a mensagem
            offers = flight_data["data"]
            num_offers = len(offers)
            
            # Pegar o voo mais barato
            cheapest_offer = min(offers, key=lambda x: float(x.get("price", {}).get("total", "999999")))
            cheapest_price = float(cheapest_offer.get("price", {}).get("total", "0"))
            currency = cheapest_offer.get("price", {}).get("currency", "BRL")
            
            # Extrair origem e destino do primeiro voo
            first_itinerary = offers[0]["itineraries"][0]
            first_segment = first_itinerary["segments"][0]
            last_segment = first_itinerary["segments"][-1]
            
            origin = first_segment["departure"]["iataCode"]
            destination = last_segment["arrival"]["iataCode"]
            
            # Construir a mensagem para o chat
            message = (
                f"Encontrei {num_offers} voos disponíveis de {origin} para {destination}! "
                f"Os preços começam em {currency} {cheapest_price:.2f}.\n\n"
                f"Para ver todos os detalhes, consulte o painel lateral de resultados que acabei de abrir, "
                f"onde você pode visualizar informações completas sobre cada opção de voo."
            )
            
            # Adicionar informação sobre melhores preços se disponível
            if best_prices_data and "best_prices" in best_prices_data and best_prices_data["best_prices"]:
                best_prices = best_prices_data["best_prices"]
                if len(best_prices) > 0:
                    best_price = min(best_prices, key=lambda x: x["price"])
                    message += (
                        f"\n\nSe sua data for flexível, encontrei um preço ainda melhor: "
                        f"R$ {best_price['price']:.2f} para o dia {self._format_date(best_price['date'])}."
                    )
            
            # Retornar a mensagem formatada e indicar que o painel lateral deve ser mostrado
            return {
                "message": message,
                "show_flight_results": True,
                "session_id": flight_data.get("session_id")
            }
        
        except Exception as e:
            logger.error(f"Erro ao formatar resultados de voo para chat: {str(e)}")
            return {
                "message": "Encontrei alguns voos, mas tive um problema ao processar os detalhes. "
                           "Por favor, verifique o painel lateral para ver as opções disponíveis.",
                "show_flight_results": True,
                "session_id": flight_data.get("session_id")
            }
    
    def _format_date(self, date_str):
        """Formata uma string de data para DD/MM/YYYY"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except:
            return date_str


# Instância global para uso em toda a aplicação
flight_data_provider = FlightDataProvider()
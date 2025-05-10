"""
Serviço de integração com o widget Trip.com para busca de voos reais
utilizando Playwright para interagir com o widget e extrair resultados.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

# Configuração de logging
logger = logging.getLogger(__name__)

class TripWidgetService:
    """
    Classe para integração direta com o widget Trip.com através do Playwright.
    Esta implementação permite obter resultados reais de voos diretamente do 
    widget oficial do Trip.com sem depender de APIs REST que podem ter limitações.
    """
    
    def __init__(self):
        """Inicializa o serviço de widget Trip.com"""
        self.marker = os.environ.get("TRAVELPAYOUTS_MARKER", "620701")
        self.search_page_url = "http://localhost:5000/widget/trip-search"
        self.browser = None
        self.context = None
    
    async def search_flights(self, origin, destination, departure_date, return_date=None, adults=1):
        """
        Busca voos usando o widget Trip.com através do Playwright.
        
        Args:
            origin: código IATA do aeroporto de origem
            destination: código IATA do aeroporto de destino
            departure_date: data de partida no formato YYYY-MM-DD
            return_date: data de retorno no formato YYYY-MM-DD (opcional)
            adults: número de adultos
            
        Returns:
            Lista de resultados de voos ou lista vazia se não encontrar
        """
        logger.info(f"Iniciando busca de voos via widget Trip.com: {origin} → {destination}")
        
        try:
            async with async_playwright() as playwright:
                # Inicializar o navegador
                self.browser = await playwright.chromium.launch(headless=True)
                self.context = await self.browser.new_context()
                
                # Criar uma nova página
                page = await self.context.new_page()
                
                # Navegar para a página de busca que contém o widget
                await page.goto(self.search_page_url)
                
                # Aguardar o carregamento do widget Trip.com (script async)
                logger.info("Aguardando carregamento do widget Trip.com")
                await page.wait_for_load_state("networkidle")
                
                # Configurar o array global para capturar resultados
                await page.evaluate("window.flights_data = []")
                
                # Injetar o listener para capturar mensagens do widget
                await page.evaluate("""() => {
                    window.addEventListener('message', event => {
                        console.log('Recebida mensagem postMessage:', JSON.stringify(event.data).substring(0, 200));
                        if (event.data && event.data.tpFlightResults) {
                            console.log('Capturados resultados de voos:', event.data.tpFlightResults.length);
                            window.flights_data.push(...event.data.tpFlightResults);
                        }
                    });
                }""")
                
                # Preencher os campos do widget
                logger.info("Preenchendo campos do widget")
                
                # Os seletores abaixo precisam ser ajustados com base na estrutura real do widget
                # Tentar preencher o campo de origem
                await page.fill('input[name="origin"]', origin)
                
                # Tentar preencher o campo de destino
                await page.fill('input[name="destination"]', destination)
                
                # Tentar preencher o campo de data de ida
                await page.fill('input[name="departureDate"]', departure_date)
                
                # Tentar preencher o campo de data de volta (se fornecido)
                if return_date:
                    await page.fill('input[name="returnDate"]', return_date)
                
                # Tentar definir o número de adultos (se o widget tiver esse campo)
                # Este campo pode variar dependendo da estrutura do widget
                try:
                    await page.fill('input[name="adults"]', str(adults))
                except:
                    logger.warning("Campo de adultos não encontrado, usando valor padrão")
                
                # Clicar no botão de busca do widget
                logger.info("Clicando no botão de busca do widget")
                await page.click('button.tp-search-button')
                
                # Aguardar até que os resultados sejam recebidos via postMessage
                logger.info("Aguardando resultados do widget Trip.com")
                try:
                    await page.wait_for_function(
                        "window.flights_data.length >= 2", 
                        timeout=15000
                    )
                    logger.info("Resultados recebidos com sucesso!")
                except Exception as e:
                    logger.warning(f"Timeout aguardando resultados: {str(e)}")
                
                # Extrair os dois melhores resultados de voos
                flights = await page.evaluate("window.flights_data.slice(0, 2)")
                
                # Verificar se temos resultados
                if not flights or len(flights) == 0:
                    logger.warning("Nenhum resultado de voo encontrado via widget")
                    return []
                
                logger.info(f"Encontrados {len(flights)} voos via widget Trip.com")
                
                # Formatar os resultados para o formato padrão da aplicação
                formatted_flights = self._format_flights(flights, origin, destination)
                
                # Fechar o navegador
                await self.browser.close()
                self.browser = None
                
                return formatted_flights
                
        except Exception as e:
            logger.error(f"Erro ao buscar voos via widget Trip.com: {str(e)}")
            
            # Garantir que o navegador seja fechado em caso de erro
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            return []
    
    def _format_flights(self, flights, origin, destination):
        """
        Formata os resultados de voos do widget Trip.com para o formato padrão da aplicação.
        
        Args:
            flights: Lista de resultados de voos do widget Trip.com
            origin: código IATA de origem
            destination: código IATA de destino
            
        Returns:
            Lista de voos formatados
        """
        formatted_flights = []
        
        for flight in flights:
            try:
                # Os campos abaixo precisam ser ajustados com base na estrutura real dos resultados
                price = flight.get("price", "0")
                departure_at = flight.get("departure_at", "")
                return_at = flight.get("return_at", "")
                airline = flight.get("airline", "")
                flight_number = flight.get("flight_number", "")
                
                # Construir URL de reserva (formato pode variar)
                booking_url = flight.get("booking_url", "")
                if not booking_url:
                    booking_url = f"https://www.travelpayouts.com/flight_search/widget_redirect/?marker={self.marker}&origin={origin}&destination={destination}&departure_at={departure_at}&locale=pt&currency=BRL&one_way=true"
                
                # Construir itinerários (ida)
                itineraries = []
                outbound_segments = []
                
                # Segmento de ida
                outbound_segments.append({
                    "departure": {
                        "iataCode": origin,
                        "at": departure_at
                    },
                    "arrival": {
                        "iataCode": destination,
                        "at": flight.get("arrival_at", departure_at)  # Pode precisar de ajuste
                    },
                    "carrierCode": airline,
                    "number": flight_number
                })
                
                itineraries.append({
                    "segments": outbound_segments
                })
                
                # Segmento de volta (se for ida e volta)
                if return_at:
                    inbound_segments = []
                    inbound_segments.append({
                        "departure": {
                            "iataCode": destination,
                            "at": return_at
                        },
                        "arrival": {
                            "iataCode": origin,
                            "at": flight.get("return_arrival_at", return_at)  # Pode precisar de ajuste
                        },
                        "carrierCode": airline,
                        "number": flight_number
                    })
                    
                    itineraries.append({
                        "segments": inbound_segments
                    })
                
                # Formatar voo final
                formatted_flight = {
                    "id": f"TP{flight.get('id', '')}",
                    "itineraries": itineraries,
                    "price": {
                        "total": str(price),
                        "currency": "BRL"
                    },
                    "validatingAirlineCodes": [airline] if airline else ["TP"],
                    "source": "Trip.com",
                    "booking_url": booking_url
                }
                
                formatted_flights.append(formatted_flight)
                
            except Exception as e:
                logger.error(f"Erro ao formatar voo: {str(e)}")
        
        return formatted_flights

# Instanciar serviço para exportação
trip_widget_service = TripWidgetService()
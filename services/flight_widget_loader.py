"""
FlightWidgetLoader - Carregador de Widget Trip.com usando Playwright

Este serviço utiliza o Playwright para carregar o widget do Trip.com/TravelPayouts
em modo headless, permitindo a extração de resultados de busca para apresentação
em interfaces personalizadas.
"""

import os
import json
import time
import logging
import tempfile
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configurar logging
logger = logging.getLogger(__name__)

class FlightWidgetLoader:
    """
    Carregador de Widget Trip.com usando Playwright
    
    Usa automação de browser para interagir com o widget de busca do Trip.com/TravelPayouts
    e extrair os resultados de forma headless (sem interface visual).
    """
    
    def __init__(self):
        """Inicializa o carregador de widget"""
        self.base_url = "http://localhost:5000/widget/search_page"
        self.browser = None
        self.active_searches = {}
        self.playwright = None
        
        # Credenciais TravelPayouts (obter de variáveis de ambiente na versão final)
        self.tp_marker = os.environ.get('TP_MARKER', '620701')
        
        logger.info("FlightWidgetLoader inicializado")
    
    def start_search(self, search_id, origin, destination, departure_date, return_date=None, adults=1):
        """
        Inicia uma busca de voos usando o widget
        
        Args:
            search_id: ID único da busca
            origin: Código IATA da origem (ex: 'GRU')
            destination: Código IATA do destino (ex: 'JFK')
            departure_date: Data de ida (formato: 'YYYY-MM-DD')
            return_date: Data de volta (formato: 'YYYY-MM-DD'), opcional
            adults: Número de adultos, padrão 1
            
        Returns:
            bool: True se a busca foi iniciada com sucesso
        """
        # Armazenar dados da busca
        self.active_searches[search_id] = {
            'id': search_id,
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'return_date': return_date,
            'adults': adults,
            'status': 'initializing',
            'created_at': datetime.utcnow().isoformat(),
            'browser': None,
            'page': None,
            'results': None
        }
        
        logger.info(f"Iniciando busca {search_id}: {origin} → {destination}")
        
        # Em uma implementação completa, aqui iniciaríamos o processo em um worker separado
        # Por enquanto, apenas simulamos o processo para teste
        
        # Simular início da busca (na versão real, iniciar browser headless)
        self.active_searches[search_id]['status'] = 'processing'
        self.active_searches[search_id]['message'] = f'Buscando voos de {origin} para {destination}'
        
        # Iniciar busca real com Playwright em um thread separado
        import threading
        
        def run_browser_search():
            try:
                logger.info(f"Iniciando busca headless para {search_id} ({origin} → {destination})")
                # Iniciar Playwright
                playwright_instance = sync_playwright().start()
                browser = playwright_instance.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # Armazenar objetos para uso posterior e limpeza
                self.active_searches[search_id]['browser'] = browser
                self.active_searches[search_id]['page'] = page
                self.active_searches[search_id]['playwright'] = playwright_instance
                
                # Navegar para a página que contém o widget
                logger.info(f"Navegando para {self.base_url}")
                page.goto(self.base_url)
                
                # Preencher formulário
                logger.info(f"Preenchendo formulário: {origin} → {destination}")
                page.fill("#origin-input", origin)
                page.fill("#destination-input", destination)
                page.fill("#departure-date", departure_date)
                if return_date:
                    page.fill("#return-date", return_date)
                
                # Ajustar número de passageiros se necessário
                if adults > 1:
                    page.click("#passengers-select")
                    for _ in range(adults - 1):
                        page.click("#adults-plus-button")
                    page.click("#apply-passengers")
                
                # Iniciar busca
                logger.info(f"Clicando no botão de busca")
                page.click("#search-button")
                
                # Aguardar resultados (até 30 segundos)
                logger.info(f"Aguardando resultados...")
                has_results = False
                
                # Aguardar até que a página marque a busca como concluída (até 30 segundos)
                try:
                    page.wait_for_selector("[data-search-complete='true']", timeout=30000)
                    logger.info(f"Resultados encontrados para {search_id}")
                    has_results = True
                except Exception as e:
                    logger.error(f"Timeout ao aguardar resultados: {str(e)}")
                    self.active_searches[search_id]['status'] = 'error'
                    self.active_searches[search_id]['message'] = 'Tempo limite excedido ao buscar resultados'
                    return
                
                # Extrair resultados
                if has_results:
                    logger.info(f"Extraindo resultados dos cards de voo")
                    # Extrair dados dos cards de voo
                    flight_cards = page.query_selector_all(".flight-card")
                    results = []
                    
                    for card in flight_cards:
                        try:
                            airline_element = card.query_selector(".flight-airline")
                            airline = airline_element.inner_text() if airline_element else "Desconhecida"
                            
                            price_element = card.query_selector(".flight-price")
                            price_text = price_element.inner_text() if price_element else "0"
                            price = float(price_text.replace("R$ ", "").replace(".", "").replace(",", "."))
                            
                            times = card.query_selector_all(".flight-times span")
                            departure = ""
                            arrival = ""
                            
                            if times and len(times) > 0:
                                departure_element = times[0]
                                if departure_element:
                                    departure = departure_element.inner_text() or ""
                                
                                if len(times) > 1:
                                    arrival_element = times[-1]
                                    if arrival_element:
                                        arrival = arrival_element.inner_text() or ""
                            
                            duration_element = card.query_selector(".flight-duration")
                            stops_info = duration_element.inner_text() if duration_element else ""
                            stops = 0 if "Direto" in stops_info else 1
                            
                            # Construir URL de reserva
                            booking_url = f"https://www.travelpayouts.com/flight?marker={self.tp_marker}&origin={origin}&destination={destination}&departure_at={departure_date}&adults={adults}&with_request=true"
                            
                            flight_data = {
                                "airline": airline,
                                "price": price,
                                "currency": "BRL",
                                "departure": departure,
                                "arrival": arrival,
                                "stops": stops,
                                "bookingUrl": booking_url
                            }
                            
                            results.append(flight_data)
                        except Exception as extraction_error:
                            logger.error(f"Erro ao extrair dados do card: {str(extraction_error)}")
                    
                    # Armazenar resultados
                    if results:
                        logger.info(f"Encontrados {len(results)} voos para {search_id}")
                        self.active_searches[search_id]['results'] = results
                        self.active_searches[search_id]['status'] = 'complete'
                        self.active_searches[search_id]['message'] = 'Busca concluída com sucesso'
                    else:
                        logger.warning(f"Nenhum resultado encontrado para {search_id}")
                        self.active_searches[search_id]['status'] = 'complete'
                        self.active_searches[search_id]['message'] = 'Nenhum voo encontrado'
                        self.active_searches[search_id]['results'] = []
            
            except Exception as e:
                logger.error(f"Erro durante busca headless: {str(e)}")
                self.active_searches[search_id]['status'] = 'error'
                self.active_searches[search_id]['message'] = f'Erro: {str(e)}'
        
        # Iniciar thread de busca em background
        search_thread = threading.Thread(target=run_browser_search)
        search_thread.daemon = True
        search_thread.start()
        
        return True
        
    def check_status(self, search_id):
        """
        Verifica o status de uma busca em andamento
        
        Args:
            search_id: ID da busca
            
        Returns:
            dict: Informações sobre o status da busca
        """
        # Verificar se a busca existe
        if search_id not in self.active_searches:
            logger.error(f"Busca não encontrada: {search_id}")
            return None
        
        # Obter dados da busca
        search_data = self.active_searches[search_id]
        
        # Verificar estado atual da busca
        status = search_data.get('status', 'pending')
        
        # Se a busca já foi concluída ou falhou
        if status in ['complete', 'error']:
            return {
                'status': status,
                'message': search_data.get('message', 'Busca finalizada'),
                'progress': 100 if status == 'complete' else 0,
                'results': search_data.get('results', []) if status == 'complete' else None
            }
        
        # Se a busca ainda está em processamento
        current_time = datetime.utcnow()
        created_time = datetime.fromisoformat(search_data['created_at'])
        time_diff = (current_time - created_time).total_seconds()
        
        # Calcular progresso baseado no tempo decorrido (máximo 30 segundos)
        max_wait_time = 30.0  # 30 segundos
        elapsed_percent = min(time_diff / max_wait_time, 0.99)  # Nunca atinge 100% até completar
        progress = int(elapsed_percent * 100)
        
        # Mensagens mais específicas conforme o progresso
        if progress < 30:
            message = f'Conectando ao sistema de reservas...'
        elif progress < 60:
            message = f'Buscando voos de {search_data["origin"]} para {search_data["destination"]}...'
        elif progress < 80:
            message = f'Processando resultados...'
        else:
            message = f'Finalizando busca...'
        
        # Se a mensagem específica foi definida pelo processo de busca, usá-la
        if search_data.get('message'):
            message = search_data['message']
            
        return {
            'status': 'processing',
            'message': message,
            'progress': progress
        }
    
    def get_results(self, search_id):
        """
        Obtém os resultados de uma busca concluída
        
        Args:
            search_id: ID da busca
            
        Returns:
            list: Lista de voos encontrados
        """
        # Verificar se a busca existe
        if search_id not in self.active_searches:
            logger.error(f"Busca não encontrada: {search_id}")
            return None
        
        # Obter dados da busca
        search_data = self.active_searches[search_id]
        
        # Verificar se a busca foi concluída
        if search_data['status'] != 'complete':
            logger.warning(f"Busca {search_id} ainda não concluída. Status: {search_data['status']}")
            return None
        
        # Retornar resultados armazenados
        if search_data.get('results'):
            return search_data['results']
        
        # Se não encontrou resultados, retornar uma lista vazia em vez de dados simulados
        logger.warning(f"Busca {search_id} completa, mas sem resultados disponíveis")
        search_data['results'] = []
        return []
    
    # Esta função foi removida para garantir que apenas dados reais sejam utilizados
    
    def cleanup(self):
        """Limpa recursos (browsers, etc)"""
        # Limpar todas as buscas ativas
        for search_id, search_data in self.active_searches.items():
            try:
                # Fechar browser se existir
                if search_data.get('browser'):
                    search_data['browser'].close()
            except Exception as e:
                logger.error(f"Erro ao limpar busca {search_id}: {str(e)}")
        
        # Limpar dicionário
        self.active_searches.clear()
        
        # Fechar playwright se estiver aberto
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                logger.error(f"Erro ao fechar Playwright: {str(e)}")
            finally:
                self.playwright = None
                
        logger.info("FlightWidgetLoader finalizado, recursos liberados")
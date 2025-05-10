from playwright.sync_api import sync_playwright
import json
import logging
import time
import os

logger = logging.getLogger(__name__)

class FlightWidgetLoader:
    def __init__(self, base_url=None):
        """
        Inicializa o carregador de widget de voos
        
        Args:
            base_url: URL base para a página do widget (ex: https://seu-site.com)
        """
        self.base_url = base_url or os.environ.get('APP_URL', 'http://localhost:5000')
        
    def fetch_flights(self, session_id, travel_params):
        """
        Carrega a página do widget e extrai os resultados de voos.
        
        1. Abre a página interna headless
        2. Passa parâmetros de viagem via localStorage/sessionStorage
        3. Aguarda renderização dos cards do widget
        4. Extrai e retorna os 2 melhores voos como JSON
        
        Args:
            session_id: ID da sessão do usuário
            travel_params: Dicionário com parâmetros da viagem (origem, destino, datas, etc)
            
        Returns:
            Lista de dicionários com informações de voos
        """
        logger.info(f"Iniciando busca headless para sessão {session_id}")
        logger.info(f"Parâmetros: {travel_params}")
        
        results = []
        try:
            with sync_playwright() as p:
                # Usar o navegador Chromium que já instalamos via sistema
                browser = p.chromium.launch(
                    headless=True,
                    chromium_sandbox=False,
                    executable_path='/nix/store/xf2iyl9p1x3i23j6i52n0apzmmmk79gn-chromium-120.0.6099.216/bin/chromium'
                )
                
                page = browser.new_page()
                
                # Injetar travel_params para que o widget use
                script = f"window._travelParams = {json.dumps(travel_params)};"
                page.add_init_script(script)
                
                # Navegar para a página com o widget
                widget_url = f"{self.base_url}/widget_search?session_id={session_id}"
                logger.info(f"Navegando para: {widget_url}")
                
                page.goto(widget_url)
                
                # Aguardar o carregamento do widget (ajustar seletores conforme necessário)
                # Nota: o seletor .flight-result-card é um exemplo, precisará ser ajustado 
                # de acordo com o HTML real do widget Trip.com
                logger.info("Aguardando carregamento do widget...")
                
                # Primeiro verificamos se o widget foi carregado
                try:
                    # Aguardar até que o iframe do widget seja carregado
                    page.wait_for_selector('iframe', timeout=10000)
                    logger.info("Widget iframe detectado")
                    
                    # Aguardar mais alguns segundos para que o conteúdo seja carregado
                    time.sleep(5)
                    
                    # Verificar se há resultados dentro do iframe
                    # Como estamos apenas testando, vamos capturar a página para análise
                    page.screenshot(path=f"./temp/widget_screenshot_{session_id}.png")
                    logger.info("Screenshot capturado para análise")
                    
                    # Tentar extrair conteúdo do iframe
                    frames = page.frames
                    if len(frames) > 1:
                        logger.info(f"Encontrados {len(frames)} frames")
                        
                        # Aqui precisamos analisar a estrutura real do widget
                        # para extrair os dados corretos
                        
                        # Amostra de dados para validação inicial
                        # Em uma implementação real, estes dados seriam extraídos do DOM
                        results = [
                            {
                                "airline": "Obtendo do widget Trip.com",
                                "departure": "Aguarde processamento",
                                "arrival": "Aguarde processamento",
                                "price": 0,
                                "currency": "BRL",
                                "bookingUrl": widget_url
                            }
                        ]
                    else:
                        logger.warning("Não foi possível encontrar o iframe do widget")
                except Exception as e:
                    logger.error(f"Erro ao aguardar widget: {str(e)}")
                    # Capturar screenshot para debug
                    page.screenshot(path=f"./temp/widget_error_{session_id}.png")
                
                browser.close()
                
        except Exception as e:
            logger.error(f"Erro ao buscar voos: {str(e)}")
            
        return results

    def extract_flight_data(self, page):
        """
        Extrai dados de voos do widget
        
        Args:
            page: Objeto da página Playwright
            
        Returns:
            Lista de dados de voos extraídos
        """
        # Esta função precisará ser adaptada para a estrutura real do widget
        return page.evaluate("""
            () => {
                try {
                    // Buscar todos os frames
                    const frames = document.querySelectorAll('iframe');
                    if (!frames.length) return [];
                    
                    // Tentar encontrar frame do widget
                    let targetFrame = null;
                    for (const frame of frames) {
                        try {
                            if (frame.src.includes('tp.media')) {
                                targetFrame = frame;
                                break;
                            }
                        } catch (e) {}
                    }
                    
                    if (!targetFrame) return [];
                    
                    // Aqui precisaríamos acessar o conteúdo do iframe
                    // Isso pode ser bloqueado por políticas de segurança
                    
                    return [{
                        airline: 'Dados não disponíveis',
                        departure: 'Função em desenvolvimento',
                        arrival: 'Função em desenvolvimento',
                        price: 0,
                        currency: 'BRL',
                        bookingUrl: ''
                    }];
                } catch (e) {
                    console.error('Erro ao extrair dados:', e);
                    return [];
                }
            }
        """)
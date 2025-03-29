/**
 * NOVO PAINEL DE RESULTADOS DE VOOS REAIS
 * Implementação completamente nova e simplificada
 */
class FlightPanel {
    constructor() {
        // Elementos da DOM
        this.panel = null;
        this.overlay = null;
        this.toggleButton = null;
        this.contentArea = null;
        this.resultsContainer = null;
        
        // Estado
        this.isVisible = false;
        this.isLoading = false;
        this.sessionId = null;
        this.searchData = null;
        this.pollCount = 0;
        this.maxPolls = 10;
        
        // Inicialização
        this.init();
        
        // Disponibilizar globalmente
        window.flightPanel = this;
        console.log("Novo painel de voos inicializado com sucesso");
        
        // Timer para auto-mostrar o painel se houver flag no localStorage
        setTimeout(() => {
            const savedSession = localStorage.getItem('currentSessionId');
            const autoShow = localStorage.getItem('autoShowFlightPanel') === 'true';
            
            if (autoShow && savedSession) {
                console.log("🔄 Auto-show do painel ativado! Usando sessão salva:", savedSession);
                this.loadFlightData(savedSession);
            }
        }, 1000);
    }
    
    // Inicializar o painel
    init() {
        this.createPanel();
        this.createToggleButton();
        this.setupEventListeners();
        
        // O painel começa escondido por padrão
        this.hide();
    }
    
    // Criar a estrutura do painel
    createPanel() {
        // Se já existe, remover
        const existingPanel = document.querySelector('.flight-panel');
        if (existingPanel) {
            existingPanel.remove();
        }
        
        // Criar o painel
        this.panel = document.createElement('div');
        this.panel.className = 'flight-panel';
        this.panel.innerHTML = `
            <div class="flight-panel-header">
                <h2><i class="fas fa-plane"></i> Resultados de Voos Reais</h2>
                <div class="panel-controls">
                    <button class="refresh-btn" title="Atualizar resultados"><i class="fas fa-sync-alt"></i></button>
                    <button class="close-btn" title="Fechar painel"><i class="fas fa-times"></i></button>
                </div>
            </div>
            <div class="flight-panel-content">
                <div class="loading-container">
                    <div class="loading-animation">
                        <div class="plane-icon">
                            <i class="fas fa-plane"></i>
                        </div>
                        <div class="loading-text">Buscando voos reais...</div>
                    </div>
                </div>
            </div>
            <div class="flight-panel-footer">
                <div class="api-credit">Dados fornecidos pela API oficial Amadeus</div>
            </div>
        `;
        
        // Adicionar ao documento
        document.body.appendChild(this.panel);
        
        // Criar overlay para o modo móvel
        this.overlay = document.createElement('div');
        this.overlay.className = 'flight-panel-overlay';
        document.body.appendChild(this.overlay);
        
        // Adicionar CSS do painel se ainda não existe
        this.addPanelStyles();
    }
    
    // Adicionar estilos CSS para o painel
    addPanelStyles() {
        if (!document.getElementById('flight-panel-styles')) {
            const styles = document.createElement('style');
            styles.id = 'flight-panel-styles';
            styles.textContent = `
                .flight-panel {
                    position: fixed;
                    top: 60px;
                    right: -400px;
                    width: 380px;
                    height: calc(100vh - 70px);
                    background-color: #fff;
                    border-radius: 8px 0 0 8px;
                    box-shadow: -2px 0 15px rgba(0, 0, 0, 0.2);
                    display: flex;
                    flex-direction: column;
                    transition: right 0.3s ease;
                    z-index: 1000;
                    overflow: hidden;
                }
                
                .flight-panel.visible {
                    right: 0;
                }
                
                .flight-panel-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.5);
                    z-index: 999;
                    display: none;
                }
                
                .flight-panel-overlay.visible {
                    display: block;
                }
                
                .flight-panel-header {
                    padding: 15px;
                    background-color: #4a90e2;
                    color: #fff;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid #3a80d2;
                }
                
                .flight-panel-header h2 {
                    margin: 0;
                    font-size: 18px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .panel-controls {
                    display: flex;
                    gap: 10px;
                }
                
                .panel-controls button {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    font-size: 16px;
                    opacity: 0.8;
                    transition: opacity 0.2s;
                }
                
                .panel-controls button:hover {
                    opacity: 1;
                }
                
                .flight-panel-content {
                    flex: 1;
                    overflow-y: auto;
                    padding: 15px;
                }
                
                .flight-panel-footer {
                    padding: 10px;
                    background-color: #f5f5f5;
                    border-top: 1px solid #ddd;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }
                
                .toggle-panel-btn {
                    position: fixed;
                    top: 120px;
                    right: 0;
                    background-color: #4a90e2;
                    color: white;
                    border: none;
                    border-radius: 4px 0 0 4px;
                    padding: 10px 15px;
                    cursor: pointer;
                    box-shadow: -2px 2px 5px rgba(0, 0, 0, 0.1);
                    z-index: 999;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    transition: transform 0.3s ease;
                }
                
                .toggle-panel-btn.panel-visible {
                    transform: translateX(-400px);
                }
                
                .toggle-panel-btn:hover {
                    background-color: #3a80d2;
                }
                
                .loading-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 200px;
                    text-align: center;
                }
                
                .loading-animation {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 15px;
                }
                
                .plane-icon {
                    font-size: 36px;
                    color: #4a90e2;
                    animation: fly 2s infinite ease-in-out;
                }
                
                .loading-text {
                    font-size: 16px;
                    color: #666;
                }
                
                @keyframes fly {
                    0% { transform: translateY(0) rotate(10deg); }
                    50% { transform: translateY(-15px) rotate(-5deg); }
                    100% { transform: translateY(0) rotate(10deg); }
                }
                
                /* Estilos para os cards de voo */
                .flight-cards {
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }
                
                .flight-card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                }
                
                .flight-card:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                
                .flight-card-header {
                    background-color: #f8f9fa;
                    padding: 12px 15px;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .airline-info {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .airline-logo {
                    width: 24px;
                    height: 24px;
                    background-color: #ddd;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 12px;
                    color: #666;
                }
                
                .flight-price {
                    font-weight: bold;
                    color: #2c7be5;
                    font-size: 18px;
                }
                
                .flight-card-body {
                    padding: 15px;
                }
                
                .flight-route {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 15px;
                    position: relative;
                }
                
                .flight-route::after {
                    content: '';
                    position: absolute;
                    left: 10%;
                    right: 10%;
                    top: 50%;
                    height: 1px;
                    background-color: #ddd;
                    z-index: 1;
                }
                
                .flight-route::before {
                    content: '✈️';
                    position: absolute;
                    left: 50%;
                    top: 50%;
                    transform: translate(-50%, -50%);
                    z-index: 2;
                    background-color: white;
                    padding: 0 10px;
                }
                
                .flight-point {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    z-index: 2;
                    background-color: white;
                    padding: 0 10px;
                }
                
                .airport-code {
                    font-weight: bold;
                    font-size: 18px;
                }
                
                .flight-time {
                    font-size: 14px;
                    color: #666;
                }
                
                .flight-details {
                    display: flex;
                    justify-content: space-between;
                    padding-top: 10px;
                    border-top: 1px dashed #eee;
                }
                
                .flight-detail {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }
                
                .detail-label {
                    font-size: 12px;
                    color: #666;
                }
                
                .detail-value {
                    font-size: 14px;
                    font-weight: bold;
                }
                
                .flight-card-footer {
                    padding: 10px 15px;
                    border-top: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                }
                
                .flight-card-footer button {
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                
                .btn-details {
                    background-color: transparent;
                    border: 1px solid #4a90e2;
                    color: #4a90e2;
                }
                
                .btn-details:hover {
                    background-color: #f0f7ff;
                }
                
                .btn-book {
                    background-color: #4a90e2;
                    border: 1px solid #4a90e2;
                    color: white;
                }
                
                .btn-book:hover {
                    background-color: #3a80d2;
                }
                
                .no-results {
                    text-align: center;
                    padding: 30px;
                    color: #666;
                }
                
                .error-container {
                    text-align: center;
                    padding: 30px;
                    color: #e74c3c;
                }
                
                .retry-button {
                    background-color: #4a90e2;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-top: 15px;
                }
                
                .flight-details-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 2000;
                    opacity: 0;
                    visibility: hidden;
                    transition: opacity 0.3s, visibility 0.3s;
                }
                
                .flight-details-modal.visible {
                    opacity: 1;
                    visibility: visible;
                }
                
                .modal-content {
                    background-color: white;
                    border-radius: 8px;
                    width: 90%;
                    max-width: 600px;
                    max-height: 90vh;
                    overflow-y: auto;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                }
                
                .modal-header {
                    padding: 15px;
                    background-color: #4a90e2;
                    color: white;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .modal-header h3 {
                    margin: 0;
                }
                
                .modal-close {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 20px;
                    cursor: pointer;
                }
                
                .modal-body {
                    padding: 20px;
                }
                
                .modal-footer {
                    padding: 15px;
                    border-top: 1px solid #eee;
                    text-align: right;
                }
                
                /* Estilos para dispositivos móveis */
                @media (max-width: 767px) {
                    .flight-panel {
                        width: 90%;
                        right: -100%;
                    }
                    
                    .flight-panel.visible {
                        right: 0;
                    }
                    
                    .toggle-panel-btn.panel-visible {
                        transform: translateX(-90vw);
                    }
                }
            `;
            document.head.appendChild(styles);
        }
    }
    
    // Criar botão para mostrar/esconder o painel
    createToggleButton() {
        // Se já existe, remover
        const existingButton = document.querySelector('.toggle-panel-btn');
        if (existingButton) {
            existingButton.remove();
        }
        
        // Criar o botão
        this.toggleButton = document.createElement('button');
        this.toggleButton.className = 'toggle-panel-btn';
        this.toggleButton.innerHTML = '<i class="fas fa-plane"></i> Ver Voos';
        
        // Adicionar ao documento
        document.body.appendChild(this.toggleButton);
    }
    
    // Configurar listeners de eventos
    setupEventListeners() {
        // Toggle do painel
        this.toggleButton.addEventListener('click', () => this.toggle());
        
        // Botão de fechar
        this.panel.querySelector('.close-btn').addEventListener('click', () => this.hide());
        
        // Botão de atualizar
        this.panel.querySelector('.refresh-btn').addEventListener('click', () => {
            if (this.sessionId) {
                this.loadFlightResults(this.sessionId);
            }
        });
        
        // Click no overlay esconde o painel (mobile)
        this.overlay.addEventListener('click', () => this.hide());
        
        // Listener para o evento de mostrar resultados de voos (disparado pelo chat)
        document.addEventListener('showFlightResults', (event) => {
            console.log('Evento showFlightResults recebido:', event.detail);
            
            if (event.detail && event.detail.sessionId) {
                // Mostrar e carregar resultados
                this.show();
                this.loadFlightResults(event.detail.sessionId);
            }
        });
        
        // Listener para o evento de forçar abertura do painel (novo evento)
        document.addEventListener('forceOpenFlightPanel', (event) => {
            console.log('Evento forceOpenFlightPanel recebido:', event.detail);
            
            // Mostrar o painel independente de ter um ID de sessão
            this.show();
            
            // Se tiver ID de sessão, carregar resultados
            if (event.detail && event.detail.sessionId) {
                this.loadFlightResults(event.detail.sessionId);
            } else {
                // Se não tiver ID, mostrar mensagem específica
                this.showMessage('Aguardando consulta à API Amadeus...');
            }
        });
    }
    
    // Mostrar o painel
    show() {
        this.panel.classList.add('visible');
        this.overlay.classList.add('visible');
        this.toggleButton.classList.add('panel-visible');
        this.isVisible = true;
    }
    
    // Esconder o painel
    hide() {
        this.panel.classList.remove('visible');
        this.overlay.classList.remove('visible');
        this.toggleButton.classList.remove('panel-visible');
        this.isVisible = false;
    }
    
    // Alternar visibilidade do painel
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    // Mostrar loading
    showLoading() {
        this.isLoading = true;
        this.panel.querySelector('.flight-panel-content').innerHTML = `
            <div class="loading-container">
                <div class="loading-animation">
                    <div class="plane-icon">
                        <i class="fas fa-plane"></i>
                    </div>
                    <div class="loading-text">Buscando voos reais...</div>
                </div>
            </div>
        `;
    }
    
    // Mostrar mensagem genérica
    showMessage(message) {
        this.panel.querySelector('.flight-panel-content').innerHTML = `
            <div class="loading-container">
                <div class="loading-animation">
                    <div class="plane-icon">
                        <i class="fas fa-plane"></i>
                    </div>
                    <div class="loading-text">${message}</div>
                </div>
            </div>
        `;
    }
    
    // Mostrar erro
    showError(message) {
        this.isLoading = false;
        this.panel.querySelector('.flight-panel-content').innerHTML = `
            <div class="error-container">
                <i class="fas fa-exclamation-circle" style="font-size: 36px; margin-bottom: 15px;"></i>
                <p>${message}</p>
                ${this.sessionId ? `
                    <button class="retry-button" onclick="flightPanel.loadFlightResults('${this.sessionId}')">
                        <i class="fas fa-sync-alt"></i> Tentar Novamente
                    </button>
                ` : ''}
                <p style="margin-top: 20px; font-size: 14px;">Por favor, refaça sua pesquisa com a Avi.</p>
            </div>
        `;
    }
    
    // Mostrar que não há resultados
    showNoResults() {
        this.isLoading = false;
        this.panel.querySelector('.flight-panel-content').innerHTML = `
            <div class="no-results">
                <i class="fas fa-search" style="font-size: 36px; margin-bottom: 15px; color: #999;"></i>
                <p>Não encontramos voos disponíveis para sua pesquisa.</p>
                <p>Tente mudar as datas ou destinos da sua viagem.</p>
            </div>
        `;
    }
    
    // Carregar resultados de voos
    loadFlightResults(sessionId) {
        // Validar o ID de sessão
        if (!sessionId || sessionId === 'undefined' || sessionId === 'null') {
            console.error('ID de sessão inválido:', sessionId);
            this.showError('Não foi possível carregar os resultados. ID de sessão inválido.');
            return;
        }
        
        // Guardar o ID da sessão
        this.sessionId = sessionId;
        console.log(`Carregando resultados para sessão: ${sessionId}`);
        
        // Mostrar loading
        this.showLoading();
        
        // Fazer a requisição para a API
        fetch(`/api/flight_results/${sessionId}`)
            .then(response => {
                console.log('Resposta da API:', response.status);
                if (!response.ok) {
                    throw new Error(`Erro na resposta: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Dados recebidos:', data);
                this.searchData = data;
                this.renderFlightResults(data);
            })
            .catch(error => {
                console.error('Erro ao buscar resultados:', error);
                this.showError(`Não foi possível carregar os resultados: ${error.message}`);
            });
    }
    
    // Renderizar resultados de voos
    renderFlightResults(data) {
        this.isLoading = false;
        
        // Verificar erro
        if (data.error) {
            this.showError(data.error);
            return;
        }
        
        // Verificar se há ofertas
        const offers = data.data || [];
        if (!offers.length) {
            this.showNoResults();
            return;
        }
        
        // Exibir as ofertas de voo
        const content = this.panel.querySelector('.flight-panel-content');
        
        let html = `
            <div class="results-summary">
                <h3>Voos Encontrados (${offers.length})</h3>
                <p>Resultados reais da API Amadeus para sua busca:</p>
            </div>
            <div class="flight-cards">
        `;
        
        // Adicionar cada oferta
        offers.forEach((offer, index) => {
            try {
                // Extrair dados principais
                const itinerary = offer.itineraries[0];
                const firstSegment = itinerary.segments[0];
                const lastSegment = itinerary.segments[itinerary.segments.length - 1];
                
                // Dados de preço
                const price = parseFloat(offer.price.total).toFixed(2);
                const currency = offer.price.currency;
                
                // Duração do voo
                const duration = this.formatDuration(itinerary.duration);
                
                // Número de paradas
                const stops = itinerary.segments.length - 1;
                const stopsText = stops === 0 ? 'Voo direto' : 
                                 stops === 1 ? '1 conexão' : 
                                 `${stops} conexões`;
                
                // Construir card
                html += `
                    <div class="flight-card" data-offer-id="${offer.id}">
                        <div class="flight-card-header">
                            <div class="airline-info">
                                <div class="airline-logo">${firstSegment.carrierCode.substring(0, 2)}</div>
                                <span>${firstSegment.carrierCode}</span>
                            </div>
                            <div class="flight-price">${currency} ${price}</div>
                        </div>
                        <div class="flight-card-body">
                            <div class="flight-route">
                                <div class="flight-point departure">
                                    <div class="airport-code">${firstSegment.departure.iataCode}</div>
                                    <div class="flight-time">${this.formatTime(firstSegment.departure.at)}</div>
                                </div>
                                <div class="flight-point arrival">
                                    <div class="airport-code">${lastSegment.arrival.iataCode}</div>
                                    <div class="flight-time">${this.formatTime(lastSegment.arrival.at)}</div>
                                </div>
                            </div>
                            <div class="flight-details">
                                <div class="flight-detail">
                                    <span class="detail-label">Duração</span>
                                    <span class="detail-value">${duration}</span>
                                </div>
                                <div class="flight-detail">
                                    <span class="detail-label">Paradas</span>
                                    <span class="detail-value">${stopsText}</span>
                                </div>
                                <div class="flight-detail">
                                    <span class="detail-label">Data</span>
                                    <span class="detail-value">${this.formatDate(firstSegment.departure.at)}</span>
                                </div>
                            </div>
                        </div>
                        <div class="flight-card-footer">
                            <button class="btn-details" data-offer-id="${offer.id}">
                                <i class="fas fa-info-circle"></i> Detalhes
                            </button>
                            <button class="btn-book" data-offer-id="${offer.id}">
                                <i class="fas fa-ticket-alt"></i> Selecionar
                            </button>
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error(`Erro ao processar oferta ${index}:`, error);
            }
        });
        
        html += '</div>';
        content.innerHTML = html;
        
        // Adicionar eventos aos botões
        this.addButtonEvents();
    }
    
    // Adicionar eventos aos botões
    addButtonEvents() {
        // Botões de detalhes
        this.panel.querySelectorAll('.btn-details').forEach(button => {
            button.addEventListener('click', (e) => {
                const offerId = e.target.closest('.btn-details').dataset.offerId;
                this.showFlightDetails(offerId);
            });
        });
        
        // Botões de reserva
        this.panel.querySelectorAll('.btn-book').forEach(button => {
            button.addEventListener('click', (e) => {
                const offerId = e.target.closest('.btn-book').dataset.offerId;
                this.selectFlight(offerId);
            });
        });
    }
    
    // Mostrar detalhes do voo
    showFlightDetails(offerId) {
        if (!this.searchData || !this.searchData.data) {
            console.error('Dados de busca não disponíveis');
            return;
        }
        
        // Encontrar a oferta
        const offer = this.searchData.data.find(o => o.id === offerId);
        if (!offer) {
            console.error(`Oferta não encontrada: ${offerId}`);
            return;
        }
        
        // Extrair dados para o modal
        const itinerary = offer.itineraries[0];
        const segments = itinerary.segments;
        const price = parseFloat(offer.price.total).toFixed(2);
        const currency = offer.price.currency;
        
        // Criar modal
        const modal = document.createElement('div');
        modal.className = 'flight-details-modal';
        
        let segmentsHtml = '';
        segments.forEach((segment, index) => {
            const departure = segment.departure;
            const arrival = segment.arrival;
            const duration = this.formatDuration(segment.duration);
            
            segmentsHtml += `
                <div class="segment-card" style="margin-bottom: 15px; padding: 15px; border: 1px solid #eee; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div style="font-weight: bold;">${segment.carrierCode} ${segment.number}</div>
                        <div>Duração: ${duration}</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; position: relative;">
                        <div style="text-align: center; width: 30%;">
                            <div style="font-size: 18px; font-weight: bold;">${departure.iataCode}</div>
                            <div>${this.formatTime(departure.at)}</div>
                            <div style="font-size: 12px; color: #666;">${this.formatDate(departure.at)}</div>
                        </div>
                        <div style="flex-grow: 1; height: 1px; background-color: #ddd; position: relative;">
                            <i class="fas fa-plane" style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%) rotate(90deg);"></i>
                        </div>
                        <div style="text-align: center; width: 30%;">
                            <div style="font-size: 18px; font-weight: bold;">${arrival.iataCode}</div>
                            <div>${this.formatTime(arrival.at)}</div>
                            <div style="font-size: 12px; color: #666;">${this.formatDate(arrival.at)}</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Adicionar conexão se não for o último segmento
            if (index < segments.length - 1) {
                const connectionTime = this.calculateConnectionTime(
                    segment.arrival.at,
                    segments[index + 1].departure.at
                );
                
                segmentsHtml += `
                    <div style="text-align: center; margin: 10px 0; color: #666; padding: 5px; background-color: #f5f5f5; border-radius: 4px;">
                        <i class="fas fa-hourglass-half"></i> ${connectionTime} de conexão em ${segment.arrival.iataCode}
                    </div>
                `;
            }
        });
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Detalhes do Voo</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0 0 5px 0;">Preço Total</h4>
                                <div style="font-size: 24px; font-weight: bold; color: #4a90e2;">${currency} ${price}</div>
                            </div>
                            <div>
                                <span style="background-color: #4a90e2; color: white; padding: 5px 10px; border-radius: 4px;">
                                    ${segments.length - 1 === 0 ? 'Voo Direto' : (segments.length - 1) + ' Conexão(ões)'}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <h4>Itinerário Completo</h4>
                    ${segmentsHtml}
                </div>
                <div class="modal-footer">
                    <button class="btn-book" style="background-color: #4a90e2; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;" data-offer-id="${offerId}">
                        Selecionar Este Voo
                    </button>
                </div>
            </div>
        `;
        
        // Adicionar ao DOM
        document.body.appendChild(modal);
        
        // Mostrar com animação
        setTimeout(() => modal.classList.add('visible'), 10);
        
        // Eventos do modal
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.classList.remove('visible');
            setTimeout(() => modal.remove(), 300);
        });
        
        modal.querySelector('.btn-book').addEventListener('click', () => {
            this.selectFlight(offerId);
            modal.classList.remove('visible');
            setTimeout(() => modal.remove(), 300);
        });
    }
    
    // Selecionar um voo
    selectFlight(offerId) {
        if (!this.searchData || !this.searchData.data) {
            console.error('Dados de busca não disponíveis');
            return;
        }
        
        // Encontrar a oferta
        const offer = this.searchData.data.find(o => o.id === offerId);
        if (!offer) {
            console.error(`Oferta não encontrada: ${offerId}`);
            return;
        }
        
        console.log('Voo selecionado:', offer);
        
        // Esconder o painel
        this.hide();
        
        // Disparar evento para o chat
        document.dispatchEvent(new CustomEvent('flightSelected', {
            detail: {
                offerId: offerId,
                flightData: offer
            }
        }));
        
        // Adicionar mensagem ao chat
        this.addFlightSelectionMessage(offer);
    }
    
    // Adicionar mensagem de seleção de voo ao chat
    addFlightSelectionMessage(offer) {
        // Verificar se há função para adicionar mensagem
        if (typeof addMessage !== 'function') {
            console.error('Função addMessage não encontrada');
            return;
        }
        
        // Extrair dados principais
        const itinerary = offer.itineraries[0];
        const firstSegment = itinerary.segments[0];
        const lastSegment = itinerary.segments[itinerary.segments.length - 1];
        const price = parseFloat(offer.price.total).toFixed(2);
        const currency = offer.price.currency;
        
        // Criar mensagem
        const message = `
            <div class="selected-flight-message">
                <h4>✅ Voo Selecionado</h4>
                <p>
                    <strong>${firstSegment.departure.iataCode}</strong> → <strong>${lastSegment.arrival.iataCode}</strong><br>
                    Data: ${this.formatDate(firstSegment.departure.at)}<br>
                    Companhia: ${firstSegment.carrierCode}<br>
                    Preço: ${currency} ${price}
                </p>
                <p>Você gostaria de continuar com este voo ou verificar outras opções?</p>
            </div>
        `;
        
        // Adicionar ao chat
        addMessage(message, false);
    }
    
    // Calcular tempo de conexão
    calculateConnectionTime(arrivalTime, departureTime) {
        const arrival = new Date(arrivalTime);
        const departure = new Date(departureTime);
        
        const diffMs = departure - arrival;
        const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        if (diffHrs > 0) {
            return `${diffHrs}h ${diffMins}min`;
        } else {
            return `${diffMins}min`;
        }
    }
    
    // Formatar duração (PT2H30M -> 2h 30min)
    formatDuration(duration) {
        if (!duration) return '';
        
        const hourMatch = duration.match(/(\d+)H/);
        const minuteMatch = duration.match(/(\d+)M/);
        
        const hours = hourMatch ? parseInt(hourMatch[1]) : 0;
        const minutes = minuteMatch ? parseInt(minuteMatch[1]) : 0;
        
        if (hours > 0 && minutes > 0) {
            return `${hours}h ${minutes}min`;
        } else if (hours > 0) {
            return `${hours}h`;
        } else {
            return `${minutes}min`;
        }
    }
    
    // Formatar data e hora (2023-06-05T14:30:00 -> 14:30)
    formatTime(dateTimeString) {
        if (!dateTimeString) return '';
        
        try {
            const date = new Date(dateTimeString);
            return date.toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        } catch (error) {
            console.error('Erro ao formatar hora:', error);
            return dateTimeString;
        }
    }
    
    // Formatar apenas a data (2023-06-05T14:30:00 -> 05/06/2023)
    formatDate(dateTimeString) {
        if (!dateTimeString) return '';
        
        try {
            const date = new Date(dateTimeString);
            return date.toLocaleDateString('pt-BR');
        } catch (error) {
            console.error('Erro ao formatar data:', error);
            return dateTimeString;
        }
    }
}

// Inicializar o painel quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new FlightPanel();
});
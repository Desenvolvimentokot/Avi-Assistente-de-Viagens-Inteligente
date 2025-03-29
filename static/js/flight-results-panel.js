/**
 * Manipulador do painel de resultados de voos
 * Este componente é responsável por mostrar dados REAIS da API Amadeus
 * em um painel lateral durante a interação do chat
 */
class FlightResultsPanel {
    constructor() {
        this.panel = null;
        this.toggleButton = null;
        this.transitionOverlay = null;
        this.isActive = false;
        this.currentSessionId = null;
        this.selectedFlightData = null; // Para armazenar a escolha do usuário
        
        // Expor a instância globalmente para debug e acesso direto
        window.flightResultsPanel = this;
        
        console.log("Painel de resultados de voos inicializado - Instância global disponível");
        
        this.init();
        
        // Configurar armazenamento compartilhado
        this.setupSharedStorage();
    }

    init() {
        // Criar o painel no DOM se ainda não existir
        if (!document.querySelector('.flight-results-panel')) {
            this.createPanel();
        } else {
            this.panel = document.querySelector('.flight-results-panel');
        }
        
        // Criar o botão de toggle se ainda não existir
        if (!document.querySelector('.toggle-flight-panel-btn')) {
            this.createToggleButton();
        } else {
            this.toggleButton = document.querySelector('.toggle-flight-panel-btn');
        }
        
        // Criar overlay de transição
        if (!document.querySelector('.flight-transition-overlay')) {
            this.createTransitionOverlay();
        } else {
            this.transitionOverlay = document.querySelector('.flight-transition-overlay');
        }

        // Adicionar listener para eventos de mensagens que mostram o painel
        document.addEventListener('showFlightResults', (event) => {
            console.log('Evento showFlightResults recebido:', event.detail);
            if (event.detail && event.detail.sessionId) {
                // Mostrar overlay de transição antes de mostrar os resultados
                this.showTransitionMessage(() => {
                    this.loadAndShowResults(event.detail.sessionId);
                });
            }
        });
        
        // Adicionar listener para verificar mudanças no localStorage
        window.addEventListener('storage', (event) => {
            if (event.key === 'flightPanelState') {
                const state = JSON.parse(event.newValue || '{}');
                if (state.isActive !== undefined && state.isActive !== this.isActive) {
                    if (state.isActive) {
                        this.showPanel();
                    } else {
                        this.hidePanel();
                    }
                }
            }
        });
        
        // Restaurar estado anterior (se existir)
        this.restoreState();
    }
    
    setupSharedStorage() {
        // Criar objeto global para compartilhar dados entre componentes
        if (!window.flightSharedData) {
            window.flightSharedData = {
                selectedFlight: null,
                searchResults: null,
                lastSessionId: null
            };
        }
    }
    
    // Salvar estado no localStorage para persistência
    saveState() {
        const state = {
            isActive: this.isActive,
            sessionId: this.currentSessionId,
            selectedFlight: this.selectedFlightData
        };
        localStorage.setItem('flightPanelState', JSON.stringify(state));
        
        // Atualizar também o objeto compartilhado
        if (window.flightSharedData) {
            window.flightSharedData.selectedFlight = this.selectedFlightData;
            window.flightSharedData.lastSessionId = this.currentSessionId;
        }
    }
    
    // Restaurar estado do localStorage
    restoreState() {
        try {
            const savedState = JSON.parse(localStorage.getItem('flightPanelState') || '{}');
            if (savedState.isActive) {
                // Se estava ativo, mostrar novamente
                this.currentSessionId = savedState.sessionId;
                this.selectedFlightData = savedState.selectedFlight;
                
                // Se tivermos um ID de sessão, tentar carregar os dados novamente
                if (this.currentSessionId) {
                    this.loadAndShowResults(this.currentSessionId);
                } else {
                    this.showPanel();
                }
            }
            
            // Atualizar objeto compartilhado
            if (window.flightSharedData) {
                window.flightSharedData.selectedFlight = this.selectedFlightData;
                window.flightSharedData.lastSessionId = this.currentSessionId;
            }
        } catch (error) {
            console.error('Erro ao restaurar estado do painel:', error);
        }
    }
    
    // Criar botão flutuante para toggle do painel
    createToggleButton() {
        this.toggleButton = document.createElement('button');
        this.toggleButton.className = 'toggle-flight-panel-btn';
        this.toggleButton.innerHTML = '<i class="fas fa-plane"></i><span>Ver Voos</span>';
        
        // Adicionar ao body
        document.body.appendChild(this.toggleButton);
        
        // Adicionar evento de clique
        this.toggleButton.addEventListener('click', () => {
            this.togglePanel();
        });
    }
    
    // Criar overlay de transição
    createTransitionOverlay() {
        this.transitionOverlay = document.createElement('div');
        this.transitionOverlay.className = 'flight-transition-overlay';
        this.transitionOverlay.innerHTML = `
            <div class="flight-transition-message">
                <div class="flight-transition-icon">
                    <i class="fas fa-plane-departure"></i>
                </div>
                <h3>Buscando voos reais para você</h3>
                <p>A Avi está consultando a API Amadeus para encontrar as melhores opções de voos disponíveis para sua viagem. Os resultados serão exibidos em instantes.</p>
            </div>
        `;
        
        // Adicionar ao body
        document.body.appendChild(this.transitionOverlay);
    }
    
    // Mostrar mensagem de transição por alguns segundos antes de mostrar os resultados
    showTransitionMessage(callback) {
        this.transitionOverlay.classList.add('active');
        
        // Esconder após 2.5 segundos
        setTimeout(() => {
            this.transitionOverlay.classList.remove('active');
            if (callback) callback();
        }, 2500);
    }

    createPanel() {
        // Criar elemento do painel
        this.panel = document.createElement('div');
        this.panel.className = 'flight-results-panel';
        this.panel.innerHTML = `
            <div class="flight-results-header">
                <span>Resultados de Voos Reais</span>
                <button class="close-btn">&times;</button>
            </div>
            <div class="flight-results-content">
                <div class="loader-container">
                    <div class="loader"></div>
                </div>
            </div>
            <div class="flight-results-footer">
                <div>Dados fornecidos pela API oficial Amadeus</div>
                <div class="amadeus-badge">AMADEUS TRAVEL API</div>
            </div>
        `;

        // Adicionar ao body
        document.body.appendChild(this.panel);

        // Adicionar evento para fechar o painel
        this.panel.querySelector('.close-btn').addEventListener('click', () => {
            this.hidePanel();
        });
    }

    showPanel() {
        this.panel.classList.add('active');
        this.isActive = true;
        
        // Mostrar o botão de toggle
        if (this.toggleButton) {
            this.toggleButton.style.display = 'block';
            this.toggleButton.classList.add('panel-visible');
        }
        
        // Salvar o estado
        this.saveState();
    }

    hidePanel() {
        this.panel.classList.remove('active');
        this.isActive = false;
        
        // Reposicionar o botão de toggle
        if (this.toggleButton) {
            this.toggleButton.classList.remove('panel-visible');
        }
        
        // Salvar o estado
        this.saveState();
    }

    togglePanel() {
        if (this.isActive) {
            this.hidePanel();
        } else {
            this.showPanel();
        }
    }

    showLoading() {
        this.panel.querySelector('.flight-results-content').innerHTML = `
            <div class="loader-container">
                <div class="loader"></div>
                <div class="loading-message">Buscando melhores ofertas de voos</div>
                <div class="loading-steps">Consultando API Amadeus em tempo real...</div>
                <div class="loading-progress">
                    <div class="loading-progress-bar" id="loadingProgressBar"></div>
                </div>
            </div>
        `;
        
        // Animar a barra de progresso
        let progress = 0;
        this.loadingInterval = setInterval(() => {
            if (progress < 90) { // Só vai até 90% para mostrar que ainda está carregando
                progress += 5;
                const progressBar = document.getElementById('loadingProgressBar');
                if (progressBar) {
                    progressBar.style.width = progress + '%';
                }
            }
        }, 300);
    }

    showError(message) {
        this.panel.querySelector('.flight-results-content').innerHTML = `
            <div class="error-message">
                <p>${message || 'Ocorreu um erro ao buscar os resultados de voos.'}</p>
                <button class="flight-book-btn" onclick="flightResultsPanel.loadAndShowResults('${this.currentSessionId}')">
                    Tentar Novamente
                </button>
            </div>
        `;
    }

    showNoResults() {
        this.panel.querySelector('.flight-results-content').innerHTML = `
            <div class="no-results">
                <p>Não encontramos voos disponíveis para esta busca.</p>
                <p>Tente alterar os filtros ou datas de viagem.</p>
            </div>
        `;
    }

    loadAndShowResults(sessionId) {
        // Salvar o ID da sessão atual
        this.currentSessionId = sessionId;
        
        // Mostrar o painel e indicar carregamento
        this.showPanel();
        this.showLoading();
        
        console.log(`Buscando resultados de voos para a sessão ${sessionId}...`);
        
        // Chamar a API para obter os resultados de voo
        fetch(`/api/flight_results/${sessionId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erro de rede: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Resultados obtidos:', data);
                this.renderResults(data);
            })
            .catch(error => {
                console.error('Erro ao buscar resultados:', error);
                this.showError(error.message);
            });
    }

    renderResults(data) {
        // Limpar o intervalo de animação da barra de progresso
        if (this.loadingInterval) {
            clearInterval(this.loadingInterval);
            this.loadingInterval = null;
        }
        
        // Verificar se temos dados para mostrar
        if (data.error) {
            this.showError(data.error);
            return;
        }

        // Verificar se temos ofertas para mostrar
        const offers = data.data || [];
        if (offers.length === 0) {
            this.showNoResults();
            return;
        }

        // Preparar o conteúdo HTML
        let resultsHtml = `
            <h3>Voos Encontrados (${offers.length})</h3>
            <p>Resultados reais da API Amadeus:</p>
            <div class="flight-cards-container">
        `;

        // Adicionar cada oferta de voo
        offers.forEach(offer => {
            try {
                // Extrair informações de cada oferta
                const itinerary = offer.itineraries[0];
                const firstSegment = itinerary.segments[0];
                const lastSegment = itinerary.segments[itinerary.segments.length - 1];
                const price = offer.price.total;
                const currency = offer.price.currency;
                
                // Formatar a duração total
                const duration = this.formatDuration(itinerary.duration);
                
                // Contar o número de conexões
                const stops = itinerary.segments.length - 1;
                const stopsText = stops === 0 ? 'Voo Direto' : 
                                  stops === 1 ? '1 Conexão' : 
                                  `${stops} Conexões`;
                
                // Construir o card do voo
                resultsHtml += `
                    <div class="flight-card">
                        <div class="flight-card-header">
                            <div class="flight-airline">${firstSegment.carrierCode}</div>
                            <div class="flight-price">${currency} ${parseFloat(price).toFixed(2)}</div>
                        </div>
                        <div class="flight-card-body">
                            <div class="flight-route">
                                <div class="flight-segment">
                                    <div class="flight-city">${firstSegment.departure.iataCode}</div>
                                    <div class="flight-time">${this.formatDateTime(firstSegment.departure.at)}</div>
                                </div>
                                <div class="flight-segment">
                                    <div class="flight-city">${lastSegment.arrival.iataCode}</div>
                                    <div class="flight-time">${this.formatDateTime(lastSegment.arrival.at)}</div>
                                </div>
                            </div>
                            <div class="flight-duration">${duration}</div>
                            <div class="flight-stops">${stopsText}</div>
                        </div>
                        <div class="flight-card-footer">
                            <button class="flight-details-btn" data-offer-id="${offer.id}">Ver Detalhes</button>
                            <button class="flight-book-btn" data-offer-id="${offer.id}">Reservar</button>
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Erro ao processar oferta de voo:', error);
            }
        });

        // Fechar o container
        resultsHtml += `</div>`;

        // Atualizar o conteúdo do painel
        this.panel.querySelector('.flight-results-content').innerHTML = resultsHtml;

        // Adicionar eventos aos botões
        this.addButtonEvents();
    }

    addButtonEvents() {
        // Adicionar eventos aos botões de detalhes
        this.panel.querySelectorAll('.flight-details-btn').forEach(button => {
            button.addEventListener('click', (event) => {
                const offerId = event.target.getAttribute('data-offer-id');
                this.showFlightDetails(offerId);
            });
        });

        // Adicionar eventos aos botões de reserva
        this.panel.querySelectorAll('.flight-book-btn').forEach(button => {
            button.addEventListener('click', (event) => {
                const offerId = event.target.getAttribute('data-offer-id');
                this.bookFlight(offerId);
            });
        });
    }

    showFlightDetails(offerId) {
        // Encontrar a oferta correspondente
        fetch(`/api/flight_results/${this.currentSessionId}`)
            .then(response => response.json())
            .then(data => {
                const offers = data.data || [];
                const selectedOffer = offers.find(offer => offer.id === offerId);
                
                if (selectedOffer) {
                    // Salvar a oferta selecionada
                    this.selectedFlightData = selectedOffer;
                    this.saveState();
                    
                    // Atualizar objeto compartilhado
                    if (window.flightSharedData) {
                        window.flightSharedData.selectedFlight = selectedOffer;
                    }
                    
                    // Criar modal com detalhes do voo
                    this.showFlightDetailsModal(selectedOffer);
                    
                    // Disparar evento para informar o chat que um voo foi selecionado
                    document.dispatchEvent(new CustomEvent('flightSelected', {
                        detail: {
                            flightData: selectedOffer
                        }
                    }));
                }
            })
            .catch(error => {
                console.error('Erro ao buscar detalhes do voo:', error);
                alert('Não foi possível obter os detalhes deste voo. Tente novamente.');
            });
    }
    
    showFlightDetailsModal(flightData) {
        // Extrair informações do voo
        const itinerary = flightData.itineraries[0];
        const price = flightData.price.total;
        const currency = flightData.price.currency;
        
        // Criar modal com animação
        const modal = document.createElement('div');
        modal.className = 'flight-details-modal';
        modal.innerHTML = `
            <div class="flight-details-modal-content">
                <div class="flight-details-modal-header">
                    <h3>Detalhes do Voo</h3>
                    <button class="close-modal-btn">&times;</button>
                </div>
                <div class="flight-details-modal-body">
                    <div class="flight-details-price">
                        <span class="price-label">Preço Total:</span>
                        <span class="price-value">${currency} ${parseFloat(price).toFixed(2)}</span>
                    </div>
                    <div class="flight-itinerary">
                        <h4>Itinerário</h4>
                        <div class="flight-segments">
                            ${this.renderSegments(itinerary.segments)}
                        </div>
                    </div>
                </div>
                <div class="flight-details-modal-footer">
                    <button class="select-flight-btn" data-offer-id="${flightData.id}">Selecionar Este Voo</button>
                </div>
            </div>
        `;
        
        // Adicionar modal ao DOM
        document.body.appendChild(modal);
        
        // Adicionar evento de fechar
        modal.querySelector('.close-modal-btn').addEventListener('click', () => {
            modal.remove();
        });
        
        // Adicionar evento de seleção
        modal.querySelector('.select-flight-btn').addEventListener('click', () => {
            this.bookFlight(flightData.id);
            modal.remove();
        });
        
        // Exibir modal com animação
        setTimeout(() => {
            modal.style.opacity = '1';
        }, 50);
    }
    
    // Renderizar segmentos do voo
    renderSegments(segments) {
        let html = '';
        
        segments.forEach((segment, index) => {
            const departure = segment.departure;
            const arrival = segment.arrival;
            const duration = this.formatDuration(segment.duration);
            
            html += `
                <div class="flight-segment-details">
                    <div class="segment-header">
                        <span class="segment-airline">${segment.carrierCode} ${segment.number}</span>
                        <span class="segment-duration">${duration}</span>
                    </div>
                    <div class="segment-route">
                        <div class="segment-departure">
                            <div class="segment-airport">${departure.iataCode}</div>
                            <div class="segment-time">${this.formatDateTime(departure.at)}</div>
                        </div>
                        <div class="segment-arrow">→</div>
                        <div class="segment-arrival">
                            <div class="segment-airport">${arrival.iataCode}</div>
                            <div class="segment-time">${this.formatDateTime(arrival.at)}</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Adicionar indicador de conexão entre segmentos
            if (index < segments.length - 1) {
                const connectionTime = this.calculateConnectionTime(segment.arrival.at, segments[index + 1].departure.at);
                html += `
                    <div class="segment-connection">
                        <div class="connection-indicator">
                            <div class="connection-line"></div>
                            <div class="connection-dot"></div>
                        </div>
                        <div class="connection-info">
                            <span class="connection-airport">${arrival.iataCode}</span>
                            <span class="connection-time">${connectionTime} de conexão</span>
                        </div>
                    </div>
                `;
            }
        });
        
        return html;
    }
    
    // Calcular tempo de conexão entre segmentos
    calculateConnectionTime(arrivalTime, departureTime) {
        const arrival = new Date(arrivalTime);
        const departure = new Date(departureTime);
        
        const diffMs = departure - arrival;
        const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        return diffHrs > 0 ? `${diffHrs}h ${diffMins}m` : `${diffMins}m`;
    }

    bookFlight(offerId) {
        // Encontrar a oferta correspondente
        fetch(`/api/flight_results/${this.currentSessionId}`)
            .then(response => response.json())
            .then(data => {
                const offers = data.data || [];
                const selectedOffer = offers.find(offer => offer.id === offerId);
                
                if (selectedOffer) {
                    // Salvar a oferta selecionada
                    this.selectedFlightData = selectedOffer;
                    this.saveState();
                    
                    // Atualizar objeto compartilhado
                    if (window.flightSharedData) {
                        window.flightSharedData.selectedFlight = selectedOffer;
                    }
                    
                    // Fechar o painel
                    this.hidePanel();
                    
                    // Disparar evento para informar o chat que um voo foi selecionado
                    document.dispatchEvent(new CustomEvent('flightSelected', {
                        detail: {
                            flightData: selectedOffer,
                            message: "Voo selecionado com sucesso"
                        }
                    }));
                    
                    // Mostrar mensagem de confirmação
                    alert('Voo selecionado com sucesso! Agora você pode continuar a conversa com a Avi.');
                }
            })
            .catch(error => {
                console.error('Erro ao selecionar voo:', error);
                alert('Não foi possível selecionar este voo. Tente novamente.');
            });
    }

    // Utilitários para formatação
    formatDateTime(dateString) {
        const date = new Date(dateString);
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        
        return `${hours}:${minutes} · ${day}/${month}`;
    }

    formatDuration(durationString) {
        // Formato PT2H30M => 2h 30m
        const hours = durationString.match(/(\d+)H/);
        const minutes = durationString.match(/(\d+)M/);
        
        let formatted = '';
        if (hours && hours[1]) {
            formatted += `${hours[1]}h `;
        }
        if (minutes && minutes[1]) {
            formatted += `${minutes[1]}m`;
        }
        
        return formatted.trim();
    }
}

// Inicializar o painel quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Criar instância global
    window.flightResultsPanel = new FlightResultsPanel();
    console.log('Painel de resultados de voos inicializado');
});
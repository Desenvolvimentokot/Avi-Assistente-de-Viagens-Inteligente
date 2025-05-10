/**
 * Manipulador do painel de resultados de voos
 * Este componente é responsável por mostrar dados REAIS da API TravelPayouts
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

        // Esconder o painel inicialmente - não mostrar no carregamento da página
        this.hidePanel();

        // Animação de busca será criada quando necessário

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

        // NÃO restaurar estado - não queremos que o painel abra automaticamente
        // this.restoreState();
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
                    <i class="fas fa-plane-departure fa-bounce"></i>
                </div>
                <h3>Buscando voos reais para você</h3>
                <p>A Avi está consultando a API TravelPayouts para encontrar as melhores opções de voos disponíveis para sua viagem. Os resultados serão exibidos em instantes.</p>
            </div>
        `;

        // Adicionar CSS para o overlay
        if (!document.getElementById('flight-overlay-style')) {
            const style = document.createElement('style');
            style.id = 'flight-overlay-style';
            style.textContent = `
                .flight-transition-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 9999;
                    opacity: 0;
                    visibility: hidden;
                    transition: opacity 0.3s ease, visibility 0.3s ease;
                }

                .flight-transition-overlay.active {
                    opacity: 1;
                    visibility: visible;
                }

                .flight-transition-message {
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    max-width: 500px;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                    animation: messageAppear 0.5s ease;
                }

                .flight-transition-icon {
                    font-size: 48px;
                    color: #4a90e2;
                    margin-bottom: 20px;
                }

                @keyframes messageAppear {
                    from { transform: translateY(-30px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }

                .fa-bounce {
                    animation: bounce 1s infinite;
                }

                @keyframes bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-20px); }
                }
            `;
            document.head.appendChild(style);
        }

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
                <div>Dados fornecidos pela API oficial TravelPayouts</div>
                <div class="travelpayouts-badge">TRAVELPAYOUTS API</div>
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
                <div class="search-animation">
                    <div class="plane-container">
                        <div class="plane">
                            <i class="fas fa-plane"></i>
                        </div>
                        <div class="route-line"></div>
                    </div>
                </div>
                <div class="loading-message">Buscando melhores ofertas de voos</div>
                <div class="loading-steps">Consultando API TravelPayouts em tempo real...</div>
                <div class="loading-progress">
                    <div class="loading-progress-bar" id="loadingProgressBar"></div>
                </div>
            </div>
        `;

        // Adicionar CSS de animação para o avião
        if (!document.getElementById('plane-animation-style')) {
            const style = document.createElement('style');
            style.id = 'plane-animation-style';
            style.textContent = `
                .search-animation {
                    height: 120px;
                    position: relative;
                    margin: 30px 0;
                }
                .plane-container {
                    position: relative;
                    height: 60px;
                    width: 100%;
                }
                .route-line {
                    position: absolute;
                    top: 50%;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(to right, #e0e0e0, #4a90e2, #e0e0e0);
                    z-index: 1;
                }
                .plane {
                    position: absolute;
                    top: calc(50% - 15px);
                    left: 0;
                    font-size: 24px;
                    color: #4a90e2;
                    animation: fly-plane 3s infinite ease-in-out;
                    z-index: 2;
                }
                .plane i {
                    transform: rotate(45deg);
                }
                @keyframes fly-plane {
                    0% { left: 0; transform: translateY(0); }
                    25% { transform: translateY(-10px); }
                    50% { left: calc(100% - 25px); transform: translateY(0); }
                    75% { transform: translateY(10px); }
                    100% { left: 0; transform: translateY(0); }
                }
            `;
            document.head.appendChild(style);
        }

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

    // Método desativado - substituído por mensagem informativa
    loadTestResults() {
        // Mostrar o painel
        this.showPanel();

        console.log("Modo de teste desativado - apenas dados reais disponíveis");

        // Exibir mensagem explicativa diretamente sem fazer requisição
        this.showError(
            "Modo de teste desativado. O sistema Flai agora utiliza exclusivamente dados reais da API TravelPayouts. " +
            "Para ver resultados de voos, converse com a Avi e forneça detalhes sobre sua viagem."
        );
    }

    loadAndShowResults(sessionId) {
        // VERIFICAÇÃO E REGISTRO DETALHADO
        console.log("loadAndShowResults chamado com sessionId:", sessionId);
        console.log("Tipo do sessionId:", typeof sessionId);

        // Verificar se temos um sessionId válido
        if (!sessionId || sessionId === 'undefined' || sessionId === 'null') {
            console.warn("SessionId inválido, não podemos buscar resultados");

            // Tentar recuperar do localStorage como último recurso
            const savedSessionId = localStorage.getItem('currentSessionId');
            console.log("Tentando recuperar sessionId do localStorage:", savedSessionId);

            if (savedSessionId && savedSessionId !== 'undefined' && savedSessionId !== 'null') {
                console.log("Usando sessionId do localStorage:", savedSessionId);
                sessionId = savedSessionId;
            } else {
                // Se realmente não temos nenhum ID válido, mostrar erro
                this.showPanel();
                this.showError("Não é possível exibir resultados sem uma sessão válida. Por favor, refaça sua pesquisa com a Avi.");
                return;
            }
        }

        // Forçar remoção de overlay de transição se estiver visível
        if (this.transitionOverlay) {
            this.transitionOverlay.classList.remove('active');
        }

        // Salvar o ID da sessão atual
        this.currentSessionId = sessionId;

        // Salvar no localStorage também para persistência
        localStorage.setItem('currentSessionId', sessionId);
        console.log("Session ID salvo no localStorage:", sessionId);

        // Atualizar o objeto compartilhado
        if (window.flightSharedData) {
            window.flightSharedData.lastSessionId = sessionId;
        }

        // Mostrar o painel e indicar carregamento
        this.showPanel();
        this.showLoading();

        console.log(`Buscando resultados de voos para a sessão ${sessionId}...`);

        // Chamar a API para obter os resultados de voo
        fetch(`/api/flight_results/${sessionId}`)
            .then(response => {
                console.log("Resposta da API:", response.status, response.statusText);
                if (!response.ok) {
                    throw new Error(`Erro de rede: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Resultados obtidos:', data);
                // Guardar no objeto compartilhado
                if (window.flightSharedData) {
                    window.flightSharedData.searchResults = data;
                }
                this.renderResults(data);
            })
            .catch(error => {
                console.error('Erro ao buscar resultados:', error);
                this.showError(`Erro ao buscar resultados: ${error.message}. Por favor, tente novamente ou refaça sua pesquisa com a Avi.`);
            });
    }

    // Método centralizado para renderização de resultados (usado tanto pelos testes quanto pelos dados reais)
    renderFlightResults(data) {
        // Limpar o loader
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

        // Usar o método principal de renderização
        this.renderResults(data);
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
            <p>Resultados reais da API TravelPayouts:</p>
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

// Inicializar painel com uma sessão específica
function initFlightResultsPanel(sessionId) {
    console.log("Novo painel de voos inicializado com sucesso");

    if (!sessionId) {
        console.error("Session ID não fornecido para o painel de voos");
        displayErrorMessage("Erro de sessão: ID não fornecido");

        // Tentar recuperar do localStorage como fallback
        const savedSessionId = localStorage.getItem('flai_flight_session_id');
        if (savedSessionId) {
            console.log("Usando session ID do localStorage: " + savedSessionId);
            currentSessionId = savedSessionId;
            loadFlightResults(savedSessionId);
            return;
        }

        return;
    }

    // Salvar a sessão no localStorage para persistência
    localStorage.setItem('flai_flight_session_id', sessionId);

    currentSessionId = sessionId;
    console.log("Inicializando painel de voos com session ID: " + sessionId);
    loadFlightResults(sessionId);
}

// Carregar resultados de voos para a sessão atual
function loadFlightResults(sessionId) {
    const resultsContainer = document.getElementById('flight-results-container');
    const loadingSpinner = document.getElementById('flight-results-loading');

    if (!sessionId) {
        console.error("Tentativa de carregar resultados sem session ID");
        displayErrorMessage("Erro: ID de sessão não fornecido");
        return;
    }

    console.log("Carregando resultados para sessão: " + sessionId);

    if (loadingSpinner) loadingSpinner.style.display = 'flex';
    if (resultsContainer) resultsContainer.innerHTML = '';

    // Adicionar headers e método específico para garantir que seja uma requisição nova
    const requestOptions = {
        method: 'GET',
        headers: {
            'Cache-Control': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Session-ID': sessionId
        },
    };

    // Adicionar timestamp para evitar cache
    const timestamp = new Date().getTime();

    // Adicionar endpoint específico para a sessão com timestamp
    fetch(`/api/flight_results/${sessionId}?_=${timestamp}`, requestOptions)
        .then(response => {
            console.log("Status da resposta:", response.status);

            if (!response.ok) {
                throw new Error(`Erro ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (loadingSpinner) loadingSpinner.style.display = 'none';

            // Log para ajudar na depuração
            console.log(`Recebidos ${data.data?.length || 0} resultados da fonte: ${data.source || 'desconhecida'}`);

            if (data.error) {
                displayErrorMessage(data.error);
                return;
            }

            if (!data.data || data.data.length === 0) {
                displayErrorMessage("Não encontramos voos para sua busca. Tente outros parâmetros.");
                return;
            }

            // Salvar session ID se ele estiver nos dados recebidos
            if (data.session_id) {
                currentSessionId = data.session_id;
                localStorage.setItem('flai_flight_session_id', data.session_id);
            }

            displayFlightResults(data);
        })
        .catch(error => {
            console.error('Erro ao carregar resultados de voos:', error);
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            displayErrorMessage("Erro ao carregar resultados: " + error.message);

            // Tentar novamente após um tempo
            setTimeout(() => {
                console.log("Tentando novamente após erro...");
                loadFlightResults(sessionId);
            }, 5000);
        });
}

// Função auxiliar para exibir mensagens de erro
function displayErrorMessage(message) {
    console.error("Mensagem de erro:", message);
    // Implemente aqui a lógica para exibir a mensagem de erro no painel
}

// Função auxiliar para exibir os resultados de voos (implemente aqui a lógica para renderizar os dados)
function displayFlightResults(data) {
    console.log("Resultados de voos:", data);
    // Implemente aqui a lógica para exibir os resultados de voos no painel
}
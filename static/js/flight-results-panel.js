/**
 * Manipulador do painel de resultados de voos
 * Este componente é responsável por mostrar dados REAIS da API Amadeus
 * em um painel lateral durante a interação do chat
 */
class FlightResultsPanel {
    constructor() {
        this.panel = null;
        this.isActive = false;
        this.currentSessionId = null;
        this.init();
    }

    init() {
        // Criar o painel no DOM se ainda não existir
        if (!document.querySelector('.flight-results-panel')) {
            this.createPanel();
        } else {
            this.panel = document.querySelector('.flight-results-panel');
        }

        // Adicionar listener para eventos de mensagens que mostram o painel
        document.addEventListener('showFlightResults', (event) => {
            console.log('Evento showFlightResults recebido:', event.detail);
            if (event.detail && event.detail.sessionId) {
                this.loadAndShowResults(event.detail.sessionId);
            }
        });
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
    }

    hidePanel() {
        this.panel.classList.remove('active');
        this.isActive = false;
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
            </div>
        `;
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
        // Implementação futura para mostrar detalhes do voo
        console.log(`Mostrando detalhes do voo ${offerId}`);
        alert(`Detalhes do voo ${offerId} serão implementados em breve.`);
    }

    bookFlight(offerId) {
        // Implementação futura para iniciar o processo de reserva
        console.log(`Iniciando reserva do voo ${offerId}`);
        alert(`Processo de reserva para o voo ${offerId} será implementado em breve.`);
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
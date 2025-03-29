/**
 * Manipulador do painel de resultados de voos
 * Este componente é responsável por mostrar dados REAIS da API Amadeus
 * em um painel lateral durante a interação do chat
 */
class FlightResultsPanel {
    constructor() {
        this.panel = document.getElementById('flight-results-panel');
        this.resultsContainer = document.getElementById('flight-results-container');
        this.loadingIndicator = document.getElementById('flight-results-loading');
        this.errorContainer = document.getElementById('flight-results-error');
        this.closeButton = document.getElementById('close-flight-results');
        this.initialized = false;
        this.sessionId = null;

        // Inicializar evento de fechamento
        if (this.closeButton) {
            this.closeButton.addEventListener('click', () => this.hidePanel());
        }

        console.log("Painel de resultados de voos inicializado");

        // Tornar a instância globalmente acessível
        window.flightResultsPanel = this;
        console.log("Painel de resultados de voos inicializado - Instância global disponível");

        // Adicionar botão de teste para desenvolvimento
        this.addTestButton();
    }

    // Adiciona um botão de teste para abrir o painel (somente para desenvolvimento)
    addTestButton() {
        const testButton = document.createElement('button');
        testButton.textContent = 'Teste Painel Voos';
        testButton.style.position = 'fixed';
        testButton.style.bottom = '10px';
        testButton.style.right = '10px';
        testButton.style.zIndex = '9999';
        testButton.addEventListener('click', () => {
            this.showPanel(null);
        });
        document.body.appendChild(testButton);
        console.log("Botão de teste do painel de voos adicionado");
    }

    // Mostrar o painel lateral
    showPanel(sessionId) {
        if (!this.panel) {
            console.error("Elemento do painel não encontrado");
            return;
        }

        console.log("Recebido show_flight_results=true, mostrando painel lateral");

        this.sessionId = sessionId;
        this.panel.classList.add('visible');

        // Limpar conteúdo anterior
        this.resultsContainer.innerHTML = '';

        // Mostrar indicador de carregamento
        this.showLoading(true);
        this.showError(false);

        // Buscar dados de voos
        this.fetchFlightResults();
    }

    // Esconder o painel lateral
    hidePanel() {
        if (this.panel) {
            this.panel.classList.remove('visible');
        }
    }

    // Mostrar/esconder indicador de carregamento
    showLoading(show) {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = show ? 'flex' : 'none';
        }
    }

    // Mostrar/esconder mensagem de erro
    showError(show, message = '') {
        if (this.errorContainer) {
            this.errorContainer.style.display = show ? 'block' : 'none';
            if (show && message) {
                this.errorContainer.innerHTML = `<p>${message}</p>`;
            }
        }
    }

    // Buscar resultados de voos
    fetchFlightResults() {
        // Construir URL com o ID da sessão
        const url = `/api/flight_results/${this.sessionId || 'test'}`;

        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erro na requisição: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                this.showLoading(false);

                // Verificar se há erro na resposta
                if (data.error) {
                    this.showError(true, `${data.error}. ${data.details || ''}`);
                    console.error("Erro na API:", data.error);
                    return;
                }

                // Renderizar resultados
                this.renderFlightResults(data);
            })
            .catch(error => {
                this.showLoading(false);
                this.showError(true, `Falha ao carregar resultados: ${error.message}`);
                console.error("Erro ao buscar resultados de voos:", error);
            });
    }

    // Renderizar resultados de voos
    renderFlightResults(data) {
        // Limpar container
        this.resultsContainer.innerHTML = '';

        // Se não houver dados, mostrar mensagem
        if (!data || (!data.data && !data.best_prices)) {
            this.showError(true, "Nenhum resultado de voo encontrado.");
            return;
        }

        // Criar elemento para indicar se são dados reais ou simulados
        const statusBadge = document.createElement('div');
        statusBadge.className = 'data-status-badge';
        statusBadge.textContent = data.is_simulated ? 'Dados Simulados' : 'Dados Reais';
        statusBadge.style.backgroundColor = data.is_simulated ? '#ff9800' : '#4CAF50';
        statusBadge.style.color = 'white';
        statusBadge.style.padding = '4px 8px';
        statusBadge.style.borderRadius = '4px';
        statusBadge.style.fontWeight = 'bold';
        statusBadge.style.marginBottom = '10px';
        statusBadge.style.display = 'inline-block';
        this.resultsContainer.appendChild(statusBadge);

        // Determinar qual tipo de dados estamos exibindo
        if (data.data) {
            // Renderizar resultados de voos regulares
            this.renderRegularFlights(data.data);
        } else if (data.best_prices) {
            // Renderizar resultados de melhores preços
            this.renderBestPrices(data.best_prices, data.origin, data.destination, data.currency);
        }
    }

    // Renderizar voos regulares
    renderRegularFlights(flights) {
        // Título
        const title = document.createElement('h3');
        title.textContent = `${flights.length} opções de voo encontradas`;
        this.resultsContainer.appendChild(title);

        // Renderizar cada voo
        flights.forEach((flight, index) => {
            const flightCard = document.createElement('div');
            flightCard.className = 'flight-card';

            // Informações básicas
            let price = 'Preço não disponível';
            if (flight.price && flight.price.total) {
                price = `R$ ${parseFloat(flight.price.total).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
            }

            // Primeiro segmento para informações de partida/chegada
            let departureInfo = 'Informações não disponíveis';
            let arrivalInfo = '';

            if (flight.itineraries && flight.itineraries.length > 0 &&
                flight.itineraries[0].segments && flight.itineraries[0].segments.length > 0) {

                const firstSegment = flight.itineraries[0].segments[0];
                const lastSegment = flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1];

                if (firstSegment.departure && lastSegment.arrival) {
                    // Extrair origem
                    const originCode = firstSegment.departure.iataCode || '';
                    const departureDate = firstSegment.departure.at ? new Date(firstSegment.departure.at) : null;
                    const departureTimeStr = departureDate ?
                        `${departureDate.getHours().toString().padStart(2, '0')}:${departureDate.getMinutes().toString().padStart(2, '0')}` : '';

                    // Extrair destino
                    const destinationCode = lastSegment.arrival.iataCode || '';
                    const arrivalDate = lastSegment.arrival.at ? new Date(lastSegment.arrival.at) : null;
                    const arrivalTimeStr = arrivalDate ?
                        `${arrivalDate.getHours().toString().padStart(2, '0')}:${arrivalDate.getMinutes().toString().padStart(2, '0')}` : '';

                    // Duração total
                    const duration = flight.itineraries[0].duration || '';
                    const formattedDuration = duration.replace('PT', '').replace('H', 'h ').replace('M', 'm');

                    // Informação formatada
                    departureInfo = `${originCode} ${departureTimeStr} → ${destinationCode} ${arrivalTimeStr}`;
                    arrivalInfo = `Duração: ${formattedDuration} · ${flight.itineraries[0].segments.length > 1 ?
                        flight.itineraries[0].segments.length - 1 + ' conexão(ões)' : 'Voo direto'}`;
                }
            }

            // Companhia aérea
            let airlineInfo = 'Companhia não informada';
            if (flight.itineraries && flight.itineraries[0] && flight.itineraries[0].segments && flight.itineraries[0].segments[0]) {
                const carrierCode = flight.itineraries[0].segments[0].carrierCode || '';
                airlineInfo = carrierCode;
            }

            // Links de compra
            let purchaseLinks = '';
            if (flight.purchaseLinks && flight.purchaseLinks.length > 0) {
                purchaseLinks = '<div class="purchase-links"><h4>Comprar em:</h4><ul>';
                flight.purchaseLinks.forEach(link => {
                    purchaseLinks += `<li><a href="${link.url}" target="_blank" rel="noopener">${link.provider}</a></li>`;
                });
                purchaseLinks += '</ul></div>';
            }

            // Montar o HTML
            flightCard.innerHTML = `
                <div class="flight-header">
                    <div class="flight-airline">${airlineInfo}</div>
                    <div class="flight-price">${price}</div>
                </div>
                <div class="flight-route">
                    <div class="flight-route-main">${departureInfo}</div>
                    <div class="flight-route-info">${arrivalInfo}</div>
                </div>
                ${purchaseLinks}
            `;

            this.resultsContainer.appendChild(flightCard);
        });
    }

    // Renderizar melhores preços
    renderBestPrices(bestPrices, origin, destination, currency) {
        // Título
        const title = document.createElement('h3');
        title.textContent = `Melhores preços: ${origin || ''} → ${destination || ''}`;
        this.resultsContainer.appendChild(title);

        // Subtítulo
        const subtitle = document.createElement('p');
        subtitle.textContent = `${bestPrices.length} opções encontradas`;
        subtitle.style.marginBottom = '20px';
        this.resultsContainer.appendChild(subtitle);

        // Renderizar cada preço
        bestPrices.forEach((priceInfo, index) => {
            const priceCard = document.createElement('div');
            priceCard.className = 'price-card';

            // Formatar preço
            const formattedPrice = `R$ ${parseFloat(priceInfo.price).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;

            // Formatar data
            let dateStr = priceInfo.date || 'Data não disponível';
            try {
                if (priceInfo.date) {
                    const date = new Date(priceInfo.date);
                    dateStr = date.toLocaleDateString('pt-BR');
                }
            } catch (e) {
                console.error("Erro ao formatar data:", e);
            }

            // Informações da companhia aérea
            const airline = priceInfo.airline || 'Companhia não informada';

            // Detalhes de duração, conexão, etc.
            let detailsInfo = '';
            if (priceInfo.duration) {
                detailsInfo += `<div>Duração: ${priceInfo.duration}</div>`;
            }
            if (priceInfo.has_connection) {
                detailsInfo += `<div>Conexão: ${priceInfo.connection_airport || 'Sim'}</div>`;
                if (priceInfo.connection_time) {
                    detailsInfo += `<div>Tempo de conexão: ${priceInfo.connection_time}</div>`;
                }
            } else {
                detailsInfo += '<div>Voo direto</div>';
            }

            // Link de compra
            let purchaseLink = '';
            if (priceInfo.affiliate_link) {
                purchaseLink = `<a href="${priceInfo.affiliate_link}" target="_blank" rel="noopener" class="purchase-button">
                    Comprar em ${priceInfo.provider || 'site parceiro'}
                </a>`;
            }

            // Montar o HTML
            priceCard.innerHTML = `
                <div class="price-header">
                    <div class="price-date">${dateStr}</div>
                    <div class="price-value">${formattedPrice}</div>
                </div>
                <div class="price-details">
                    <div class="price-airline">${airline}</div>
                    <div class="price-info">
                        ${detailsInfo}
                    </div>
                </div>
                <div class="price-actions">
                    ${purchaseLink}
                </div>
            `;

            this.resultsContainer.appendChild(priceCard);
        });
    }
}

// Inicializar assim que o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    const panel = new FlightResultsPanel();

    // Escutar evento personalizado para mostrar o painel
    document.addEventListener('showFlightResults', (event) => {
        console.log("Evento showFlightResults recebido:", event.detail);
        if (panel) {
            panel.showPanel(event.detail?.sessionId);
        }
    });
});

// Função auxiliar para disparar evento de abertura do painel
function triggerFlightResultsPanel(sessionId) {
    const event = new CustomEvent('showFlightResults', {
        detail: { sessionId: sessionId }
    });
    document.dispatchEvent(event);
}
/**
 * flight-results-panel.js
 * Script para gerenciar o painel lateral de resultados de voos reais da API Amadeus
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elementos principais
    const flightResultsPanel = document.createElement('div');
    flightResultsPanel.id = 'flight-results-panel';
    flightResultsPanel.className = 'flight-results-panel';
    document.body.appendChild(flightResultsPanel);

    // Estado do painel
    let panelState = {
        isVisible: false,
        sessionId: null,
        flightResults: null,
        isLoading: false,
        error: null
    };

    // Render inicial do painel (oculto)
    renderPanel();

    /**
     * Método público para mostrar o painel e iniciar a busca
     * @param {string} sessionId ID da sessão de chat
     */
    window.showFlightResultsPanel = function(sessionId) {
        panelState.sessionId = sessionId;
        panelState.isVisible = true;
        panelState.isLoading = true;
        panelState.flightResults = null;
        panelState.error = null;
        
        renderPanel();
        fetchFlightResults(sessionId);
    };

    /**
     * Método público para ocultar o painel
     */
    window.hideFlightResultsPanel = function() {
        panelState.isVisible = false;
        renderPanel();
    };

    /**
     * Busca os resultados de voo da API
     * @param {string} sessionId ID da sessão de chat
     */
    function fetchFlightResults(sessionId) {
        fetch(`/api/flight_results/${sessionId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro ao buscar resultados de voo');
                }
                return response.json();
            })
            .then(data => {
                panelState.isLoading = false;
                if (data.error) {
                    panelState.error = data.error;
                } else {
                    panelState.flightResults = data;
                }
                renderPanel();
            })
            .catch(error => {
                console.error('Erro ao buscar resultados:', error);
                panelState.isLoading = false;
                panelState.error = 'Não foi possível obter os resultados. Tente novamente.';
                renderPanel();
            });
    }

    /**
     * Renderiza o painel com base no estado atual
     */
    function renderPanel() {
        if (!panelState.isVisible) {
            flightResultsPanel.style.display = 'none';
            return;
        }

        flightResultsPanel.style.display = 'block';
        let panelContent = '';

        // Construir cabeçalho do painel
        panelContent = `
            <div class="panel-header">
                <h2>Resultados Reais - Amadeus</h2>
                <button id="close-panel" class="close-panel-btn" title="Fechar painel">×</button>
            </div>
        `;

        // Conteúdo do painel com base no estado
        if (panelState.isLoading) {
            panelContent += `
                <div class="panel-loading">
                    <div class="loading-spinner"></div>
                    <p>Buscando voos reais na API Amadeus...</p>
                </div>
            `;
        } else if (panelState.error) {
            panelContent += `
                <div class="panel-error">
                    <div class="error-icon">⚠️</div>
                    <p>${panelState.error}</p>
                    <button id="retry-search" class="retry-btn">Tentar novamente</button>
                </div>
            `;
        } else if (panelState.flightResults) {
            // Verificar se temos resultados válidos
            if (panelState.flightResults.flights && panelState.flightResults.flights.length > 0) {
                panelContent += renderFlightResults(panelState.flightResults);
            } else if (panelState.flightResults.best_prices && panelState.flightResults.best_prices.length > 0) {
                panelContent += renderBestPrices(panelState.flightResults);
            } else {
                panelContent += `
                    <div class="panel-no-results">
                        <p>Nenhum resultado encontrado para esta busca.</p>
                        <p>Tente ajustar seus critérios de busca.</p>
                    </div>
                `;
            }
        } else {
            panelContent += `
                <div class="panel-empty">
                    <p>Nenhuma busca realizada.</p>
                </div>
            `;
        }

        flightResultsPanel.innerHTML = panelContent;

        // Adicionar event listeners
        if (panelState.isVisible) {
            document.getElementById('close-panel').addEventListener('click', () => {
                window.hideFlightResultsPanel();
            });

            if (panelState.error) {
                document.getElementById('retry-search').addEventListener('click', () => {
                    panelState.isLoading = true;
                    panelState.error = null;
                    renderPanel();
                    fetchFlightResults(panelState.sessionId);
                });
            }

            // Adicionar listeners para botões de compra se houver resultados
            if (panelState.flightResults) {
                const bookButtons = flightResultsPanel.querySelectorAll('.book-now-btn');
                bookButtons.forEach(button => {
                    button.addEventListener('click', (e) => {
                        const url = e.target.getAttribute('data-url');
                        if (url) {
                            window.open(url, '_blank');
                        }
                    });
                });

                // Listeners para filtros e ordenação
                const sortSelect = flightResultsPanel.querySelector('#sort-results');
                if (sortSelect) {
                    sortSelect.addEventListener('change', () => {
                        sortFlightResults(sortSelect.value);
                    });
                }
            }
        }
    }

    /**
     * Renderiza os resultados de voos específicos
     */
    function renderFlightResults(data) {
        const flights = data.flights;
        let html = `
            <div class="panel-tools">
                <div class="panel-filters">
                    <select id="sort-results" class="sort-select">
                        <option value="price">Ordenar por Preço</option>
                        <option value="duration">Ordenar por Duração</option>
                        <option value="departure">Ordenar por Horário de Partida</option>
                    </select>
                </div>
                <div class="panel-info">
                    <span class="results-count">${flights.length} voos encontrados</span>
                    <span class="results-timestamp">Atualizado: ${new Date().toLocaleTimeString()}</span>
                </div>
            </div>
            <div class="flight-results-list">
        `;

        // Adicionar cada voo
        flights.forEach((flight, index) => {
            const departureTime = new Date(flight.departure.time).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
            const arrivalTime = new Date(flight.arrival.time).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
            
            const price = parseFloat(flight.price.split(' ')[1]);
            const formattedPrice = price.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });

            const airline = flight.airline || 'Companhia Aérea';
            const flightNumber = flight.flight_number || '';
            const duration = flight.duration || '';
            
            html += `
                <div class="flight-card" data-flight-index="${index}">
                    <div class="flight-main-info">
                        <div class="flight-time">
                            <div class="departure-time">${departureTime}</div>
                            <div class="flight-duration">
                                <div class="duration-line"></div>
                                <div class="duration-text">${duration}</div>
                                <div class="duration-line"></div>
                            </div>
                            <div class="arrival-time">${arrivalTime}</div>
                        </div>
                        <div class="flight-route">
                            <div class="origin">${flight.departure.airport}</div>
                            <div class="destination">${flight.arrival.airport}</div>
                        </div>
                    </div>
                    <div class="flight-details">
                        <div class="airline-info">
                            <div class="airline-logo">
                                <img src="/static/img/airlines/${airline.toLowerCase().replace(/\s+/g, '-')}.png" 
                                     onerror="this.src='/static/img/airlines/default.png'" 
                                     alt="${airline}">
                            </div>
                            <div class="airline-name">${airline} ${flightNumber}</div>
                        </div>
                        <div class="stops-info">
                            <div class="stops-badge">${flight.segments > 1 ? `${flight.segments - 1} escala(s)` : 'Voo direto'}</div>
                        </div>
                    </div>
                    <div class="flight-price-section">
                        <div class="price">${formattedPrice}</div>
                        <button class="book-now-btn" data-url="${flight.booking_url || '#'}">
                            Reservar
                        </button>
                    </div>
                </div>
            `;
        });

        html += `</div>`;
        return html;
    }

    /**
     * Renderiza os resultados de melhores preços
     */
    function renderBestPrices(data) {
        const bestPrices = data.best_prices;
        let html = `
            <div class="panel-tools">
                <div class="panel-filters">
                    <select id="sort-results" class="sort-select">
                        <option value="price">Ordenar por Preço</option>
                        <option value="date">Ordenar por Data</option>
                    </select>
                </div>
                <div class="panel-info">
                    <span class="results-count">${bestPrices.length} datas encontradas</span>
                    <span class="results-timestamp">Atualizado: ${new Date().toLocaleTimeString()}</span>
                </div>
            </div>
            <div class="price-calendar">
                <h3>Calendário de Preços</h3>
                <div class="price-calendar-grid">
        `;

        // Criar grid de calendário de preços
        bestPrices.forEach((price, index) => {
            const dateObj = new Date(price.date);
            const formattedDate = dateObj.toLocaleDateString('pt-BR');
            const formattedPrice = price.price.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });

            const isCheapest = index === 0; // O primeiro é o mais barato

            html += `
                <div class="calendar-day ${isCheapest ? 'best-price' : ''}">
                    <div class="calendar-date">${formattedDate}</div>
                    <div class="calendar-price">${formattedPrice}</div>
                    <button class="book-now-btn small" data-url="${price.booking_url || '#'}">
                        ${isCheapest ? 'Melhor preço' : 'Reservar'}
                    </button>
                </div>
            `;
        });

        html += `
                </div>
            </div>
            <div class="best-price-highlight">
        `;

        // Destacar o melhor preço
        if (bestPrices.length > 0) {
            const bestPrice = bestPrices[0];
            const dateObj = new Date(bestPrice.date);
            const formattedDate = dateObj.toLocaleDateString('pt-BR');
            const formattedPrice = bestPrice.price.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });

            html += `
                <div class="best-price-card">
                    <div class="best-price-header">
                        <div class="best-price-badge">Melhor Preço</div>
                    </div>
                    <div class="best-price-content">
                        <div class="route-info">
                            <div class="origin-destination">
                                ${data.origin} → ${data.destination}
                            </div>
                            <div class="travel-date">
                                ${formattedDate}
                            </div>
                        </div>
                        <div class="price-info">
                            <div class="price-amount">${formattedPrice}</div>
                            <button class="book-now-btn" data-url="${bestPrice.booking_url || '#'}">
                                Reservar Agora
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        html += `</div>`;
        return html;
    }

    /**
     * Ordena os resultados de voos com base no critério selecionado
     */
    function sortFlightResults(criterion) {
        if (!panelState.flightResults) return;

        let results = panelState.flightResults;
        
        if (results.flights) {
            // Ordenar voos específicos
            switch (criterion) {
                case 'price':
                    results.flights.sort((a, b) => {
                        const priceA = parseFloat(a.price.split(' ')[1]);
                        const priceB = parseFloat(b.price.split(' ')[1]);
                        return priceA - priceB;
                    });
                    break;
                case 'duration':
                    results.flights.sort((a, b) => {
                        // Converter duração para minutos
                        const getDurationMinutes = (duration) => {
                            const match = duration.match(/PT(\d+)H(\d+)M/);
                            if (match) {
                                return parseInt(match[1]) * 60 + parseInt(match[2]);
                            }
                            return 0;
                        };
                        
                        return getDurationMinutes(a.duration) - getDurationMinutes(b.duration);
                    });
                    break;
                case 'departure':
                    results.flights.sort((a, b) => {
                        const timeA = new Date(a.departure.time).getTime();
                        const timeB = new Date(b.departure.time).getTime();
                        return timeA - timeB;
                    });
                    break;
            }
        } else if (results.best_prices) {
            // Ordenar melhores preços
            switch (criterion) {
                case 'price':
                    results.best_prices.sort((a, b) => a.price - b.price);
                    break;
                case 'date':
                    results.best_prices.sort((a, b) => {
                        const dateA = new Date(a.date).getTime();
                        const dateB = new Date(b.date).getTime();
                        return dateA - dateB;
                    });
                    break;
            }
        }
        
        // Re-renderizar o painel com os resultados ordenados
        renderPanel();
    }
});
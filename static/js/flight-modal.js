/**
 * Flight Modal
 * 
 * Script para gerenciar o modal de resultados de voos.
 * Este script substitui o redirecionamento para a página de resultados,
 * exibindo os resultados em um modal na mesma página.
 */

// Objeto global para o modal de voos
const FlightModal = {
    modal: null,
    resultsContainer: null,
    loadingSpinner: null,
    searchParams: null,
    initialized: false,
    currentRequest: null,

    /**
     * Inicializa o modal e os listeners de eventos
     */
    init: function() {
        console.log('[FlightModal] Inicializando...');
        
        // Verificar se já está inicializado
        if (this.initialized) {
            console.log('[FlightModal] Já inicializado, abortando.');
            return;
        }

        // Criar estrutura do modal se não existir
        if (!document.getElementById('flight-results-modal')) {
            this.createModalStructure();
        }

        // Obter referências aos elementos
        this.modal = document.getElementById('flight-results-modal');
        this.resultsContainer = document.getElementById('flight-modal-results');
        this.loadingSpinner = document.getElementById('flight-modal-loading');
        this.searchParams = document.getElementById('flight-modal-params');

        // Configurar event listeners para fechar o modal
        const closeElements = document.getElementsByClassName('flight-modal-close');
        for (let i = 0; i < closeElements.length; i++) {
            closeElements[i].addEventListener('click', () => this.close());
        }

        // Fechar o modal quando clicar fora dele
        window.addEventListener('click', (event) => {
            if (event.target === this.modal) {
                this.close();
            }
        });

        // Marcar como inicializado
        this.initialized = true;
        console.log('[FlightModal] Inicialização concluída.');
    },

    /**
     * Cria a estrutura HTML do modal e adiciona ao body
     */
    createModalStructure: function() {
        console.log('[FlightModal] Criando estrutura do modal...');
        const modalHTML = `
            <div id="flight-results-modal" class="flight-modal">
                <div class="flight-modal-content">
                    <div class="flight-modal-header">
                        <h2 class="flight-modal-title">Resultados de Voos</h2>
                        <span class="flight-modal-close">&times;</span>
                    </div>
                    <div class="flight-modal-body">
                        <div id="flight-modal-params" class="flight-modal-search-params mb-4">
                            <div class="row">
                                <div class="col-md-3">
                                    <strong>Origem:</strong> <span id="modal-origin-display"></span>
                                </div>
                                <div class="col-md-3">
                                    <strong>Destino:</strong> <span id="modal-destination-display"></span>
                                </div>
                                <div class="col-md-3">
                                    <strong>Data de ida:</strong> <span id="modal-departure-date-display"></span>
                                </div>
                                <div class="col-md-3">
                                    <strong>Passageiros:</strong> <span id="modal-passengers-display">1</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Resultados dos voos -->
                        <div id="flight-modal-results">
                            <!-- Preenchido via JavaScript -->
                        </div>
                        
                        <!-- Spinner de carregamento -->
                        <div class="flight-modal-loading" id="flight-modal-loading">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Carregando...</span>
                            </div>
                            <p class="mt-2">Buscando as melhores opções de voos para você...</p>
                        </div>
                    </div>
                    <div class="flight-modal-footer">
                        <button type="button" class="btn btn-secondary flight-modal-close">Fechar</button>
                    </div>
                </div>
            </div>
        `;
        
        // Adicionar ao body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        console.log('[FlightModal] Estrutura do modal criada.');
    },

    /**
     * Abre o modal e inicia a busca de voos com os parâmetros fornecidos
     * @param {Object} params - Parâmetros para busca de voos
     */
    open: function(params) {
        console.log('[FlightModal] Abrindo modal com parâmetros:', params);
        
        // Inicializar se necessário
        if (!this.initialized) {
            this.init();
        }
        
        // Abrir o modal
        this.modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Impedir rolagem do body

        // Atualizar parâmetros de busca exibidos
        document.getElementById('modal-origin-display').textContent = this.getAirportDisplayName(params.origin);
        document.getElementById('modal-destination-display').textContent = this.getAirportDisplayName(params.destination);
        document.getElementById('modal-departure-date-display').textContent = params.departureDate || '';
        document.getElementById('modal-passengers-display').textContent = (params.adults || 1) + ' adulto(s)';

        // Limpar resultados anteriores
        this.resultsContainer.innerHTML = '';

        // Mostrar spinner de carregamento
        this.loadingSpinner.style.display = 'block';

        // Iniciar busca de voos
        this.fetchFlights(params);
    },

    /**
     * Fecha o modal
     */
    close: function() {
        console.log('[FlightModal] Fechando modal...');
        if (this.modal) {
            this.modal.style.display = 'none';
            document.body.style.overflow = ''; // Restaurar rolagem do body
        }
        
        // Cancelar requisição atual se estiver em andamento
        if (this.currentRequest && typeof this.currentRequest.abort === 'function') {
            this.currentRequest.abort();
        }
    },

    /**
     * Busca resultados de voos usando os parâmetros fornecidos
     * @param {Object} params - Parâmetros para busca de voos
     */
    fetchFlights: function(params) {
        console.log('[FlightModal] Buscando voos com parâmetros:', params);
        
        // Cancelar requisição anterior se existir
        if (this.currentRequest && typeof this.currentRequest.abort === 'function') {
            this.currentRequest.abort();
        }

        // URL para API de resultados - o cookie flai_session_id será enviado automaticamente
        const url = `/amadeus-test`;
        
        // Fazer a requisição
        fetch(url)
            .then(response => {
                console.log('[FlightModal] Status da resposta:', response.status);
                return response.json();
            })
            .then(data => {
                // Ocultar spinner
                this.loadingSpinner.style.display = 'none';
                console.log('[FlightModal] Dados recebidos:', data);
                
                // Verificar se houve erro
                if (data.error) {
                    console.error('[FlightModal] Erro retornado pela API:', data.error);
                    this.showError(data.error);
                    return;
                }

                // Verificar se temos dados válidos
                if (!data.data || !Array.isArray(data.data) || data.data.length === 0) {
                    console.log('[FlightModal] Nenhum resultado encontrado');
                    this.showNoResults();
                    return;
                }

                // Renderizar resultados
                this.renderFlightResults(data.data);
            })
            .catch(error => {
                console.error('[FlightModal] Erro ao buscar voos:', error);
                this.loadingSpinner.style.display = 'none';
                this.showError('Erro ao buscar voos. Por favor, tente novamente.');
            });
    },

    /**
     * Renderiza a mensagem de erro no modal
     * @param {string} message - Mensagem de erro
     */
    showError: function(message) {
        console.error('[FlightModal] Erro:', message);
        this.resultsContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${message}
            </div>
        `;
    },

    /**
     * Renderiza a mensagem de nenhum resultado encontrado
     */
    showNoResults: function() {
        console.log('[FlightModal] Nenhum resultado encontrado');
        this.resultsContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Não encontramos voos para os critérios informados. Tente ajustar os filtros ou datas.
            </div>
        `;
    },

    /**
     * Renderiza os resultados de voos no modal
     * @param {Array} flights - Array de objetos de voos
     */
    renderFlightResults: function(flights) {
        console.log('[FlightModal] Renderizando resultados de voos...');
        this.resultsContainer.innerHTML = '';

        try {
            // Verificar se temos voos para renderizar
            if (!flights || flights.length === 0) {
                this.showNoResults();
                return;
            }

            console.log(`[FlightModal] Processando ${flights.length} ofertas de voos`);

            // Processando cada oferta de voo
            flights.forEach((flight, flightIndex) => {
                try {
                    // Verificar se o voo tem a estrutura de preço esperada
                    if (!flight.price || !flight.price.total) {
                        console.warn(`[FlightModal] Voo ${flightIndex} sem informação de preço válida:`, flight);
                        return;
                    }

                    // Verificar se o voo tem itinerários
                    if (!flight.itineraries || !Array.isArray(flight.itineraries) || flight.itineraries.length === 0) {
                        console.warn(`[FlightModal] Voo ${flightIndex} sem itinerários válidos:`, flight);
                        return;
                    }

                    // Criar card para a oferta
                    const flightCard = document.createElement('div');
                    flightCard.className = 'flight-modal-card mb-4';

                    const priceTotal = parseFloat(flight.price.total);
                    const currencyCode = flight.price.currency || 'BRL';

                    // Flag para viagem de ida e volta
                    const isRoundTrip = flight.itineraries.length > 1;

                    // Processando o voo de ida (itinerário 0)
                    const outboundItinerary = flight.itineraries[0];

                    // Verificar se o itinerário tem segmentos
                    if (!outboundItinerary || !outboundItinerary.segments || outboundItinerary.segments.length === 0) {
                        console.warn(`[FlightModal] Itinerário de ida do voo ${flightIndex} inválido`);
                        return;
                    }

                    const outboundSegments = outboundItinerary.segments;
                    const outboundFirstSegment = outboundSegments[0];
                    const outboundLastSegment = outboundSegments[outboundSegments.length - 1];

                    // Elementos de informação do voo
                    const departureDateTime = this.formatDateTime(outboundFirstSegment.departure.at);
                    const arrivalDateTime = this.formatDateTime(outboundLastSegment.arrival.at);
                    const originCode = outboundFirstSegment.departure.iataCode;
                    const destinationCode = outboundLastSegment.arrival.iataCode;
                    const duration = outboundItinerary.duration;
                    const formattedDuration = this.formatDuration(duration);
                    const stops = outboundSegments.length - 1;
                    const stopsText = this.getStopsText(stops);

                    // Extrair só a primeira companhia aérea como principal
                    const mainCarrier = outboundFirstSegment.carrierCode;

                    // Construir o HTML do card
                    flightCard.innerHTML = `
                        <div class="row p-3">
                            <div class="col-md-9">
                                <div class="row">
                                    <div class="col-md-1 text-center d-none d-md-block">
                                        <div class="airline-logo-placeholder rounded-circle bg-light d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                                            <span>${mainCarrier}</span>
                                        </div>
                                    </div>
                                    <div class="col-md-11">
                                        <div class="row">
                                            <!-- Partida -->
                                            <div class="col-5 col-md-3">
                                                <div class="flight-time">${departureDateTime.time}</div>
                                                <div class="flight-date">${departureDateTime.date}</div>
                                                <div class="airport-code">${originCode}</div>
                                                <div class="airport-name">${this.getAirportName(originCode)}</div>
                                            </div>
                                            
                                            <!-- Duração e escalas -->
                                            <div class="col-2 col-md-6">
                                                <div class="flight-duration">
                                                    <span class="duration-time">${formattedDuration}</span>
                                                </div>
                                                <div class="text-center">
                                                    <span class="stops">${stopsText}</span>
                                                </div>
                                            </div>
                                            
                                            <!-- Chegada -->
                                            <div class="col-5 col-md-3 text-md-end">
                                                <div class="flight-time">${arrivalDateTime.time}</div>
                                                <div class="flight-date">${arrivalDateTime.date}</div>
                                                <div class="airport-code">${destinationCode}</div>
                                                <div class="airport-name">${this.getAirportName(destinationCode)}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Preço e botão -->
                            <div class="col-md-3">
                                <div class="price-container">
                                    <div class="price">${this.formatPrice(priceTotal, currencyCode)}</div>
                                    <div class="text-muted small mb-2">${isRoundTrip ? 'Ida e volta' : 'Somente ida'}</div>
                                    <button class="flight-modal-select-btn" data-flight-id="${flight.id}" data-flight-index="${flightIndex}">Selecionar</button>
                                </div>
                            </div>
                        </div>
                    `;

                    // Adicionar evento ao botão de seleção
                    const selectBtn = flightCard.querySelector('.flight-modal-select-btn');
                    selectBtn.addEventListener('click', () => {
                        this.handleFlightSelection(flight, flightIndex);
                    });

                    // Adicionar o card ao container
                    this.resultsContainer.appendChild(flightCard);

                } catch (cardError) {
                    console.error(`[FlightModal] Erro ao processar voo ${flightIndex}:`, cardError);
                }
            });

        } catch (error) {
            console.error('[FlightModal] Erro ao renderizar resultados:', error);
            this.showError('Erro ao processar os resultados de voos.');
        }
    },

    /**
     * Trata a seleção de um voo pelo usuário
     * @param {Object} flight - Objeto do voo selecionado
     * @param {number} index - Índice do voo no array
     */
    handleFlightSelection: function(flight, index) {
        console.log(`[FlightModal] Voo selecionado: Índice ${index}, ID ${flight.id}`);
        
        // Formatar dados do voo para exibição/uso no chat
        const flightInfo = {
            id: flight.id,
            price: flight.price.total,
            currency: flight.price.currency,
            origin: flight.itineraries[0].segments[0].departure.iataCode,
            destination: flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1].arrival.iataCode,
            departure: flight.itineraries[0].segments[0].departure.at,
            arrival: flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1].arrival.at,
            carrier: flight.itineraries[0].segments[0].carrierCode
        };
        
        // Enviar mensagem para o chat
        this.addFlightSelectionToChat(flightInfo);
        
        // Fechar o modal
        this.close();
    },

    /**
     * Adiciona a seleção de voo ao chat como mensagem do usuário
     * @param {Object} flightInfo - Informações do voo selecionado
     */
    addFlightSelectionToChat: function(flightInfo) {
        try {
            // Verificar se estamos na página de chat
            const chatInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');
            
            if (!chatInput || !sendButton) {
                console.warn('[FlightModal] Elementos do chat não encontrados, não foi possível adicionar a seleção');
                return;
            }
            
            // Formatar mensagem para o chat
            const message = `Vou escolher esse voo de ${this.getAirportDisplayName(flightInfo.origin)} para ${this.getAirportDisplayName(flightInfo.destination)} por ${this.formatPrice(flightInfo.price, flightInfo.currency)}`;
            
            // Adicionar mensagem ao chat
            chatInput.value = message;
            sendButton.click();
            
            console.log('[FlightModal] Seleção de voo adicionada ao chat:', message);
        } catch (error) {
            console.error('[FlightModal] Erro ao adicionar seleção ao chat:', error);
        }
    },

    /**
     * Formata um valor numérico como preço
     * @param {number|string} price - Valor do preço
     * @param {string} currency - Código da moeda (padrão: BRL)
     * @return {string} - Preço formatado
     */
    formatPrice: function(price, currency = 'BRL') {
        return new Intl.NumberFormat('pt-BR', { 
            style: 'currency', 
            currency: currency 
        }).format(price);
    },

    /**
     * Formata uma string de data/hora ISO
     * @param {string} dateTimeStr - String de data/hora no formato ISO
     * @return {Object} - Objeto com tempo e data formatados
     */
    formatDateTime: function(dateTimeStr) {
        try {
            if (!dateTimeStr) {
                return { time: '--:--', date: '--/--/----' };
            }

            const date = new Date(dateTimeStr);

            if (isNaN(date.getTime())) {
                return { time: '--:--', date: '--/--/----' };
            }

            return {
                time: date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
                date: date.toLocaleDateString('pt-BR')
            };
        } catch (error) {
            console.error('[FlightModal] Erro ao formatar data/hora:', error);
            return { time: '--:--', date: '--/--/----' };
        }
    },

    /**
     * Formata a duração do voo a partir da string ISO 8601
     * @param {string} durationStr - String de duração no formato ISO 8601 (PT2H30M)
     * @return {string} - Duração formatada
     */
    formatDuration: function(durationStr) {
        try {
            if (!durationStr) return '--h--m';

            // Extrair horas e minutos da string PT2H30M
            const hoursMatch = durationStr.match(/([0-9]+)H/);
            const minutesMatch = durationStr.match(/([0-9]+)M/);
            
            const hours = hoursMatch ? parseInt(hoursMatch[1]) : 0;
            const minutes = minutesMatch ? parseInt(minutesMatch[1]) : 0;
            
            return `${hours}h${minutes > 0 ? minutes + 'm' : ''}`;
        } catch (error) {
            console.error('[FlightModal] Erro ao formatar duração:', error);
            return '--h--m';
        }
    },

    /**
     * Retorna o texto para o número de escalas
     * @param {number} stops - Número de escalas
     * @return {string} - Texto formatado
     */
    getStopsText: function(stops) {
        if (stops === 0) return 'Direto';
        if (stops === 1) return '1 escala';
        return `${stops} escalas`;
    },

    /**
     * Retorna o nome completo do aeroporto a partir do código IATA
     * @param {string} iataCode - Código IATA do aeroporto
     * @return {string} - Nome do aeroporto
     */
    getAirportName: function(iataCode) {
        // Esta função depende do objeto airportData definido globalmente
        if (typeof airportData !== 'undefined' && airportData[iataCode]) {
            return airportData[iataCode].city;
        }
        return iataCode;
    },

    /**
     * Retorna o nome formatado do aeroporto a partir do código IATA
     * @param {string} iataCode - Código IATA do aeroporto
     * @return {string} - Nome formatado do aeroporto
     */
    getAirportDisplayName: function(iataCode) {
        // Esta função depende do objeto airportData definido globalmente
        if (typeof airportData !== 'undefined' && airportData[iataCode]) {
            return `${airportData[iataCode].city} (${iataCode})`;
        }
        return iataCode;
    }
};

// Dados para mapeamento de códigos IATA (simplificado)
const airportData = {
    // Aeroportos brasileiros mais comuns
    "GRU": {"name": "Aeroporto Internacional de São Paulo/Guarulhos", "city": "São Paulo", "country": "Brasil"},
    "CGH": {"name": "Aeroporto de Congonhas", "city": "São Paulo", "country": "Brasil"},
    "VCP": {"name": "Aeroporto Internacional de Viracopos", "city": "Campinas", "country": "Brasil"},
    "SDU": {"name": "Aeroporto Santos Dumont", "city": "Rio de Janeiro", "country": "Brasil"},
    "GIG": {"name": "Aeroporto Internacional do Galeão", "city": "Rio de Janeiro", "country": "Brasil"},
    "BSB": {"name": "Aeroporto Internacional de Brasília", "city": "Brasília", "country": "Brasil"},
    "CNF": {"name": "Aeroporto Internacional de Confins", "city": "Belo Horizonte", "country": "Brasil"},
    "SSA": {"name": "Aeroporto Internacional de Salvador", "city": "Salvador", "country": "Brasil"},
    "REC": {"name": "Aeroporto Internacional do Recife", "city": "Recife", "country": "Brasil"},
    "FOR": {"name": "Aeroporto Internacional de Fortaleza", "city": "Fortaleza", "country": "Brasil"},
    "CWB": {"name": "Aeroporto Internacional de Curitiba", "city": "Curitiba", "country": "Brasil"},
    "POA": {"name": "Aeroporto Internacional de Porto Alegre", "city": "Porto Alegre", "country": "Brasil"},
    "FLN": {"name": "Aeroporto Internacional de Florianópolis", "city": "Florianópolis", "country": "Brasil"},
    "NAT": {"name": "Aeroporto Internacional de Natal", "city": "Natal", "country": "Brasil"},
    "BEL": {"name": "Aeroporto Internacional de Belém", "city": "Belém", "country": "Brasil"},
    "VIX": {"name": "Aeroporto de Vitória", "city": "Vitória", "country": "Brasil"},
    "AJU": {"name": "Aeroporto Internacional de Aracaju", "city": "Aracaju", "country": "Brasil"},
    "MCZ": {"name": "Aeroporto Internacional de Maceió", "city": "Maceió", "country": "Brasil"},
};

// Inicializar o modal quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    FlightModal.init();
});

document.addEventListener('DOMContentLoaded', function() {
    // Adicionar evento para o botão do mural de voos
    const flightsMuralButton = document.getElementById('openFlightsMuralButton');
    if (flightsMuralButton) {
        flightsMuralButton.addEventListener('click', function() {
            console.log("Botão do Mural de Voos clicado");

            // Verificar se temos o objeto global do painel
            if (window.flightResultsPanel) {
                // Mostrar o painel com o ID da sessão atual
                window.flightResultsPanel.showPanel();

                // FORÇA TESTE PRIMEIRO para garantir que algo seja exibido
                if (!sessionId) {
                    console.log("TESTE: Usando endpoint de teste por não ter sessionId");
                    window.flightResultsPanel.loadTestResults();
                    return;
                }

                // Se tivermos um ID de sessão, carregar resultados
                if (sessionId) {
                    console.log("Mostrando painel com sessionId:", sessionId);
                    // Salvar sessionId no localStorage para persistência
                    localStorage.setItem('currentSessionId', sessionId);
                    // Salvar no objeto do painel também
                    window.flightResultsPanel.currentSessionId = sessionId;
                    window.flightResultsPanel.loadAndShowResults(sessionId);
                } else {
                    console.log("Painel mostrado sem sessionId");
                    // Tentar restaurar do localStorage
                    const savedSessionId = localStorage.getItem('currentSessionId');
                    if (savedSessionId) {
                        console.log("Usando sessionId do localStorage:", savedSessionId);
                        window.flightResultsPanel.loadAndShowResults(savedSessionId);
                    } else {
                        // Último recurso: mostrar dados de teste
                        window.flightResultsPanel.loadTestResults();
                    }
                }
            } else {
                console.error("Painel de voos não está disponível, tentando inicializar");
                // Tentar inicializar manualmente
                window.flightResultsPanel = new FlightResultsPanel();
            }
        });
    } else {
        console.error("Botão do Mural de Voos não encontrado");
    }

    // Listener para evento de seleção de voo
    document.addEventListener('flightSelected', (event) => {
        console.log('Chat: Evento flightSelected recebido:', event.detail);

        if (event.detail && event.detail.flightData) {
            // Obter os dados do voo selecionado
            const flightData = event.detail.flightData;

            // Armazenar no contexto
            if (chatContext) {
                chatContext.selectedFlight = flightData;
            }

            // Se estiver aguardando seleção, adicionar mensagem confirmando
            const firstSegment = flightData.itineraries[0].segments[0];
            const lastSegment = flightData.itineraries[0].segments[flightData.itineraries[0].segments.length - 1];

            // Formatar mensagem com detalhes básicos do voo selecionado
            const message = `✅ Voo selecionado: ${firstSegment.carrierCode} de ${firstSegment.departure.iataCode} para ${lastSegment.arrival.iataCode} por ${flightData.price.currency} ${parseFloat(flightData.price.total).toFixed(2)}`;

            // Adicionar como mensagem do assistente
            addMessage(message, false);

            // Adicionar mensagem sugerindo continuar a conversa
            addMessage("Você pode me fazer perguntas específicas sobre este voo ou solicitar outras informações para sua viagem.", false);

            // Scroll para mostrar a mensagem
            scrollToBottom();
        }
    });
    // Elementos do DOM
    const chatMessages = document.querySelector('.chat-messages');
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const modeButtons = document.querySelectorAll('.mode-button');

    // Variáveis globais
    let chatMode = 'quick-search'; // Modo padrão
    let currentConversationId = null;
    let sessionId = null; // Para manter a sessão com o servidor
    let chatHistory = []; // Para manter o histórico da conversa
    let awaitingFlightSelection = false; // Flag para controlar se estamos esperando o usuário selecionar um voo
    let chatContext = {
        mode: 'quick-search',
        quickSearchStep: 0,
        quickSearchData: {},
        selectedFlight: null // Para armazenar os dados do voo selecionado
    };

    // Inicialização
    addWelcomeMessage();

    // Eventos
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }

    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Alternar entre modos de chat
    modeButtons.forEach(button => {
        button.addEventListener('click', () => {
            const mode = button.getAttribute('data-mode');
            if (mode && mode !== chatMode) {
                chatMode = mode;

                // Atualizar UI
                modeButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');

                // Resetar chat para o novo modo
                chatMessages.innerHTML = '';
                addWelcomeMessage();

                // Ocultar a explicação após primeiro clique
                const welcomeInfo = document.getElementById('welcome-options-info');
                if (welcomeInfo) welcomeInfo.style.display = 'none';

                // Alterar a cor de fundo se for planejamento completo
                if (mode === 'full-planning') {
                    document.querySelector('.chat-container').classList.add('planning-mode');
                } else {
                    document.querySelector('.chat-container').classList.remove('planning-mode');
                }

                // Atualizar contexto
                chatContext = {
                    mode: mode,
                    quickSearchStep: 0,
                    quickSearchData: {}
                };
            }
        });
    });

    // Funções principais
    function addWelcomeMessage() {
        const welcomeHTML = `
            <div class="message assistant-message">
                <div class="message-avatar">
                    <img src="/static/img/avi rosto chat.png" alt="Avi" style="width: 30px; height: 30px; border-radius: 50%;">
                </div>
                <div class="message-content">
                    <p>Olá! Eu sou Avi, sua assistente de viagens. Como posso ajudar você hoje?</p>
                    <div id="welcome-options-info">
                        <p>Escolha uma das opções acima:</p>
                        <ul>
                            <li><strong>Busca Rápida</strong>: Encontre passagens aéreas de forma simples e rápida.</li>
                            <li><strong>Planejamento Completo</strong>: Crie seu roteiro de viagem com voos, hotéis e atrações.</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;

        chatMessages.innerHTML = welcomeHTML;
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message === '') return;

        // Adiciona a mensagem do usuário à conversa
        addMessage(message, true);
        messageInput.value = '';

        // Atualiza o histórico local com a mensagem do usuário
        chatHistory.push({user: message});

        // Garantir que a área de chat rola para mostrar a mensagem enviada
        scrollToBottom();

        // Mostra o indicador de digitação
        showTypingIndicator();

        // Fazer a solicitação para o backend
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                mode: chatMode,
                session_id: sessionId,  // Envia o ID da sessão se existir
                history: chatHistory,   // Envia o histórico local
                conversationId: currentConversationId,
                context: chatContext
            })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();

            if (data.error) {
                addMessage('Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente.', false);
                console.log("Error response:", data.error);
                return;
            }

            // Armazena o session_id retornado pelo servidor
            if (data.session_id) {
                sessionId = data.session_id;
                console.log("Sessão ativa:", sessionId);
            }

            // Adicionar resposta ao chat
            addMessage(data.response, false);

            // Atualiza o histórico local com a resposta
            chatHistory.push({assistant: data.response});

            // Scroll para mostrar a nova mensagem
            scrollToBottom();

            // Verificar se estamos no estágio de busca de dados reais da Amadeus
            // O backend envia a flag "show_flight_results" quando deve exibir o painel lateral
            if (data.show_flight_results) {
                console.log("Recebido show_flight_results=true, mostrando painel lateral");

                // Garantir que temos uma sessão válida
                const sessionId = getChatSessionId();
                console.log("ID da sessão atual:", sessionId);

                // Aguardar a inicialização do painel e então mostrar resultados
                setTimeout(() => {
                    console.log('Executando disparo do evento de exibição do painel (timeout)');
                    // Verificar se o painel está inicializado
                    if (typeof flightResultsPanel !== 'undefined') {
                        const event = new CustomEvent('showFlightResults', {
                            detail: { sessionId: sessionId }
                        });
                        document.dispatchEvent(event);
                        console.log("Evento showFlightResults disparado com sessionId:", sessionId);
                    } else {
                        console.error("Painel de resultados de voos não inicializado!");
                        // Tentar inicializar o painel se não estiver disponível
                        if (typeof initFlightResultsPanel === 'function') {
                            initFlightResultsPanel();
                            setTimeout(() => {
                                const event = new CustomEvent('showFlightResults', {
                                    detail: { sessionId: sessionId }
                                });
                                document.dispatchEvent(event);
                                console.log("Evento showFlightResults disparado após inicialização, sessionId:", sessionId);
                            }, 300);
                        }
                    }
                }, 500);
            }

            // MANTÉM o código legado para compatibilidade com o sistema atual
            // Eventualmente este código será substituído completamente pelo painel lateral
            if (data.flight_data || data.best_prices_data) {
                addFlightOptions(data.flight_data, data.best_prices_data);
            }

            // Se houver link de compra direto, mostrar botão
            if (data.purchase_link) {
                addPurchaseLink(data.purchase_link);
            }
        })
        .catch(error => {
            console.log("Error getting chat response:", error);
            removeTypingIndicator();
            addMessage('Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente.', false);
        });
    }

    function addMessage(text, isUser = false) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(isUser ? 'user-message' : 'assistant-message');

        const contentContainer = document.createElement('div');
        contentContainer.classList.add('message-box');
        contentContainer.classList.add(isUser ? 'user' : 'assistant');

        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');

        // Processa o texto para manter formatação markdown básica
        if (!isUser) {
            // Converte markdown para HTML
            text = convertMarkdownHeaders(text);
            text = convertMarkdownBold(text);
            text = convertMarkdownItalic(text);
            text = convertMarkdownLists(text);
            contentElement.innerHTML = text;
        } else {
            contentElement.innerText = text;
        }

        contentContainer.appendChild(contentElement);
        messageElement.appendChild(contentContainer);
        chatMessages.appendChild(messageElement);

        // Garantir que o texto não fique na vertical
        if (isUser) {
            contentElement.style.whiteSpace = 'normal';
            contentElement.style.display = 'inline-block';
        }
    }

    // Funções para converter markdown básico para HTML
    function convertMarkdownHeaders(text) {
        return text.replace(/### (.*?)$/gm, '<h3>$1</h3>')
                  .replace(/## (.*?)$/gm, '<h2>$1</h2>')
                  .replace(/# (.*?)$/gm, '<h1>$1</h1>');
    }

    function convertMarkdownBold(text) {
        return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    }

    function convertMarkdownItalic(text) {
        return text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    function convertMarkdownLists(text) {
        return text.replace(/- (.*?)$/gm, '<ul><li>$1</li></ul>').replace(/<\/ul><ul>/g, '');
    }

    function addPurchaseLink(url) {
        const purchaseElement = document.createElement('div');
        purchaseElement.classList.add('purchase-link');
        purchaseElement.innerHTML = `
            <p>Quer comprar esta passagem? Clique no botão abaixo:</p>
            <a href="${url}" target="_blank" class="purchase-button">
                <i class="fas fa-shopping-cart"></i> Comprar Agora
            </a>
        `;

        chatMessages.appendChild(purchaseElement);
        scrollToBottom();
    }

    function addFlightOptions(flightData, bestPricesData) {
        // Se não tivermos dados de voos ou preços, não fazer nada
        if (!flightData && !bestPricesData) return;

        const flightOptionsElement = document.createElement('div');
        flightOptionsElement.classList.add('flight-options');

        let optionsHtml = '<div class="flight-options-container">';
        optionsHtml += '<h3>Opções de Voos para Sua Viagem</h3>';

        // Adicionar dois cards: Voo solicitado e Recomendação
        if (bestPricesData && bestPricesData.best_prices && bestPricesData.best_prices.length > 0) {
            // Organizar dados para os dois cartões
            const bestPrice = bestPricesData.best_prices[0]; // O melhor preço (menor)
            const requestedPrice = bestPricesData.best_prices.length > 1 ? bestPricesData.best_prices[1] : bestPricesData.best_prices[0];

            // Formatar datas
            const requestedDateObj = new Date(requestedPrice.date);
            const bestDateObj = new Date(bestPrice.date);

            const formattedRequestedDate = requestedDateObj.toLocaleDateString('pt-BR');
            const formattedBestDate = bestDateObj.toLocaleDateString('pt-BR');

            // Obter nomes dos locais
            const origin = requestedPrice.origin_info ? requestedPrice.origin_info.name : bestPricesData.origin;
            const destination = requestedPrice.destination_info ? requestedPrice.destination_info.name : bestPricesData.destination;

            // Códigos de aeroporto
            const originCode = requestedPrice.origin_info ? requestedPrice.origin_info.code : bestPricesData.origin;
            const destinationCode = requestedPrice.destination_info ? requestedPrice.destination_info.code : bestPricesData.destination;

            // Extrair mais informações se disponíveis
            const airline = requestedPrice.airline || '';
            const flightNumber = requestedPrice.flight_number || '';
            const departureTime = requestedPrice.departure_time || '';
            const arrivalTime = requestedPrice.arrival_time || '';
            const duration = requestedPrice.duration || '';

            // Criar o card para o voo solicitado
            optionsHtml += `
            <div class="flight-option-section">
                <div class="flight-option-header requested">
                    <div class="option-label">Voo Solicitado</div>
                </div>
                <div class="flight-card highlight">
                    <div class="flight-header">
                        <div class="flight-title">
                            <div class="flight-cities">${origin} (${originCode}) → ${destination} (${destinationCode})</div>
                            <div class="flight-date">${formattedRequestedDate}</div>
                        </div>
                        <div class="flight-price">R$ ${requestedPrice.price.toFixed(2)}</div>
                    </div>
                    <div class="flight-details">
                        ${airline ? `<div class="flight-airline"><strong>Companhia:</strong> ${airline} ${flightNumber}</div>` : ''}
                        ${departureTime && arrivalTime ? `
                            <div class="flight-time-info">
                                <span class="departure"><strong>Saída:</strong> ${departureTime}</span>
                                <span class="flight-arrow">→</span>
                                <span class="arrival"><strong>Chegada:</strong> ${arrivalTime}</span>
                                ${duration ? `<span class="duration"><strong>Duração:</strong> ${duration}</span>` : ''}
                            </div>` : ''
                        }
                        <div class="provider-info">
                            <span class="provider-name"><strong>Via:</strong> ${requestedPrice.provider || 'Agência'}</span>
                        </div>
                    </div>
                    <div class="flight-actions">
                        <a href="${requestedPrice.affiliate_link}" target="_blank" class="btn-purchase" title="Comprar esta passagem agora">
                            <i class="fas fa-shopping-cart"></i> Comprar Agora
                        </a>
                        <button class="btn-details" data-option="0" data-type="price" title="Ver mais detalhes sobre este voo">
                            <i class="fas fa-info-circle"></i> Detalhes
                        </button>
                    </div>
                </div>
            </div>`;

            // Mostrar o melhor preço apenas se for diferente do solicitado
            if (bestPrice.price < requestedPrice.price || bestPrice.date !== requestedPrice.date) {
                // Calcular a economia (em percentual)
                const savings = ((requestedPrice.price - bestPrice.price) / requestedPrice.price) * 100;
                const savingsPercentage = savings.toFixed(0);

                // Extrair mais informações do melhor preço se disponíveis
                const bestAirline = bestPrice.airline || '';
                const bestFlightNumber = bestPrice.flight_number || '';
                const bestDepartureTime = bestPrice.departure_time || '';
                const bestArrivalTime = bestPrice.arrival_time || '';
                const bestDuration = bestPrice.duration || '';

                optionsHtml += `
                <div class="flight-option-section">
                    <div class="flight-option-header recommended">
                        <div class="option-label">Melhor Oferta</div>
                        ${savings > 5 ? `<div class="savings-badge">Economia de ${savingsPercentage}%</div>` : ''}
                    </div>
                    <div class="flight-card">
                        <div class="flight-header">
                            <div class="flight-title">
                                <div class="flight-cities">${origin} (${originCode}) → ${destination} (${destinationCode})</div>
                                <div class="flight-date">${formattedBestDate}</div>
                            </div>
                            <div class="flight-price">R$ ${bestPrice.price.toFixed(2)}</div>
                        </div>
                        <div class="flight-details">
                            ${bestAirline ? `<div class="flight-airline"><strong>Companhia:</strong> ${bestAirline} ${bestFlightNumber}</div>` : ''}
                            ${bestDepartureTime && bestArrivalTime ? `
                                <div class="flight-time-info">
                                    <span class="departure"><strong>Saída:</strong> ${bestDepartureTime}</span>
                                    <span class="flight-arrow">→</span>
                                    <span class="arrival"><strong>Chegada:</strong> ${bestArrivalTime}</span>
                                    ${bestDuration ? `<span class="duration"><strong>Duração:</strong> ${bestDuration}</span>` : ''}
                                </div>` : ''
                            }
                            <div class="provider-info">
                                <span class="provider-name"><strong>Via:</strong> ${bestPrice.provider || 'Agência'}</span>
                            </div>
                        </div>
                        <div class="flight-actions">
                            <a href="${bestPrice.affiliate_link}" target="_blank" class="btn-purchase" title="Comprar esta passagem com economia">
                                <i class="fas fa-shopping-cart"></i> Comprar
                            </a>
                            <button class="btn-details" data-option="1" data-type="price" title="Ver mais detalhes sobre este voo">
                                <i class="fas fa-info-circle"></i> Detalhes
                            </button>
                        </div>
                    </div>
                </div>`;
            }
        }

        // Se tivermos dados específicos de voo, adicionar apenas o primeiro como alternativa
        else if (flightData && flightData.flights && flightData.flights.length > 0) {
            const flight = flightData.flights[0];

            // Formatar data/hora para exibição
            const departureTime = new Date(flight.departure.time);
            const arrivalTime = new Date(flight.arrival.time);
            const formattedDeparture = departureTime.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
            const formattedArrival = arrivalTime.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
            const formattedDate = departureTime.toLocaleDateString('pt-BR');

            optionsHtml += `
            <div class="flight-option-section">
                <div class="flight-option-header recommended">
                    <div class="option-label">Voo Disponível</div>
                </div>
                <div class="flight-card">
                    <div class="flight-header">
                        <div class="flight-title">
                            <div class="flight-cities">${flight.departure.airport} → ${flight.arrival.airport}</div>
                            <div class="flight-airline">${flight.airline}</div>
                        </div>
                        <div class="flight-price">R$ ${flight.price.toFixed(2)}</div>
                    </div>
                    <div class="flight-details">
                        <div class="flight-time">
                            <span class="departure"><strong>Saída:</strong> ${formattedDeparture}</span>
                            <span class="flight-arrow">→</span>
                            <span class="arrival"><strong>Chegada:</strong> ${formattedArrival}</span>
                            <span class="flight-date"><strong>Data:</strong> ${formattedDate}</span>
                        </div>
                    </div>
                    <div class="flight-actions">
                        <a href="${flight.affiliate_link}" target="_blank" class="btn-purchase">
                            <i class="fas fa-shopping-cart"></i> Comprar
                        </a>
                        <button class="btn-details" data-option="0" data-type="flight">
                            <i class="fas fa-info-circle"></i> Detalhes
                        </button>
                    </div>
                </div>
            </div>`;
        }

        optionsHtml += '</div>';
        flightOptionsElement.innerHTML = optionsHtml;

        chatMessages.appendChild(flightOptionsElement);

        // Adicionar event listeners para os botões de detalhes
        const detailButtons = flightOptionsElement.querySelectorAll('.btn-details');
        detailButtons.forEach(button => {
            button.addEventListener('click', () => {
                const optionType = button.getAttribute('data-type');
                const optionIndex = parseInt(button.getAttribute('data-option'));

                let selectedOption;
                if (optionType === 'price') {
                    selectedOption = bestPricesData.best_prices[optionIndex];
                    showFlightDetailsModal(selectedOption, bestPricesData);
                } else if (optionType === 'flight') {
                    selectedOption = flightData.flights[optionIndex];
                    showFlightDetailsModal(selectedOption, null, true);
                }
            });
        });

        scrollToBottom();
    }

    // Função para exibir modal com detalhes do voo
    function showFlightDetailsModal(flightData, bestPricesData, isFlightType = false) {
        // Verificar se os dados são simulados
        const isSimulated = flightData.is_simulated || 
                          (bestPricesData && bestPricesData.is_simulated);

        // Remover qualquer modal existente
        const existingModal = document.querySelector('.flight-details-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // Criar o modal
        const modalElement = document.createElement('div');
        modalElement.classList.add('flight-details-modal');

        // Determinar os dados a serem mostrados com base no tipo
        let origin, destination, departureDate, departureTime, arrivalTime, 
            airline, flightNumber, price, duration, connection, baggage;

        if (isFlightType) {
            // Para dados do tipo flight
            origin = flightData.departure.airport;
            destination = flightData.arrival.airport;

            const depTime = new Date(flightData.departure.time);
            const arrTime = new Date(flightData.arrival.time);

            departureDate = depTime.toLocaleDateString('pt-BR');
            departureTime = depTime.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
            arrivalTime = arrTime.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});

            airline = flightData.airline;
            flightNumber = flightData.flight_number || '';
            price = flightData.price.toFixed(2);
            duration = flightData.duration || '';
            connection = flightData.connection || 'Direto';
            baggage = flightData.baggage || '1 bagagem (até 23kg)';
        } else {
            // Para dados do tipo price
            origin = flightData.origin_info ? flightData.origin_info.name : bestPricesData.origin;
            destination = flightData.destination_info ? flightData.destination_info.name : bestPricesData.destination;

            const originCode = flightData.origin_info ? flightData.origin_info.code : bestPricesData.origin;
            const destinationCode = flightData.destination_info ? flightData.destination_info.code : bestPricesData.destination;

            const dateObj = new Date(flightData.date);
            departureDate = dateObj.toLocaleDateString('pt-BR');
            departureTime = flightData.departure_time || '';
            arrivalTime = flightData.arrival_time || '';

            airline = flightData.airline || '';
            flightNumber = flightData.flight_number || '';
            price = flightData.price.toFixed(2);
            duration = flightData.duration || '';

            connection = 'Direto';
            if (flightData.has_connection && flightData.connection_airport) {
                connection = `Conexão em ${flightData.connection_airport}`;
                if (flightData.connection_time) {
                    connection += ` (${flightData.connection_time})`;
                }
            }

            baggage = flightData.baggage_allowance || '1 bagagem (até 23kg)';
        }

        // Montar o HTML do modal
        // Verificar se há um aviso de dados simulados para adicionar
        let simulatedDataWarning = '';
        if (isSimulated) {
            simulatedDataWarning = `
                <div style="padding: 10px; background-color: #FFF3CD; color: #856404; 
                    border: 1px solid #FFEEBA; border-radius: 5px; margin: 10px 0; font-size: 12px;">
                    ⚠️ <strong>Nota:</strong> Os dados mostrados são ilustrativos. 
                    Estamos trabalhando para fornecer informações em tempo real.
                </div>
            `;
        }

        const modalHTML = `
            <div class="modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Detalhes do Voo</h2>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${isSimulated ? simulatedDataWarning : ''}
                        <div class="flight-info-section">
                            <h3>Informações do Voo</h3>
                            <div class="flight-route">
                                <div class="city-info origin">
                                    <div class="city-name">${origin}</div>
                                    <div class="city-code">${flightData.origin_info ? flightData.origin_info.code : bestPricesData.origin}</div>
                                </div>
                                <div class="route-line">
                                    <div class="route-duration">${duration}</div>
                                </div>
                                <div class="city-info destination">
                                    <div class="city-name">${destination}</div>
                                    <div class="city-code">${flightData.destination_info ? flightData.destination_info.code : bestPricesData.destination}</div>
                                </div>
                            </div>

                            <div class="flight-main-details">
                                <div class="detail-item">
                                    <div class="detail-label">Data</div>
                                    <div class="detail-value">${departureDate}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Horário</div>
                                    <div class="detail-value">${departureTime} - ${arrivalTime}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Duração</div>
                                    <div class="detail-value">${duration}</div>
                                </div>
                            </div>

                            <div class="flight-secondary-details">
                                <div class="detail-item">
                                    <div class="detail-label">Companhia Aérea</div>
                                    <div class="detail-value">${airline}</div>
                                </div>
                                ${flightNumber ? `
                                <div class="detail-item">
                                    <div class="detail-label">Número do Voo</div>
                                    <div class="detail-value">${flightNumber}</div>
                                </div>` : ''}
                                <div class="detail-item">
                                    <div class="detail-label">Conexão</div>
                                    <div class="detail-value">${connection}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Bagagem</div>
                                    <div class="detail-value">${baggage}</div>
                                </div>
                                ${flightData.aircraft ? `
                                <div class="detail-item">
                                    <div class="detail-label">Aeronave</div>
                                    <div class="detail-value">${flightData.aircraft}</div>
                                </div>` : ''}
                            </div>
                        </div>

                        <div class="price-section">
                            <div class="price-header">Preço Total</div>
                            <div class="price-value">R$ ${price}</div>
                            <div class="price-provider">via ${flightData.provider}</div>

                            <a href="${flightData.affiliate_link}" target="_blank" class="btn-modal-purchase">
                                <i class="fas fa-shopping-cart"></i> Comprar esta Passagem
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;

        modalElement.innerHTML = modalHTML;
        document.body.appendChild(modalElement);

        // Adicionar event listener para fechar o modal
        const closeButton = modalElement.querySelector('.modal-close');
        const overlay = modalElement.querySelector('.modal-overlay');

        closeButton.addEventListener('click', () => {
            modalElement.remove();
        });

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                modalElement.remove();
            }
        });
    }

    function showTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.classList.add('message', 'assistant-message', 'typing-indicator');

        const avatarElement = document.createElement('div');
        avatarElement.classList.add('message-avatar');
        avatarElement.innerHTML = '<img src="/static/img/avi rosto chat.png" alt="Avi" style="width: 30px; height: 30px; border-radius: 50%;">';

        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');
        contentElement.innerHTML = '<div class="typing-dots"><span>.</span><span>.</span><span>.</span></div>';

        typingElement.appendChild(avatarElement);
        typingElement.appendChild(contentElement);

        chatMessages.appendChild(typingElement);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Funções de carregamento e gerenciamento de dados
    function loadConversations() {
        fetch('/api/conversations')
        .then(response => response.json())
        .then(data => {
            // Implementação futura: exibir histórico de conversas
        })
        .catch(error => {
            console.error('Error loading conversations:', error);
        });
    }

    function loadUserProfile() {
        fetch('/api/user/profile')
        .then(response => response.json())
        .then(data => {
            // Implementação futura: carregar preferências do usuário
        })
        .catch(error => {
            console.error('Error loading profile:', error);
        });
    }

    function loadTravelPlans() {
        fetch('/api/travel-plans')
        .then(response => response.json())
        .then(data => {
            // Implementação futura: exibir planos de viagem salvos
        })
        .catch(error => {
            console.error('Error loading plans:', error);
        });
    }

    function startPriceMonitoring() {
        // Implementação futura: monitoramento de preços
        // Simulação básica
        setInterval(() => {
            checkPriceAlerts();
        }, 30000); // Verificar a cada 30 segundos (em produção seria mais espaçado)
    }

    function checkPriceAlerts() {
        // Simulação de verificação de preços
        fetch('/api/price-alerts/check')
        .then(response => response.json())
        .then(data => {            console.log('Verificando preços para ' + (data.monitored_offers || 0) + ' ofertas monitoradas');
            // Se houver alertas, notificar o usuário
            if (data.alerts && data.alerts.length > 0) {
                // Exibir alerta de preço
                data.alerts.forEach(alert => {
                    addPriceAlert(alert);
                });
            }
        })
        .catch(error => {
            // Silenciosamente ignorar erros na verificação de preços
        });
    }

    function addPriceAlert(alert) {
        // Adicionar alerta de preço ao chat
        const alertDiv = document.createElement('div');
        alertDiv.classList.add('price-alert');

        alertDiv.innerHTML = `
            <div class="alert-icon"><i class="fas fa-exclamation-circle"></i></div>
            <div class="alert-content">
                <div class="alert-title">Alerta de preço!</div>
                <div class="alert-message">${alert.message}</div>
                <button class="alert-action">Ver detalhes</button>
            </div>
        `;

        // Adicionar alerta como mensagem do bot
        addMessage('', false, alertDiv);
    }

    // Funções auxiliares
    function getAirlineName(carrierCode) {
        // Mapear códigos de companhias aéreas para nomes
        const airlines = {
            'LA': 'LATAM',
            'G3': 'GOL',
            'AD': 'Azul',
            'AA': 'American Airlines',
            'DL': 'Delta',
            'UA': 'United',
            'BA': 'British Airways',
            'LH': 'Lufthansa',
            'AF': 'Air France',
            'KL': 'KLM'
        };

        return airlines[carrierCode] || carrierCode;
    }

    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function formatTime(dateTimeStr) {
        // Formatar hora (ex: 15:30)
        const date = new Date(dateTimeStr);
        return date.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
    }

    function formatDateTime(dateTimeStr) {
        // Formatar data e hora (ex: 01/01/2023 15:30)
        const date = new Date(dateTimeStr);
        return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
    }

    function formatDuration(durationStr) {
        const hoursMatch = durationStr.match(/(\d+)H/);
        const minutesMatch = durationStr.match(/(\d+)M/);

        const hours = hoursMatch ? hoursMatch[1] + 'h ' : '';
        const minutes = minutesMatch ? minutesMatch[1] + 'min' : '';

        return hours + minutes;
    }

    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    function getBookingLink(type, code) {
        const baseLinks = {
            flight: {
                'LATAM': 'https://www.latamairlines.com',
                'GOL': 'https://www.voegol.com.br',
                'AZUL': 'https://www.voeazul.com.br',
                'default': 'https://www.google.com/flights'
            },
            hotel: {
                'Booking.com': 'https://www.booking.com',
                'Hoteis.com': 'https://www.hoteis.com',
                'default': 'https://www.booking.com'
            }
        };

        const links = baseLinks[type] || {};
        return links[code] || links['default'];
    }

    // Adicionar event listeners para itens da navegação
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            document.querySelectorAll('.nav-item').forEach(navItem => {
                navItem.classList.remove('active');
            });
            this.classList.add('active');

            // Implementação básica para navegação (a ser expandida no futuro)
            const itemText = this.querySelector('span').textContent.toLowerCase();
            if (itemText === 'chat') {
                // Já estamos na tela de chat, não fazer nada
            } else if (itemText === 'planos') {
                alert('Funcionalidade de Planos em desenvolvimento');
            } else if (itemText === 'perfil') {
                alert('Funcionalidade de Perfil em desenvolvimento');
            }
        });
    });

    // Adicionar event listener para o botão de nova conversa
    document.querySelector('.add-conversation').addEventListener('click', function() {
        // Limpar mensagens existentes
        chatMessages.innerHTML = '';

        // Resetar sessão e histórico
        sessionId = null;
        chatHistory = [];

        // Resetar ID de conversa e contexto
        currentConversationId = null;
        chatContext = {
            mode: chatMode,
            quickSearchStep: 0,
            quickSearchData: {}
        };

        // Adicionar mensagem de boas-vindas
        addWelcomeMessage();
    });

    // Função que garante o scroll automático no contêiner correto
    function scrollToBottom() {
        const chatContainer = document.querySelector('.chat-container');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Função para mostrar o painel de resultados de voos
    function showFlightResults(sessionId) {
        console.log("Chamando showFlightResults com sessionId:", sessionId);

        // Mostrar o painel imediatamente, mesmo sem ID de sessão
        if (window.flightResultsPanel) {
            // Se temos ID de sessão, carregamos os resultados
            if (sessionId) {
                window.flightResultsPanel.loadAndShowResults(sessionId);
            } else {
                // Caso contrário, apenas mostramos o painel com carregamento
                window.flightResultsPanel.showPanel();
                window.flightResultsPanel.showLoadingAnimation("Consultando API Amadeus...");

                // Salvar o estado atual da conversa para que o painel possa recuperá-lo depois
                localStorage.setItem('currentChatState', JSON.stringify({
                    messages: chatMessages,
                    currentSessionId: getCurrentSessionId()
                }));
            }
        } else {
            // Se o painel não estiver inicializado, tentar novamente após um breve atraso
            setTimeout(() => {
                if (window.flightResultsPanel) {
                    if (sessionId) {
                        window.flightResultsPanel.loadAndShowResults(sessionId);
                    } else {
                        window.flightResultsPanel.showPanel();
                        window.flightResultsPanel.showLoadingAnimation("Consultando API Amadeus...");
                    }
                } else {
                    console.error("Não foi possível mostrar o painel de resultados de voos");
                }
            }, 500);
        }
    }

    // Função para detectar busca de voos na mensagem do usuário
    function detectFlightSearchInMessage(message) {
        // Palavras-chave que indicam busca de voos
        const flightKeywords = [
            'voos', 'voo', 'passagem', 'passagens', 'voar para', 'viagem para',
            'avião', 'companhia aérea', 'amadeus', 'buscar voo'
        ];

        // Verificar se a mensagem contém alguma das palavras-chave
        const messageLower = message.toLowerCase();
        return flightKeywords.some(keyword => messageLower.includes(keyword.toLowerCase()));
    }

    // Start functions
    loadConversations();
    loadUserProfile();
    loadTravelPlans();
    startPriceMonitoring();
});

function getChatSessionId() {
    return sessionId;
}

function getCurrentSessionId() {
    return sessionId;
}
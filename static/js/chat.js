// Variáveis globais
let currentSessionId = null;
let typingTimer = null;
let conversationHistory = [];
let isTyping = false;
let isProcessing = false;
let promptIdCounter = 1;

// Inicialização após carregamento do DOM
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar a sessão
    initSession();

    // Definir eventos
    setupEventListeners();

    // Carregar histórico se existir
    loadChatHistory();
});

// Inicializar sessão
function initSession() {
    // Gerar um ID de sessão único se não existir
    currentSessionId = localStorage.getItem('flai_session_id');
    if (!currentSessionId) {
        currentSessionId = generateUUID();
        localStorage.setItem('flai_session_id', currentSessionId);
    }
    console.log("ID da sessão:", currentSessionId);
}

// Configurar event listeners
function setupEventListeners() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const resetButton = document.getElementById('reset-button');

    // Envio de mensagem pelo botão
    sendButton.addEventListener('click', function() {
        sendMessage();
    });

    // Envio de mensagem pelo Enter
    messageInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    // Limpar conversa
    resetButton.addEventListener('click', function() {
        resetChat();
    });

    // Exibir indicador de digitação
    messageInput.addEventListener('input', function() {
        updateTypingIndicator();
    });

    // Ouvir eventos de visibilidade para recarregar a conversa quando o usuário voltar
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden && conversationHistory.length === 0) {
            loadChatHistory();
        }
    });
    // Adicionar evento para o botão do mural de voos
    const flightsMuralButton = document.getElementById('openFlightsMuralButton');
    if (flightsMuralButton) {
        flightsMuralButton.addEventListener('click', function() {
            console.log("Botão do Mural de Voos clicado");

            // Verificar se temos o objeto global do painel
            if (window.flightResultsPanel) {
                // Mostrar o painel com o ID da sessão atual
                window.flightResultsPanel.showPanel(currentSessionId);
            } else {
                console.error("Painel de voos não está disponível, tentando inicializar");
                // Tentar inicializar manualmente (implementação faltando no código original)
                // ... (código para inicializar FlightResultsPanel se necessário)
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

            // Armazenar no contexto (não usado na versão editada, mas manter para compatibilidade)
            //if (chatContext) {
            //    chatContext.selectedFlight = flightData;
            //}

            // Se estiver aguardando seleção, adicionar mensagem confirmando
            const firstSegment = flightData.itineraries[0].segments[0];
            const lastSegment = flightData.itineraries[0].segments[flightData.itineraries[0].segments.length - 1];

            // Formatar mensagem com detalhes básicos do voo selecionado
            const message = `✅ Voo selecionado: ${firstSegment.carrierCode} de ${firstSegment.departure.iataCode} para ${lastSegment.arrival.iataCode} por ${flightData.price.currency} ${parseFloat(flightData.price.total).toFixed(2)}`;

            // Adicionar como mensagem do assistente
            appendMessage(message, 'assistant');

            // Adicionar mensagem sugerindo continuar a conversa
            appendMessage("Você pode me fazer perguntas específicas sobre este voo ou solicitar outras informações para sua viagem.", 'assistant');

            // Scroll para mostrar a mensagem
            scrollToBottom();
        }
    });

    //Alternar entre modos de chat (removido, falta implementação no código original)
     // ... (código para alternar modos de chat se necessário)
}


// Atualizar indicador de digitação
function updateTypingIndicator() {
    const messageInput = document.getElementById('message-input');
    const typingIndicator = document.getElementById('typing-indicator');

    if (messageInput.value.trim().length > 0) {
        typingIndicator.style.display = 'block';

        // Reset typing timer
        clearTimeout(typingTimer);
        typingTimer = setTimeout(function() {
            typingIndicator.style.display = 'none';
        }, 1000);
    } else {
        typingIndicator.style.display = 'none';
    }
}

// Função principal para enviar mensagem
function sendMessage() {
    if (isProcessing) return;

    const messageInput = document.getElementById('message-input');
    const userMessage = messageInput.value.trim();

    if (userMessage.length === 0) return;

    // Limpar campo de entrada
    messageInput.value = '';
    updateTypingIndicator();

    // Adicionar mensagem do usuário ao chat
    appendMessage(userMessage, 'user');

    // Salvar na história da conversa
    conversationHistory.push({
        role: 'user',
        content: userMessage
    });

    // Mostrar indicador de digitação do assistente
    showAssistantTyping(true);

    // Marcar como processando
    isProcessing = true;

    // Enviar para o backend
    sendToBackend(userMessage);
}

// Enviar mensagem para o backend
function sendToBackend(message) {
    const promptId = `prompt_${promptIdCounter++}`;

    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            message: message,
            prompt_id: promptId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erro na requisição: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("Resposta do servidor:", data);

        // Esconder indicador de digitação
        showAssistantTyping(false);

        // Processar a resposta
        processResponse(data);
    })
    .catch(error => {
        console.error('Erro ao enviar mensagem:', error);
        showAssistantTyping(false);
        isProcessing = false;

        // Mostrar mensagem de erro no chat
        appendMessage('Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.', 'assistant', 'error');
    });
}

// Processar resposta do backend
function processResponse(response) {
    if (!response) {
        console.error("Resposta vazia do servidor");
        isProcessing = false;
        return;
    }

    // Adicionar resposta ao chat
    if (response.response) {
        appendMessage(response.response, 'assistant');

        // Salvar na história da conversa
        conversationHistory.push({
            role: 'assistant',
            content: response.response
        });
    }

    // Verificar comandos especiais retornados pela API
    processCommands(response);

    // Salvar histórico no armazenamento local
    saveChatHistory();

    // Desativar flag de processamento
    isProcessing = false;
}

// Processar comandos especiais
function processCommands(response) {
    // Verificar se há comando para mostrar resultados de voos
    if (response.show_flight_results === true) {
        console.log("Executando disparo do evento de exibição do painel (timeout)");

        // Usar um pequeno timeout para garantir que o DOM já processou a resposta
        setTimeout(() => {
            // Disparar evento para o painel de resultados
            if (typeof triggerFlightResultsPanel === 'function') {
                triggerFlightResultsPanel(currentSessionId);
            } else if (window.flightResultsPanel) {
                window.flightResultsPanel.showPanel(currentSessionId);
            } else {
                console.error("Função triggerFlightResultsPanel não encontrada");
            }
        }, 100);
    }
    // MANTÉM o código legado para compatibilidade com o sistema atual
    // Eventualmente este código será substituído completamente pelo painel lateral
    if (response.flight_data || response.best_prices_data) {
        addFlightOptions(response.flight_data, response.best_prices_data);
    }

    // Se houver link de compra direto, mostrar botão
    if (response.purchase_link) {
        addPurchaseLink(response.purchase_link);
    }
}

// Adicionar mensagem ao chat
function appendMessage(message, sender, messageType = null) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    if (messageType) {
        messageElement.classList.add(messageType);
    }

    // Processar markdown na mensagem
    const processedMessage = processMarkdown(message);

    // Configurar avatar com base no remetente
    const avatarSrc = sender === 'user' ? '/static/img/user-avatar.png' : '/static/img/assistant-avatar.png';
    const avatarName = sender === 'user' ? 'Você' : 'Avi';

    // Construir HTML da mensagem
    messageElement.innerHTML = `
        <div class="avatar">
            <img src="${avatarSrc}" alt="${avatarName}">
            <span>${avatarName}</span>
        </div>
        <div class="content">${processedMessage}</div>
    `;

    // Adicionar ao container
    chatMessages.appendChild(messageElement);

    // Rolar para o final
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Processamento básico de Markdown
function processMarkdown(text) {
    // Links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

    // Negrito
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Itálico
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Listas não ordenadas
    text = text.replace(/^\s*-\s+(.+)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.+<\/li>\n?)+/g, '<ul>$&</ul>');

    // Quebras de linha
    text = text.replace(/\n/g, '<br>');

    return text;
}

// Mostrar/esconder indicador de digitação do assistente
function showAssistantTyping(show) {
    const chatMessages = document.getElementById('chat-messages');
    let typingElement = document.getElementById('assistant-typing');

    if (show) {
        if (!typingElement) {
            typingElement = document.createElement('div');
            typingElement.id = 'assistant-typing';
            typingElement.classList.add('message', 'assistant', 'typing');
            typingElement.innerHTML = `
                <div class="avatar">
                    <img src="/static/img/assistant-avatar.png" alt="Avi">
                    <span>Avi</span>
                </div>
                <div class="content">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            chatMessages.appendChild(typingElement);
        }
        typingElement.style.display = 'flex';
    } else if (typingElement) {
        typingElement.style.display = 'none';
    }

    // Rolar para o final
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Limpar o chat
function resetChat() {
    // Confirmar com o usuário
    if (!confirm('Tem certeza que deseja limpar a conversa?')) {
        return;
    }

    // Limpar histórico
    conversationHistory = [];

    // Limpar local storage
    localStorage.removeItem('flai_chat_history');

    // Gerar nova sessão
    currentSessionId = generateUUID();
    localStorage.setItem('flai_session_id', currentSessionId);

    // Limpar mensagens da interface
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';

    // Adicionar mensagem de boas-vindas
    setTimeout(() => {
        appendMessage('Olá! Sou a Avi, sua assistente de viagens. Como posso ajudar?', 'assistant');
    }, 300);
}

// Salvar histórico no armazenamento local
function saveChatHistory() {
    if (conversationHistory.length > 0) {
        localStorage.setItem('flai_chat_history', JSON.stringify(conversationHistory));
    }
}

// Carregar histórico do armazenamento local
function loadChatHistory() {
    const chatHistory = localStorage.getItem('flai_chat_history');

    if (chatHistory) {
        try {
            conversationHistory = JSON.parse(chatHistory);

            // Limpar mensagens atuais
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = '';

            // Recriar mensagens da conversa
            conversationHistory.forEach(message => {
                appendMessage(message.content, message.role);
            });
        } catch (error) {
            console.error('Erro ao carregar histórico do chat:', error);
        }
    } else {
        // Mostrar mensagem de boas-vindas se não houver histórico
        appendMessage('Olá! Sou a Avi, sua assistente de viagens. Como posso ajudar?', 'assistant');
    }
}

// Gerar UUID para sessão
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
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

    const chatMessages = document.getElementById('chat-messages');
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

function addPurchaseLink(url) {
    const purchaseElement = document.createElement('div');
    purchaseElement.classList.add('purchase-link');
    purchaseElement.innerHTML = `
        <p>Quer comprar esta passagem? Clique no botão abaixo:</p>
        <a href="${url}" target="_blank" class="purchase-button">
            <i class="fas fa-shopping-cart"></i> Comprar Agora
        </a>
    `;

    const chatMessages = document.getElementById('chat-messages');
    chatMessages.appendChild(purchaseElement);
    scrollToBottom();
}

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


function scrollToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Funções originais mantidas (a serem revisadas e possivelmente integradas melhor)
document.addEventListener('DOMContentLoaded', function() {
    // ... (rest of the original code, except for sendMessage and related functions)
    // ...  This part needs to be carefully integrated.  The existing functions like addMessage, addFlightOptions, etc.
    // ...  should be integrated with the new structure, keeping their functionality.  Also, functions like
    // ...  addWelcomeMessage can be removed or adapted to the new appendMessage structure.  The event listeners
    // ...  for navigation items should be preserved.   The rest of the original code requires careful consideration for integration.
});

function getChatSessionId() {
    return sessionId;
}

function getCurrentSessionId() {
    return sessionId;
}

function addWelcomeMessage() {
    appendMessage('Olá! Sou a Avi, sua assistente de viagens. Como posso ajudar?', 'assistant');
}

function addMessage(text, isUser = false, customElement = null) {
    appendMessage(text, isUser ? 'user' : 'assistant');
    if (customElement) {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.appendChild(customElement);
        scrollToBottom();
    }
}

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
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';

    // Resetar sessão e histórico
    currentSessionId = generateUUID();
    localStorage.setItem('flai_session_id', currentSessionId);
    conversationHistory = [];

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

// Controle para evitar múltiplas requisições
let flightSearchInProgress = false;

// Exibir resultados de voos quando solicitado
function showFlightResults(sessionId) {
    // Evitar múltiplas chamadas simultâneas
    if (flightSearchInProgress) {
        console.log("Busca de voos já em andamento. Ignorando solicitação duplicada.");
        return;
    }

    console.log("Recebido show_flight_results=true, mostrando painel lateral");
    flightSearchInProgress = true;

    // Mostrar o painel lateral
    document.getElementById('flight-results-panel').classList.add('show');

    // Mostrar mensagem de busca em andamento
    const loadingMessage = document.createElement('div');
    loadingMessage.className = 'chat-message system';
    loadingMessage.innerHTML = `
        <div class="message-content">
            <p><em>🔍 Consultando API Amadeus. Por favor, aguarde enquanto buscamos as melhores opções de voos para você...</em></p>
        </div>
    `;
    document.getElementById('chat-messages').appendChild(loadingMessage);

    // Dar um pequeno delay para garantir que o painel seja exibido antes de carregar os resultados
    setTimeout(() => {
        console.log("Executando disparo do evento de exibição do painel (timeout)");
        // Disparar evento personalizado para notificar o painel que deve carregar os resultados
        const event = new CustomEvent('showFlightResults', {
            detail: { sessionId: sessionId }
        });
        document.dispatchEvent(event);

        // Após 5 segundos, permitir novas buscas (tempo suficiente para que a primeira requisição seja processada)
        setTimeout(() => {
            flightSearchInProgress = false;
        }, 5000);
    }, 300);
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

// Funções auxiliares mantidas do código original

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
    .then(data => {
        console.log('Verificando preços para ' + (data.monitored_offers || 0) + ' ofertas monitoradas');
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
document.addEventListener('DOMContentLoaded', function() {
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
    let chatContext = {
        mode: 'quick-search',
        quickSearchStep: 0,
        quickSearchData: {}
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
                    <p>Olá! Eu sou Flai, seu assistente de viagens virtual. Como posso ajudar você hoje?</p>
                    <p>Escolha uma das modalidades acima:</p>
                    <ul>
                        <li><strong>Busca Rápida</strong>: Para encontrar os melhores voos rapidamente.</li>
                        <li><strong>Planejamento Completo</strong>: Para criar um itinerário detalhado com voos, hotéis e atrações.</li>
                    </ul>
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

            // Se tivermos resultados de voos ou preços, exibir em um formato visual atraente
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
        optionsHtml += '<h3>Opções de Voos Disponíveis</h3>';
        
        // Adicionar resultados de busca de melhores preços
        if (bestPricesData && bestPricesData.best_prices && bestPricesData.best_prices.length > 0) {
            optionsHtml += '<div class="best-prices-section">';
            optionsHtml += '<h4>Melhores Preços</h4>';
            
            bestPricesData.best_prices.forEach((price, index) => {
                // Formatar data para exibição
                const dateObj = new Date(price.date);
                const formattedDate = dateObj.toLocaleDateString('pt-BR');
                
                optionsHtml += `
                <div class="flight-card">
                    <div class="flight-info">
                        <div class="flight-date">${formattedDate}</div>
                        <div class="flight-price">R$ ${price.price.toFixed(2)}</div>
                    </div>
                    <div class="flight-actions">
                        <a href="${price.affiliate_link}" target="_blank" class="btn-purchase">
                            <i class="fas fa-shopping-cart"></i> Comprar
                        </a>
                        <button class="btn-select" data-option="${index}" data-type="price">
                            <i class="fas fa-check"></i> Selecionar
                        </button>
                    </div>
                </div>`;
            });
            
            optionsHtml += '</div>';
        }
        
        // Adicionar resultados de busca de voos específicos
        if (flightData && flightData.flights && flightData.flights.length > 0) {
            optionsHtml += '<div class="flights-section">';
            optionsHtml += '<h4>Voos Disponíveis</h4>';
            
            flightData.flights.forEach((flight, index) => {
                // Formatar data/hora para exibição
                const departureTime = new Date(flight.departure.time);
                const arrivalTime = new Date(flight.arrival.time);
                const formattedDeparture = departureTime.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
                const formattedArrival = arrivalTime.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
                
                optionsHtml += `
                <div class="flight-card">
                    <div class="flight-header">
                        <div class="airline">${flight.airline}</div>
                        <div class="flight-price">R$ ${flight.price.toFixed(2)}</div>
                    </div>
                    <div class="flight-details">
                        <div class="flight-time">
                            <span class="departure">${formattedDeparture}</span>
                            <span class="flight-arrow">→</span>
                            <span class="arrival">${formattedArrival}</span>
                        </div>
                        <div class="flight-route">
                            <span>${flight.departure.airport}</span>
                            <span class="flight-arrow">→</span>
                            <span>${flight.arrival.airport}</span>
                        </div>
                    </div>
                    <div class="flight-actions">
                        <a href="${flight.affiliate_link}" target="_blank" class="btn-purchase">
                            <i class="fas fa-shopping-cart"></i> Comprar
                        </a>
                        <button class="btn-select" data-option="${index}" data-type="flight">
                            <i class="fas fa-check"></i> Selecionar
                        </button>
                    </div>
                </div>`;
            });
            
            optionsHtml += '</div>';
        }
        
        optionsHtml += '</div>';
        flightOptionsElement.innerHTML = optionsHtml;
        
        chatMessages.appendChild(flightOptionsElement);
        
        // Adicionar event listeners para os botões
        const selectButtons = flightOptionsElement.querySelectorAll('.btn-select');
        selectButtons.forEach(button => {
            button.addEventListener('click', () => {
                const optionType = button.getAttribute('data-type');
                const optionIndex = button.getAttribute('data-option');
                
                let selectedOption;
                if (optionType === 'price') {
                    selectedOption = bestPricesData.best_prices[optionIndex];
                    sendMessage(`Quero mais detalhes sobre o voo do dia ${new Date(selectedOption.date).toLocaleDateString('pt-BR')}`);
                } else if (optionType === 'flight') {
                    selectedOption = flightData.flights[optionIndex];
                    sendMessage(`Quero mais detalhes sobre o voo da ${selectedOption.airline} de ${selectedOption.departure.airport} para ${selectedOption.arrival.airport}`);
                }
            });
        });
        
        scrollToBottom();
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

    // Start functions
    loadConversations();
    loadUserProfile();
    loadTravelPlans();
    startPriceMonitoring();
});

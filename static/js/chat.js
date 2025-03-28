document.addEventListener('DOMContentLoaded', function() {
    // Elementos do DOM
    const chatMessages = document.querySelector('.chat-messages');
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const modeButtons = document.querySelectorAll('.mode-button');

    // Variáveis globais
    let chatMode = 'quick-search'; // Modo padrão
    let currentConversationId = null;
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
        const messageText = messageInput.value.trim();

        if (messageText) {
            // Adicionar mensagem do usuário ao chat
            addMessageToChat('user', messageText);

            // Limpar campo de entrada
            messageInput.value = '';

            // Adicionar indicador de digitação
            showTypingIndicator();

            // Enviar para processamento
            processMessage(messageText);
        }
    }

    function processMessage(message) {
        // Preparar histórico para envio
        const history = [];
        const messageDivs = document.querySelectorAll('.message');

        messageDivs.forEach(div => {
            const isUser = div.classList.contains('user-message');
            const content = div.querySelector('.message-content').innerText;

            if (content) {
                history.push({
                    is_user: isUser,
                    content: content
                });
            }
        });

        // Enviar para o backend
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                mode: chatMode,
                history: history
            })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();

            if (data.error) {
                addMessageToChat('assistant', 'Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente.');
                console.log("Error response:", data.error);
                return;
            }

            // Adicionar resposta ao chat
            addMessageToChat('assistant', data.response);

            // Garantir que rola até a mensagem mais recente
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 100);

            // Se houver link de compra, mostrar botão
            if (data.purchase_link) {
                addPurchaseLink(data.purchase_link);
            }
        })
        .catch(error => {
            console.log("Error getting chat response:", error);
            removeTypingIndicator();
            addMessageToChat('assistant', 'Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente.');
        });
    }

    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', role);

        if (role === 'assistant') {
            // Adiciona a imagem do assistente
            const avatarContainer = document.createElement('div');
            avatarContainer.classList.add('avatar-container');

            const avatarImg = document.createElement('img');
            avatarImg.src = '/static/img/avi rosto chat.png';
            avatarImg.alt = 'Avatar da Avi';
            avatarImg.classList.add('assistant-avatar');

            avatarContainer.appendChild(avatarImg);
            messageDiv.appendChild(avatarContainer);

            // Formata links, se houver
            content = formatLinks(content);

            // Formata quebras de linha
            content = content.replace(/\n/g, '<br>');

            const messageContentDiv = document.createElement('div');
            messageContentDiv.classList.add('message-content');
            messageContentDiv.innerHTML = content;
            messageDiv.appendChild(messageContentDiv);
        } else {
            // Formata links, se houver
            content = formatLinks(content);

            // Formata quebras de linha
            content = content.replace(/\n/g, '<br>');

            const messageContentDiv = document.createElement('div');
            messageContentDiv.classList.add('message-content');
            messageContentDiv.innerHTML = content;
            messageDiv.appendChild(messageContentDiv);
        }

        chatMessages.appendChild(messageDiv);

        // Rolagem automática para garantir que a mensagem mais recente esteja visível
        chatMessages.scrollTop = chatMessages.scrollHeight;
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
        chatMessages.scrollTop = chatMessages.scrollHeight;
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
        chatMessages.scrollTop = chatMessages.scrollHeight;
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
        addMessageToChat('assistant', '', alertDiv);
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

    function formatLinks(text) {
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        return text.replace(urlRegex, (url) => `<a href="${url}" target="_blank">${url}</a>`);
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
        document.querySelector('.chat-messages').innerHTML = '';

        // Resetar ID de conversa
        chatContext = {
            mode: chatMode,
            quickSearchStep: 0,
            quickSearchData: {}
        };

        // Adicionar mensagem de boas-vindas
        addWelcomeMessage();
    });


    //Start functions
    loadConversations();
    loadUserProfile();
    loadTravelPlans();
    startPriceMonitoring();
});
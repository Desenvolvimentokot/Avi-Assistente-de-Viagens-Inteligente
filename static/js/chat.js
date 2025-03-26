document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.querySelector('.chat-messages');
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const modeButtons = document.querySelectorAll('.mode-button');

    let currentMode = 'quick-search';
    let conversationHistory = [];

    // Inicialização
    function init() {
        addMessage('👋 Olá! Sou o BuscaRápida do Flai, especialista em encontrar as melhores passagens aéreas para você. Como posso ajudar?', false);
    }

    // Event Listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    modeButtons.forEach(button => {
        button.addEventListener('click', function() {
            modeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentMode = this.dataset.mode;
        });
    });

    // Funções
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Adicionar mensagem do usuário ao chat
        addMessage(message, true);

        // Limpar input
        messageInput.value = '';

        // Adicionar à história da conversa
        conversationHistory.push({ role: 'user', content: message });

        // Mostrar indicador de digitação
        showTypingIndicator();

        // Enviar requisição para o backend
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                mode: currentMode,
                history: conversationHistory
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na requisição');
            }
            return response.json();
        })
        .then(data => {
            // Remover indicador de digitação
            removeTypingIndicator();

            // Processar resposta
            if (data.error) {
                addMessage('Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente.', false);
            } else {
                // Adicionar resposta ao chat
                addMessage(data.response, false);

                // Adicionar à história da conversa
                conversationHistory.push({ role: 'assistant', content: data.response });

                // Se houver link de compra, mostrar botão
                if (data.purchase_link) {
                    addPurchaseLink(data.purchase_link);
                }
            }
        })
        .catch(error => {
            console.log("Error getting chat response:", error);
            removeTypingIndicator();
            addMessage('Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente.', false);
        });
    }

    function addMessage(text, isUser) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(isUser ? 'user-message' : 'assistant-message');

        const avatarElement = document.createElement('div');
        avatarElement.classList.add('message-avatar');
        avatarElement.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');
        contentElement.innerText = text;

        messageElement.appendChild(avatarElement);
        messageElement.appendChild(contentElement);

        chatMessages.appendChild(messageElement);

        // Scroll para o final
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.classList.add('message', 'assistant-message', 'typing-indicator');

        const avatarElement = document.createElement('div');
        avatarElement.classList.add('message-avatar');
        avatarElement.innerHTML = '<i class="fas fa-robot"></i>';

        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');
        contentElement.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

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

    function addPurchaseLink(url) {
        const linkContainer = document.createElement('div');
        linkContainer.classList.add('purchase-link-container');

        const linkButton = document.createElement('a');
        linkButton.href = url;
        linkButton.target = '_blank';
        linkButton.classList.add('purchase-link-button');
        linkButton.innerHTML = '<i class="fas fa-external-link-alt"></i> Comprar passagem';

        linkContainer.appendChild(linkButton);
        chatMessages.appendChild(linkContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Inicializar
    init();


    // Funções de carregamento e gerenciamento de dados (from original code)
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

    // Funções auxiliares (from original code)
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

    function formatCurrency(amount, currency) {
        // Formatar preço conforme a moeda
        const formatter = new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: currency || 'BRL'
        });

        return formatter.format(amount);
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
        // Formatar duração (ex: PT2H30M -> 2h 30min)
        const hoursMatch = durationStr.match(/(\d+)H/);
        const minutesMatch = durationStr.match(/(\d+)M/);

        const hours = hoursMatch ? hoursMatch[1] + 'h ' : '';
        const minutes = minutesMatch ? minutesMatch[1] + 'min' : '';

        return hours + minutes;
    }

    // Adicionar event listeners para itens da navegação (from original code)
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

    // Adicionar event listener para o botão de nova conversa (from original code)
    document.querySelector('.add-conversation').addEventListener('click', function() {
        // Limpar mensagens existentes
        document.querySelector('.chat-messages').innerHTML = '';

        // Resetar ID de conversa
        conversationHistory = [];

        // Adicionar mensagem de boas-vindas
        addMessage('👋 Olá! Sou o BuscaRápida do Flai, especialista em encontrar as melhores passagens aéreas para você. Como posso ajudar?', false);
    });


    //Start functions from original code
    loadConversations();
    loadUserProfile();
    loadTravelPlans();
    startPriceMonitoring();


});
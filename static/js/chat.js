document.addEventListener('DOMContentLoaded', function() {
    // Elementos do DOM
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const messagesContainer = document.getElementById('chat-messages');
    const messageForm = document.getElementById('message-form');
    const modeTabs = document.querySelectorAll('.mode-tab');
    const buyButton = document.getElementById('buy-button');

    // Estado atual do chat
    let currentMode = 'quick-search'; // ['quick-search', 'full-planning']
    let isWaitingResponse = false;
    let conversationHistory = [];
    let currentPurchaseLink = null;

    // Inicialização
    initializeChat();

    // Função para inicializar o chat
    function initializeChat() {
        // Exibir mensagem de boas-vindas
        showBotMessage(`Olá! Eu sou Flai, seu assistente de viagens virtual. Como posso ajudar você hoje?

Escolha uma das modalidades acima:

• <b>Busca Rápida</b>: Para encontrar os melhores voos rapidamente.
• <b>Planejamento Completo</b>: Para criar um itinerário detalhado com voos, hotéis e atrações.`);

        // Configurar eventos
        setupEventListeners();
    }

    // Configurar listeners de eventos
    function setupEventListeners() {
        // Enviar mensagem com Enter ou clique no botão
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });

        sendButton.addEventListener('click', function() {
            sendMessage();
        });

        // Alternar entre modos
        modeTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const mode = this.getAttribute('data-mode');
                switchMode(mode);
            });
        });

        // Botão de compra
        if (buyButton) {
            buyButton.addEventListener('click', function() {
                if (currentPurchaseLink) {
                    window.open(currentPurchaseLink, '_blank');
                }
            });
        }
    }

    // Função para enviar mensagem
    function sendMessage() {
        if (isWaitingResponse) return;

        const message = chatInput.value.trim();
        if (!message) return;

        // Limpar input
        chatInput.value = '';

        // Exibir mensagem do usuário
        showUserMessage(message);

        // Atualizar histórico
        updateHistory('user', message);

        // Enviar para processamento
        processMessage(message);
    }

    // Processar mensagem e obter resposta
    function processMessage(message) {
        isWaitingResponse = true;

        // Mostrar indicador de digitação
        showTypingIndicator();

        // Preparar dados para enviar à API
        const requestData = {
            message: message,
            mode: currentMode,
            history: conversationHistory
        };

        // Enviar requisição para API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            // Remover indicador de digitação
            hideTypingIndicator();

            // Verificar se houve erro
            if (data.error) {
                showErrorMessage(data.message || 'Ocorreu um erro ao processar sua mensagem.');
                return;
            }

            // Exibir resposta
            showBotMessage(data.response);

            // Atualizar histórico
            updateHistory('assistant', data.response);

            // Verificar se há link de compra
            if (data.purchase_link) {
                currentPurchaseLink = data.purchase_link;
                showBuyButton();
            } else {
                hideBuyButton();
            }
        })
        .catch(error => {
            console.error('Error getting chat response:', error);
            hideTypingIndicator();
            showErrorMessage('Ocorreu um erro na comunicação com o servidor. Por favor, tente novamente mais tarde.');
        })
        .finally(() => {
            isWaitingResponse = false;
        });
    }

    // Exibir mensagem do usuário
    function showUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.innerHTML = `<p>${escapeHtml(message)}</p>`;
        messagesContainer.appendChild(messageElement);
        scrollToBottom();
    }

    // Exibir mensagem do bot
    function showBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';

        // Processar links em markdown [text](url)
        const processedMessage = message.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        messageElement.innerHTML = `<p>${processedMessage}</p>`;
        messagesContainer.appendChild(messageElement);
        scrollToBottom();
    }

    // Exibir mensagem de erro
    function showErrorMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message error-message';
        messageElement.innerHTML = `<p>Erro: ${escapeHtml(message)}</p>`;
        messagesContainer.appendChild(messageElement);
        scrollToBottom();
    }

    // Mostrar indicador de digitação
    function showTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.className = 'message bot-message typing-indicator';
        typingElement.id = 'typing-indicator';
        typingElement.innerHTML = `<div class="dot-flashing"></div>`;
        messagesContainer.appendChild(typingElement);
        scrollToBottom();
    }

    // Esconder indicador de digitação
    function hideTypingIndicator() {
        const typingElement = document.getElementById('typing-indicator');
        if (typingElement) {
            typingElement.remove();
        }
    }

    // Atualizar histórico de conversa
    function updateHistory(role, content) {
        conversationHistory.push({
            role: role,
            content: content
        });

        // Limitar tamanho do histórico
        if (conversationHistory.length > 20) {
            conversationHistory = conversationHistory.slice(-20);
        }
    }

    // Alternar entre modos
    function switchMode(mode) {
        if (mode === currentMode) return;

        // Atualizar UI
        modeTabs.forEach(tab => {
            if (tab.getAttribute('data-mode') === mode) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        // Atualizar estado
        currentMode = mode;

        // Limpar histórico ao trocar de modo
        // conversationHistory = [];

        // Exibir mensagem sobre o novo modo
        let modeMessage = '';

        if (mode === 'quick-search') {
            modeMessage = 'Modo <b>Busca Rápida</b> ativado. Me diga seu destino e datas desejadas para encontrar as melhores passagens!';
        } else {
            modeMessage = 'Modo <b>Planejamento Completo</b> ativado. Vamos criar um roteiro detalhado para sua viagem, incluindo voos, hospedagem e atrações.';
        }

        showBotMessage(modeMessage);
    }

    // Mostrar botão de compra
    function showBuyButton() {
        if (buyButton) {
            buyButton.style.display = 'block';
        }
    }

    // Esconder botão de compra
    function hideBuyButton() {
        if (buyButton) {
            buyButton.style.display = 'none';
        }
        currentPurchaseLink = null;
    }

    // Rolar para o final da conversa
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Escapar HTML para evitar XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
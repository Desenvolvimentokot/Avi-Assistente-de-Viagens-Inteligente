
document.addEventListener('DOMContentLoaded', function() {
    // Elementos da interface
    const chatContainer = document.querySelector('.chat-messages');
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const modeButtons = document.querySelectorAll('.mode-button');
    
    // Variáveis de estado
    let currentConversationId = null;
    let chatContext = {
        mode: 'quick-search', // Modo padrão: busca rápida
        quickSearchStep: 0,
        quickSearchData: {}
    };
    
    // Event listeners
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // Alternar entre modos de chat
    if (modeButtons) {
        modeButtons.forEach(button => {
            button.addEventListener('click', function() {
                const mode = this.dataset.mode;
                modeButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // Atualizar o modo do chat
                chatContext.mode = mode;
                
                // Resetar passos se mudar de modo
                if (mode === 'quick-search') {
                    chatContext.quickSearchStep = 0;
                    chatContext.quickSearchData = {};
                } else if (mode === 'full-planning') {
                    chatContext.fullPlanningStep = 0;
                    chatContext.fullPlanningData = {};
                }
                
                // Adicionar mensagem do sistema sobre o novo modo
                const modeMessages = {
                    'quick-search': '🔍 Modo Busca Rápida ativado. Como posso ajudar a encontrar sua passagem?',
                    'full-planning': '📝 Modo Planejamento Completo ativado. Vamos planejar sua viagem!',
                    'general': '💬 Modo Geral ativado. Como posso ajudar?'
                };
                
                addMessage(modeMessages[mode] || 'Modo alterado. Como posso ajudar?', false);
            });
        });
    }
    
    // Função para enviar mensagem
    function sendMessage() {
        if (!messageInput) return;
        
        const message = messageInput.value.trim();
        if (message === '') return;
        
        // Adicionar mensagem do usuário à interface
        addMessage(message, true);
        
        // Limpar input
        messageInput.value = '';
        
        // Mostrar indicador de digitação
        addTypingIndicator();
        
        // Enviar para a API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId,
                context: chatContext
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remover indicador de digitação
            removeTypingIndicator();
            
            // Atualizar o ID da conversa se for nova
            if (data.conversation_id) {
                currentConversationId = data.conversation_id;
            }
            
            // Atualizar o contexto do chat
            if (data.context) {
                chatContext = data.context;
            }
            
            // Adicionar resposta do assistente
            if (data.response) {
                addMessage(data.response, false);
            }
            
            // Processar ação, se houver
            if (data.action) {
                processAction(data.action);
            }
        })
        .catch(error => {
            console.error('Error getting chat response:', error);
            removeTypingIndicator();
            addMessage('Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.', false);
        });
    }
    
    // Adicionar mensagem à interface
    function addMessage(content, isUser) {
        if (!chatContainer) return;
        
        const messageClass = isUser ? 'user-message' : 'assistant-message';
        const avatar = isUser ? '<div class="user-avatar"><i class="fas fa-user"></i></div>' : 
                                '<div class="assistant-avatar"><i class="fas fa-robot"></i></div>';
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${messageClass}`;
        messageElement.innerHTML = `
            ${avatar}
            <div class="message-content">
                <div class="message-text">${formatMessageContent(content)}</div>
            </div>
        `;
        
        chatContainer.appendChild(messageElement);
        
        // Rolar para baixo
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Formatar conteúdo da mensagem (adicionar quebras de linha, links, etc)
    function formatMessageContent(content) {
        // Substituir quebras de linha por <br>
        let formatted = content.replace(/\n/g, '<br>');
        
        // Detectar e formatar links
        formatted = formatted.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        return formatted;
    }
    
    // Adicionar indicador de digitação
    function addTypingIndicator() {
        if (!chatContainer) return;
        
        const typingElement = document.createElement('div');
        typingElement.className = 'message assistant-message typing-indicator';
        typingElement.innerHTML = `
            <div class="assistant-avatar"><i class="fas fa-robot"></i></div>
            <div class="message-content">
                <div class="message-text">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        
        typingElement.id = 'typing-indicator';
        chatContainer.appendChild(typingElement);
        
        // Rolar para baixo
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Remover indicador de digitação
    function removeTypingIndicator() {
        const typingElement = document.getElementById('typing-indicator');
        if (typingElement) {
            typingElement.remove();
        }
    }
    
    // Processar ação retornada pela API
    function processAction(action) {
        if (!action || !action.type) return;
        
        switch (action.type) {
            case 'search_flights':
                // Buscar voos com os dados fornecidos
                fetchFlights(action.data);
                break;
                
            case 'generate_travel_plan':
                // Gerar plano de viagem
                generateTravelPlan(action.data);
                break;
        }
    }
    
    // Buscar voos na API
    function fetchFlights(searchData) {
        addMessage('🔍 Buscando voos com os dados fornecidos...', false);
        
        fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: 'flights',
                params: searchData
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addMessage(`❌ Erro na busca: ${data.error}`, false);
                return;
            }
            
            if (!data.flights || data.flights.length === 0) {
                addMessage('Não encontrei voos com os critérios informados. Que tal tentar com datas ou aeroportos alternativos?', false);
                return;
            }
            
            // Mostrar resultados
            let resultsMessage = '✅ Encontrei estas opções de voo para você:\n\n';
            
            data.flights.slice(0, 3).forEach((flight, index) => {
                resultsMessage += `**Opção ${index + 1}:**\n`;
                resultsMessage += `🛫 Partida: ${flight.departure.airport} às ${formatDateTime(flight.departure.time)}\n`;
                resultsMessage += `🛬 Chegada: ${flight.arrival.airport} às ${formatDateTime(flight.arrival.time)}\n`;
                resultsMessage += `⏱ Duração: ${formatDuration(flight.duration)}\n`;
                resultsMessage += `💰 Preço: ${flight.price}\n`;
                resultsMessage += `${flight.segments > 1 ? `🔄 ${flight.segments - 1} conexões` : '✈️ Voo direto'}\n\n`;
            });
            
            resultsMessage += 'Gostaria de mais detalhes sobre alguma dessas opções?';
            
            addMessage(resultsMessage, false);
        })
        .catch(error => {
            console.error('Error fetching flights:', error);
            addMessage('Desculpe, ocorreu um erro ao buscar voos. Por favor, tente novamente mais tarde.', false);
        });
    }
    
    // Formatar data e hora para exibição
    function formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        return `${date.toLocaleDateString('pt-BR')} ${date.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'})}`;
    }
    
    // Formatar duração (PT2H30M -> 2h 30min)
    function formatDuration(durationStr) {
        const hoursMatch = durationStr.match(/(\d+)H/);
        const minutesMatch = durationStr.match(/(\d+)M/);
        
        const hours = hoursMatch ? hoursMatch[1] + 'h ' : '';
        const minutes = minutesMatch ? minutesMatch[1] + 'min' : '';
        
        return hours + minutes;
    }
    
    // Gerar plano de viagem
    function generateTravelPlan(planData) {
        // Implementação futura
        addMessage('Funcionalidade de geração de plano de viagem em desenvolvimento.', false);
    }
    
    // Inicializar chat com uma mensagem de boas-vindas
    addMessage('👋 Olá! Sou o BuscaRápida do Flai, especialista em encontrar passagens aéreas. Para onde você gostaria de viajar?', false);
});

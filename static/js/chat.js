
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.querySelector('.chat-messages');
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const modeButtons = document.querySelectorAll('.mode-button');
    
    let currentMode = 'quick-search';
    let currentConversationId = null;
    
    // Inicialização
    function init() {
        addMessage('👋 Olá! Sou o BuscaRápida do Flai, especialista em encontrar as melhores passagens aéreas para você. Como posso ajudar?', false);
        
        // Carregar conversas existentes
        loadConversations();
        
        // Carregar perfil do usuário
        loadUserProfile();
        
        // Carregar planos de viagem
        loadTravelPlans();
        
        // Iniciar verificação de preços
        startPriceMonitoring();
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
        currentConversationId = null;
        
        // Adicionar mensagem de boas-vindas
        addMessage('👋 Olá! Sou o BuscaRápida do Flai, especialista em encontrar as melhores passagens aéreas para você. Como posso ajudar?', false);
    });
    
    // Funções principais
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            // Adicionar mensagem do usuário à interface
            addMessage(message, true);
            
            // Limpar input
            messageInput.value = '';
            
            // Processar mensagem
            processMessage(message);
        }
    }
    
    function addMessage(message, isUser, additionalContent = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
        
        const avatarDiv = document.createElement('div');
        avatarDiv.classList.add('avatar');
        
        const iconDiv = document.createElement('div');
        iconDiv.classList.add('icon');
        
        const icon = document.createElement('i');
        icon.classList.add('fas');
        icon.classList.add(isUser ? 'fa-user' : 'fa-paper-plane');
        
        iconDiv.appendChild(icon);
        avatarDiv.appendChild(iconDiv);
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('content');
        
        // Processar links e formatação básica no texto
        const formattedMessage = formatMessage(message);
        contentDiv.innerHTML = formattedMessage;
        
        // Adicionar conteúdo adicional se houver
        if (additionalContent) {
            contentDiv.appendChild(additionalContent);
        }
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll para a última mensagem
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function formatMessage(text) {
        // Converter URLs em links clicáveis
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        text = text.replace(urlRegex, function(url) {
            return `<a href="${url}" target="_blank">${url}</a>`;
        });
        
        // Substituir quebras de linha por <br>
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    function processMessage(message) {
        // Mostrar indicador de digitação
        showTypingIndicator();
        
        // Determinar ação com base no modo atual
        if (currentMode === 'quick-search') {
            processQuickSearch(message);
        } else {
            processFullPlanning(message);
        }
    }
    
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('message', 'bot-message', 'typing-indicator');
        
        const avatarDiv = document.createElement('div');
        avatarDiv.classList.add('avatar');
        
        const iconDiv = document.createElement('div');
        iconDiv.classList.add('icon');
        
        const icon = document.createElement('i');
        icon.classList.add('fas', 'fa-paper-plane');
        
        iconDiv.appendChild(icon);
        avatarDiv.appendChild(iconDiv);
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('content');
        
        const dotsDiv = document.createElement('div');
        dotsDiv.classList.add('typing-dots');
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dotsDiv.appendChild(dot);
        }
        
        contentDiv.appendChild(dotsDiv);
        typingDiv.appendChild(avatarDiv);
        typingDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return typingDiv;
    }
    
    function removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Processar busca rápida
    function processQuickSearch(message) {
        // Fazer solicitação à API
        fetch('/api/chat/busca-rapida', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remover indicador de digitação
            removeTypingIndicator();
            
            // Se tiver um novo ID de conversa, atualizar o atual
            if (data.conversation_id) {
                currentConversationId = data.conversation_id;
            }
            
            // Adicionar resposta do bot
            addMessage(data.response, false);
            
            // Se houver resultados de voos, exibi-los
            if (data.flights && data.flights.data && data.flights.data.length > 0) {
                displayFlightResults(data.flights);
            }
        })
        .catch(error => {
            console.error('Error getting chat response:', error);
            removeTypingIndicator();
            addMessage('Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente.', false);
        });
    }
    
    // Exibir resultados de voos
    function displayFlightResults(flightData) {
        const resultsDiv = document.createElement('div');
        resultsDiv.classList.add('search-result');
        
        const flights = flightData.data.slice(0, 3); // Limitar a 3 resultados
        
        flights.forEach((flight, index) => {
            const flightCard = document.createElement('div');
            flightCard.classList.add('search-result-item');
            
            // Cabeçalho do card
            const header = document.createElement('div');
            header.classList.add('search-result-header');
            
            const airline = document.createElement('div');
            airline.innerHTML = `<strong>${getAirlineName(flight.itineraries[0].segments[0].carrierCode)}</strong>`;
            
            const price = document.createElement('div');
            price.innerHTML = `<strong>${formatCurrency(flight.price.total, flight.price.currency)}</strong>`;
            
            header.appendChild(airline);
            header.appendChild(price);
            flightCard.appendChild(header);
            
            // Detalhes do voo
            const details = document.createElement('div');
            details.classList.add('search-result-details');
            
            // Origem -> Destino
            const itinerary = flight.itineraries[0];
            const firstSegment = itinerary.segments[0];
            const lastSegment = itinerary.segments[itinerary.segments.length - 1];
            
            const flightInfo = document.createElement('div');
            flightInfo.classList.add('flight-info');
            
            // Partida
            const departure = document.createElement('div');
            departure.classList.add('departure');
            departure.innerHTML = `
                <div class="time">${formatTime(firstSegment.departure.at)}</div>
                <div class="location">${firstSegment.departure.iataCode}</div>
            `;
            
            // Duração e linha
            const duration = document.createElement('div');
            duration.classList.add('flight-duration');
            duration.innerHTML = `
                <div class="line"></div>
                <div class="duration">${formatDuration(itinerary.duration)}</div>
                <div class="stops">${itinerary.segments.length > 1 ? 
                    `${itinerary.segments.length - 1} ${itinerary.segments.length - 1 > 1 ? 'escalas' : 'escala'}` : 
                    'Direto'}</div>
            `;
            
            // Chegada
            const arrival = document.createElement('div');
            arrival.classList.add('arrival');
            arrival.innerHTML = `
                <div class="time">${formatTime(lastSegment.arrival.at)}</div>
                <div class="location">${lastSegment.arrival.iataCode}</div>
            `;
            
            flightInfo.appendChild(departure);
            flightInfo.appendChild(duration);
            flightInfo.appendChild(arrival);
            details.appendChild(flightInfo);
            
            // Detalhes adicionais
            const additionalInfo = document.createElement('div');
            additionalInfo.classList.add('additional-info');
            additionalInfo.innerHTML = `
                <div>Partida: ${formatDateTime(firstSegment.departure.at)}</div>
                <div>Chegada: ${formatDateTime(lastSegment.arrival.at)}</div>
            `;
            details.appendChild(additionalInfo);
            
            // Botão de compra
            const bookButton = document.createElement('button');
            bookButton.classList.add('btn-book');
            bookButton.textContent = 'Comprar esta passagem';
            bookButton.dataset.flightId = flight.id;
            bookButton.addEventListener('click', () => bookFlight(flight));
            
            details.appendChild(bookButton);
            flightCard.appendChild(details);
            
            resultsDiv.appendChild(flightCard);
        });
        
        // Adicionar mensagem com os resultados
        addMessage('Aqui estão algumas opções de voos que encontrei para você. Clique em "Comprar esta passagem" para ser redirecionado ao site da companhia aérea. Precisa de mais detalhes sobre alguma dessas opções?', false, resultsDiv);
    }
    
    // Função para redirecionar para compra
    function bookFlight(flight) {
        // Simular link de afiliado baseado na companhia aérea
        let affiliateLink = '';
        const carrierCode = flight.itineraries[0].segments[0].carrierCode;
        
        // Links fictícios - em produção seriam substituídos por links de afiliados reais
        switch(carrierCode) {
            case 'LA':
                affiliateLink = 'https://www.latamairlines.com/';
                break;
            case 'G3':
                affiliateLink = 'https://www.voegol.com.br/';
                break;
            case 'AD':
                affiliateLink = 'https://www.flyazul.com.br/';
                break;
            case 'AA':
                affiliateLink = 'https://www.aa.com/';
                break;
            case 'AF':
                affiliateLink = 'https://www.airfrance.com/';
                break;
            case 'LH':
                affiliateLink = 'https://www.lufthansa.com/';
                break;
            default:
                affiliateLink = 'https://www.skyscanner.com.br/';
        }
        
        // Construir mensagem sobre o redirecionamento
        const message = `Estou redirecionando você para o site da companhia aérea para finalizar sua compra. O preço total é ${formatCurrency(flight.price.total, flight.price.currency)}.`;
        addMessage(message, false);
        
        // Adicionar botão de redirecionamento
        const redirectDiv = document.createElement('div');
        redirectDiv.classList.add('redirect-info');
        
        const redirectButton = document.createElement('a');
        redirectButton.classList.add('btn-redirect');
        redirectButton.href = affiliateLink;
        redirectButton.target = '_blank';
        redirectButton.textContent = 'Ir para o site de compra';
        redirectButton.style.display = 'inline-block';
        redirectButton.style.padding = '10px 20px';
        redirectButton.style.backgroundColor = '#4CAF50';
        redirectButton.style.color = 'white';
        redirectButton.style.textDecoration = 'none';
        redirectButton.style.borderRadius = '4px';
        redirectButton.style.margin = '10px 0';
        
        redirectDiv.appendChild(redirectButton);
        
        // Adicionar mensagem informativa
        const infoText = document.createElement('p');
        infoText.innerHTML = 'Dica: Compare os preços antes de finalizar a compra. Às vezes, o site oficial da companhia aérea pode ter promoções exclusivas.';
        infoText.style.fontSize = '12px';
        infoText.style.color = '#6a737d';
        infoText.style.marginTop = '5px';
        
        redirectDiv.appendChild(infoText);
        
        // Adicionar à mensagem
        addMessage('Clique no botão abaixo para ser redirecionado ao site de compra:', false, redirectDiv);
    }
    
    // Processar planejamento completo (a ser implementado)
    function processFullPlanning(message) {
        // Remover indicador de digitação
        removeTypingIndicator();
        
        // Resposta temporária
        addMessage('O modo de planejamento completo ainda está em desenvolvimento. Por favor, use o modo de Busca Rápida por enquanto.', false);
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
    
    // Inicializar
    init();
});

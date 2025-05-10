/**
 * Integração do Chat com o Widget Trip.com
 * 
 * Este script integra o chat com a API do widget headless Trip.com/TravelPayouts,
 * permitindo a exibição dos resultados de busca diretamente na interface de chat.
 */

// Funções auxiliares para interface
function showLoadingIndicator(message) {
    // Verifica se o elemento de loading já existe
    let loadingElement = document.getElementById('flight-loading-indicator');
    
    if (!loadingElement) {
        // Criar elemento de loading
        loadingElement = document.createElement('div');
        loadingElement.id = 'flight-loading-indicator';
        loadingElement.className = 'message assistant-message';
        loadingElement.innerHTML = `
            <div class="message-content">
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">${message || 'Buscando voos...'}</div>
                </div>
            </div>
        `;
        
        // Inserir no chat
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.appendChild(loadingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    } else {
        // Atualizar mensagem de loading
        const loadingText = loadingElement.querySelector('.loading-text');
        if (loadingText) {
            loadingText.textContent = message || 'Buscando voos...';
        }
    }
}

function hideLoadingIndicator() {
    const loadingElement = document.getElementById('flight-loading-indicator');
    if (loadingElement) {
        loadingElement.remove();
    }
}

function displayMessage(message) {
    // Criar mensagem da assistente
    const messageElement = document.createElement('div');
    messageElement.className = 'message assistant-message';
    messageElement.innerHTML = `
        <div class="message-content">
            <p>${message}</p>
        </div>
    `;
    
    // Inserir no chat
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function displayFlightCard(flight) {
    // Validar dados do voo
    if (!flight) return;
    
    // Elementos de preço
    const price = typeof flight.price === 'number' 
        ? flight.price.toLocaleString('pt-BR', { minimumFractionDigits: 2 })
        : flight.price;
    
    // Criar card de voo
    const cardElement = document.createElement('div');
    cardElement.className = 'message assistant-message';
    cardElement.innerHTML = `
        <div class="message-content flight-card">
            <div class="flight-card-header">
                <div class="flight-airline">${flight.airline || 'Companhia Aérea'}</div>
                <div class="flight-price">${flight.currency || 'R$'} ${price}</div>
            </div>
            <div class="flight-card-body">
                <div class="flight-info">
                    <div class="flight-times">
                        <span class="departure-time">${flight.departure || 'Partida'}</span>
                        <span class="flight-arrow">→</span>
                        <span class="arrival-time">${flight.arrival || 'Chegada'}</span>
                    </div>
                </div>
            </div>
            <div class="flight-card-footer">
                ${flight.bookingUrl ? 
                    `<a href="${flight.bookingUrl}" target="_blank" class="flight-book-btn">Ver oferta</a>` :
                    '<span class="flight-notice">Oferta indisponível</span>'}
            </div>
        </div>
    `;
    
    // Inserir no chat
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.appendChild(cardElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function displayFlightCardsInChat(flights) {
    if (!flights || !flights.length) {
        displayMessage('Não encontramos voos para esta rota. Tente outra combinação de datas ou aeroportos.');
        return;
    }
    
    // Mostrar mensagem introdutória
    displayMessage('Encontrei as seguintes opções de voo para você:');
    
    // Mostrar cards de voo
    flights.forEach(flight => {
        displayFlightCard(flight);
    });
}

/**
 * Inicia uma busca de voos a partir dos parâmetros de viagem
 * 
 * @param {Object} travelParams - Parâmetros da viagem
 */
function searchFlights(travelParams) {
    // Validar parâmetros obrigatórios
    if (!travelParams.origin || !travelParams.destination || !travelParams.departure_date) {
        displayMessage('Não foi possível buscar voos: parâmetros de viagem incompletos.');
        return;
    }
    
    // Mostrar indicador de carregamento
    showLoadingIndicator('🔄 Estou buscando os melhores voos...');
    
    // Verificar se o cliente da API foi carregado
    if (typeof window.widgetApiClient === 'undefined') {
        console.error('Cliente da API de widget não carregado');
        hideLoadingIndicator();
        displayMessage('Desculpe, não foi possível iniciar a busca de voos. Por favor, tente novamente mais tarde.');
        return;
    }
    
    // Iniciar busca usando o cliente da API
    window.widgetApiClient.startSearch(
        travelParams,
        // Callback de status
        (status, message) => {
            if (status === 'searching') {
                showLoadingIndicator(message);
            }
        },
        // Callback de sucesso
        (results) => {
            hideLoadingIndicator();
            displayFlightCardsInChat(results);
        },
        // Callback de erro
        (error) => {
            hideLoadingIndicator();
            displayMessage(`Desculpe, ocorreu um erro durante a busca: ${error}`);
        }
    );
}

// Adicionar função ao contexto global para uso pelo chat
window.aviSearchFlights = searchFlights;
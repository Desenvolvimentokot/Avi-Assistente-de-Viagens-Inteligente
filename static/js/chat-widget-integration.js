
/**
 * Script para integração do widget Trip.com com o chat da Avi
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Inicializando integração do widget Trip.com com o chat");
    
    // Verificar se estamos em uma página com chat - com retry
    let attempts = 0;
    const maxAttempts = 5;
    
    function initializeWidget() {
        const chatMessagesElement = document.querySelector('.chat-messages');
        if (!chatMessagesElement) {
            attempts++;
            if (attempts < maxAttempts) {
                console.log(`Elemento .chat-messages não encontrado, tentativa ${attempts}/${maxAttempts}`);
                setTimeout(initializeWidget, 500);
            } else {
                console.log("Elemento .chat-messages não encontrado após várias tentativas");
            }
            return;
        }
    
    // Exportar função para exibir cartões de voos no chat
    window.displayFlightCardsInChat = function(flights) {
        // Verificar se temos voos para exibir
        if (!flights || !flights.length) {
            console.log("Nenhum voo para exibir");
            return;
        }
        
        // Criar mensagem para cartões de voo
        const flightMessage = document.createElement('div');
        flightMessage.className = 'message assistant-message';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        // Adicionar texto explicativo
        const introText = document.createElement('p');
        introText.textContent = 'Encontrei estas opções de voo para você:';
        content.appendChild(introText);
        
        // Adicionar container de cartões
        const cardsContainer = document.createElement('div');
        cardsContainer.className = 'flight-cards-container';
        
        // Limitar a 3 cartões para não sobrecarregar o chat
        const displayFlights = flights.slice(0, 3);
        
        // Criar cartões para cada voo
        displayFlights.forEach(flight => {
            const card = createFlightCard(flight);
            cardsContainer.appendChild(card);
        });
        
        // Adicionar container de cartões ao conteúdo
        content.appendChild(cardsContainer);
        
        // Adicionar o conteúdo à mensagem
        flightMessage.appendChild(content);
        
        // Adicionar a mensagem ao chat
        const chatMessages = document.querySelector('.chat-messages');
        if (chatMessages) {
            chatMessages.appendChild(flightMessage);
            scrollToBottom();
        }
    };
    
    // Função para criar um cartão de voo
    function createFlightCard(flight) {
        const card = document.createElement('div');
        card.className = 'flight-card';
        
        // Implementar conteúdo do cartão com informações do voo
        card.innerHTML = `
            <div class="flight-card-header">
                <div class="flight-card-airline">${flight.airline || 'Companhia'}</div>
                <div class="flight-card-price">${formatPrice(flight.price)}</div>
            </div>
            <div class="flight-card-route">
                <div class="flight-card-cities">${flight.origin} → ${flight.destination}</div>
                <div class="flight-card-date">${formatDate(flight.departureDate)}</div>
            </div>
            <a href="${flight.bookingLink}" target="_blank" class="flight-card-action">
                Ver detalhes
            </a>
        `;
        
        return card;
    }
    
    // Funções auxiliares
    function formatPrice(price) {
        if (!price) return 'Preço não disponível';
        
        try {
            const value = parseFloat(price);
            return value.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });
        } catch (e) {
            return price;
        }
    }
    
    function formatDate(dateStr) {
        if (!dateStr) return '';
        
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('pt-BR');
        } catch (e) {
            return dateStr;
        }
    }
    
    function scrollToBottom() {
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    console.log("Integração do widget Trip.com inicializada com sucesso");
    }
    
    initializeWidget();
});

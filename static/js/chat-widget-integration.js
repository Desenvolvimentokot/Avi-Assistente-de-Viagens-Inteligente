/**
 * Chat-Widget Integration
 * 
 * Este script integra a busca de voos via widget Trip.com com a interface
 * de chat, permitindo exibir cards de resultados diretamente no chat e
 * no painel lateral.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos em uma página com chat
    if (!document.querySelector('.chat-messages')) return;
    
    // Exportar função para exibir cartões de voos no chat
    window.displayFlightCardsInChat = function(flights) {
        // Verificar se temos voos para exibir
        if (!flights || !flights.length) return;
        
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
        
        // Adicionar link para ver mais
        if (flights.length > 3) {
            const viewMoreLink = document.createElement('div');
            viewMoreLink.className = 'view-more-flights';
            viewMoreLink.innerHTML = `<a href="/widget-api/chat_search" class="view-more-link">Ver todas as ${flights.length} opções</a>`;
            cardsContainer.appendChild(viewMoreLink);
        }
        
        content.appendChild(cardsContainer);
        flightMessage.appendChild(content);
        
        // Adicionar ao chat
        document.querySelector('.chat-messages').appendChild(flightMessage);
        
        // Scroll para mostrar novas mensagens
        document.querySelector('.chat-messages').scrollTop = document.querySelector('.chat-messages').scrollHeight;
    };
    
    // Função auxiliar para criar um cartão de voo
    function createFlightCard(flight) {
        const card = document.createElement('div');
        card.className = 'flight-card';
        
        // Formatação do preço
        const price = typeof flight.price === 'number' 
            ? flight.price.toLocaleString('pt-BR', { minimumFractionDigits: 2 })
            : flight.price;
        
        card.innerHTML = `
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
                    <div class="flight-duration">
                        ${flight.duration || ''}
                        ${flight.stops > 0 ? `(${flight.stops} ${flight.stops > 1 ? 'paradas' : 'parada'})` : 'Direto'}
                    </div>
                </div>
            </div>
            <div class="flight-card-footer">
                ${flight.bookingUrl ? 
                    `<a href="${flight.bookingUrl}" target="_blank" class="flight-book-btn">Ver oferta</a>` :
                    '<span class="flight-notice">Oferta indisponível</span>'}
            </div>
        `;
        
        return card;
    }
});
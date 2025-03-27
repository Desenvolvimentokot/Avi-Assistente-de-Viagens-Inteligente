
document.addEventListener('DOMContentLoaded', function() {
    // Definir datas padrão no formulário (hoje + 1 mês para ida, + 1 mês e 10 dias para volta)
    const today = new Date();
    const departureDate = new Date(today);
    departureDate.setMonth(today.getMonth() + 1);
    
    const returnDate = new Date(departureDate);
    returnDate.setDate(departureDate.getDate() + 10);
    
    // Formatar as datas para o formato YYYY-MM-DD
    document.getElementById('departure-date').value = formatDate(departureDate);
    document.getElementById('return-date').value = formatDate(returnDate);
    
    // Adicionar listener para o formulário de busca
    const searchForm = document.getElementById('flight-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', searchFlights);
    }
});

// Função para formatar a data no formato YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Função para buscar voos
function searchFlights(e) {
    e.preventDefault();
    
    // Mostrar algum tipo de indicador de carregamento
    const resultsSection = document.getElementById('results-section');
    const flightResults = document.getElementById('flight-results');
    
    flightResults.innerHTML = '<p>Buscando voos. Por favor, aguarde...</p>';
    resultsSection.classList.remove('hidden');
    
    // Obter valores do formulário
    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    const departureDate = document.getElementById('departure-date').value;
    const returnDate = document.getElementById('return-date').value;
    const adults = document.getElementById('adults').value;
    
    // Construir URL com parâmetros
    const url = `/api/search-flights?origin=${origin}&destination=${destination}&departure_date=${departureDate}&return_date=${returnDate}&adults=${adults}`;
    
    // Fazer a requisição à API
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao buscar voos');
            }
            return response.json();
        })
        .then(data => {
            displayFlightResults(data);
        })
        .catch(error => {
            flightResults.innerHTML = `<p class="error">Erro: ${error.message}</p>`;
        });
}

// Função para exibir os resultados da busca de voos
function displayFlightResults(data) {
    const flightResults = document.getElementById('flight-results');
    
    // Limpar resultados anteriores
    flightResults.innerHTML = '';
    
    // Verificar se há dados ou se ocorreu um erro
    if (data.error) {
        flightResults.innerHTML = `<p class="error">${data.error}</p>`;
        return;
    }
    
    // Verificar se há ofertas de voos
    if (!data.data || data.data.length === 0) {
        flightResults.innerHTML = '<p>Nenhum voo encontrado com os critérios informados.</p>';
        return;
    }
    
    // Exibir cada oferta de voo
    data.data.forEach(offer => {
        const flightCard = document.createElement('div');
        flightCard.className = 'flight-card';
        
        // Informações básicas do voo
        const price = offer.price?.total || 'Preço indisponível';
        const currency = offer.price?.currency || 'EUR';
        
        let html = `
            <h3>Voo ${offer.id}</h3>
            <p><strong>Preço:</strong> ${price} ${currency}</p>
        `;
        
        // Informações dos itinerários
        if (offer.itineraries && offer.itineraries.length > 0) {
            html += '<div class="itineraries">';
            
            offer.itineraries.forEach((itinerary, index) => {
                const isOutbound = index === 0;
                html += `<div class="itinerary ${isOutbound ? 'outbound' : 'inbound'}">`;
                html += `<h4>${isOutbound ? 'Ida' : 'Volta'}</h4>`;
                
                // Informações dos segmentos (voos)
                if (itinerary.segments && itinerary.segments.length > 0) {
                    itinerary.segments.forEach((segment, segIndex) => {
                        const departure = segment.departure || {};
                        const arrival = segment.arrival || {};
                        
                        html += `
                            <div class="segment">
                                <p><strong>Voo ${segIndex + 1}:</strong> ${segment.carrierCode || ''} ${segment.number || ''}</p>
                                <p><strong>De:</strong> ${departure.iataCode || ''} às ${formatTime(departure.at)}</p>
                                <p><strong>Para:</strong> ${arrival.iataCode || ''} às ${formatTime(arrival.at)}</p>
                            </div>
                        `;
                    });
                }
                
                html += '</div>'; // Fim do itinerário
            });
            
            html += '</div>'; // Fim dos itinerários
        }
        
        flightCard.innerHTML = html;
        flightResults.appendChild(flightCard);
    });
}

// Função para formatar a hora de um datetime ISO
function formatTime(isoDatetime) {
    if (!isoDatetime) return 'N/A';
    
    const date = new Date(isoDatetime);
    return date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}


// Aguardar o carregamento completo do DOM
document.addEventListener('DOMContentLoaded', function() {
    // Obter referência ao formulário e container de resultados
    const flightSearchForm = document.getElementById('flight-search-form');
    const flightResults = document.getElementById('flight-results');
    
    // Definir data mínima nos campos de data (hoje)
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('departure-date').min = today;
    document.getElementById('return-date').min = today;
    
    // Preencher com datas padrão (para teste)
    const nextMonth = new Date();
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    const twoMonths = new Date();
    twoMonths.setMonth(twoMonths.getMonth() + 2);
    
    document.getElementById('departure-date').value = nextMonth.toISOString().split('T')[0];
    document.getElementById('return-date').value = twoMonths.toISOString().split('T')[0];
    
    // Adicionar evento de envio ao formulário
    if (flightSearchForm) {
        flightSearchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Mostrar mensagem de carregamento
            flightResults.innerHTML = '<p class="loading">Buscando voos, aguarde...</p>';
            
            // Obter valores do formulário
            const formData = new FormData(flightSearchForm);
            
            // Construir URL com parâmetros de consulta
            const params = new URLSearchParams();
            for (const [key, value] of formData.entries()) {
                if (value) params.append(key, value);
            }
            
            try {
                // Fazer a requisição para a API
                const response = await fetch(`/api/search-flights?${params.toString()}`);
                const data = await response.json();
                
                // Verificar se houve erro
                if (data.error) {
                    flightResults.innerHTML = `<p class="error">Erro: ${data.error}</p>`;
                    return;
                }
                
                // Exibir resultados
                displayFlightResults(data);
            } catch (error) {
                console.error('Erro na busca de voos:', error);
                flightResults.innerHTML = `<p class="error">Erro ao buscar voos. Tente novamente.</p>`;
            }
        });
    }
    
    // Função para exibir os resultados de voos
    function displayFlightResults(data) {
        // Verificar se há dados de voos
        if (!data.data || data.data.length === 0) {
            flightResults.innerHTML = '<p>Nenhum voo encontrado para os critérios informados.</p>';
            return;
        }
        
        // Limitar a 10 resultados para melhor performance
        const flights = data.data.slice(0, 10);
        
        // Criar HTML para os resultados
        let resultsHTML = `<p>Encontrados ${data.data.length} voos. Mostrando os primeiros 10:</p>`;
        
        flights.forEach((flight, index) => {
            const price = flight.price ? flight.price.grandTotal : 'Preço não disponível';
            const currency = flight.price ? flight.price.currency : '';
            
            resultsHTML += `
                <div class="flight-card">
                    <div class="flight-header">
                        <span class="flight-price">${price} ${currency}</span>
                        <span class="flight-airline">${getAirlineName(flight)}</span>
                    </div>
                    
                    <div class="flight-details">
                        ${generateItineraryHTML(flight.itineraries)}
                    </div>
                </div>
            `;
        });
        
        // Inserir HTML no container de resultados
        flightResults.innerHTML = resultsHTML;
    }
    
    // Função para obter o nome da companhia aérea
    function getAirlineName(flight) {
        if (flight.validatingAirlineCodes && flight.validatingAirlineCodes.length > 0) {
            return `Companhia: ${flight.validatingAirlineCodes[0]}`;
        }
        return 'Companhia não especificada';
    }
    
    // Função para gerar HTML do itinerário
    function generateItineraryHTML(itineraries) {
        if (!itineraries || itineraries.length === 0) {
            return '<p>Detalhes do itinerário não disponíveis</p>';
        }
        
        let html = '';
        
        itineraries.forEach((itinerary, index) => {
            const isOutbound = index === 0;
            const label = isOutbound ? 'Ida' : 'Volta';
            
            html += `<div class="flight-segment"><h4>${label}</h4>`;
            
            if (itinerary.segments && itinerary.segments.length > 0) {
                itinerary.segments.forEach(segment => {
                    const departure = segment.departure;
                    const arrival = segment.arrival;
                    
                    html += `
                        <div class="segment-details">
                            <div class="segment-times">
                                <span class="flight-time">${formatTime(departure.at)}</span>
                                <span class="flight-arrow">→</span>
                                <span class="flight-time">${formatTime(arrival.at)}</span>
                            </div>
                            <div class="segment-airports">
                                <span class="flight-airport">${departure.iataCode}</span>
                                <span class="flight-duration">${formatDuration(segment.duration)}</span>
                                <span class="flight-airport">${arrival.iataCode}</span>
                            </div>
                        </div>
                    `;
                });
            }
            
            html += '</div>';
        });
        
        return html;
    }
    
    // Função para formatar data/hora
    function formatTime(dateTimeStr) {
        if (!dateTimeStr) return 'N/A';
        
        const date = new Date(dateTimeStr);
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }
    
    // Função para formatar duração
    function formatDuration(durationStr) {
        if (!durationStr) return '';
        
        // Formato PT2H30M (2 horas e 30 minutos)
        const hours = durationStr.match(/(\d+)H/);
        const minutes = durationStr.match(/(\d+)M/);
        
        let formatted = '';
        if (hours) formatted += `${hours[1]}h `;
        if (minutes) formatted += `${minutes[1]}m`;
        
        return formatted.trim();
    }
});

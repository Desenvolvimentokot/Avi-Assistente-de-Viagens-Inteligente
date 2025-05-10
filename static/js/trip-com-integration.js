/**
 * Script de integração com o Trip.com para busca de voos
 * Este script fornece funções para carregar o iframe do Trip.com
 * e extrair os resultados de voos para uso no aplicativo.
 */

// Namespace para a integração do Trip.com
window.tripComIntegration = (function() {
    // Mapeamento de códigos de aeroporto para códigos de cidade do Trip.com
    const airportToCityMap = {
        'GRU': 'sao_paulo',    // São Paulo - Guarulhos
        'CGH': 'sao_paulo',    // São Paulo - Congonhas
        'VCP': 'sao_paulo',    // São Paulo - Viracopos
        'GIG': 'rio_de_janeiro', // Rio de Janeiro - Galeão
        'SDU': 'rio_de_janeiro', // Rio de Janeiro - Santos Dumont
        'BSB': 'brasilia',     // Brasília
        'CNF': 'belo_horizonte', // Belo Horizonte - Confins
        'PLU': 'belo_horizonte', // Belo Horizonte - Pampulha
        'SSA': 'salvador',     // Salvador
        'REC': 'recife',       // Recife
        'FOR': 'fortaleza',    // Fortaleza
        'CWB': 'curitiba',     // Curitiba
        'POA': 'porto_alegre', // Porto Alegre
        'FLN': 'florianopolis', // Florianópolis
        'MAO': 'manaus',       // Manaus
        'BEL': 'belem',        // Belém
        'CGB': 'cuiaba',       // Cuiabá
        'CGR': 'campo_grande', // Campo Grande
        'NAT': 'natal',        // Natal
        'MCZ': 'maceio',       // Maceió
        'VIX': 'vitoria',      // Vitória
        'GYN': 'goiania',      // Goiânia
        
        // Aeroportos internacionais populares
        'JFK': 'new_york',     // Nova York - John F. Kennedy
        'LGA': 'new_york',     // Nova York - LaGuardia
        'EWR': 'new_york',     // Nova York - Newark
        'LAX': 'los_angeles',  // Los Angeles
        'MIA': 'miami',        // Miami
        'LHR': 'london',       // Londres - Heathrow
        'CDG': 'paris',        // Paris - Charles de Gaulle
        'FCO': 'rome',         // Roma - Fiumicino
        'MAD': 'madrid',       // Madri
        'BCN': 'barcelona',    // Barcelona
        'FRA': 'frankfurt',    // Frankfurt
        'AMS': 'amsterdam',    // Amsterdã
        'MEX': 'mexico_city',  // Cidade do México
        'EZE': 'buenos_aires', // Buenos Aires - Ezeiza
        'GRU': 'sao_paulo',    // São Paulo - Guarulhos
        'SCL': 'santiago',     // Santiago
        'LIM': 'lima',         // Lima
        'BOG': 'bogota',       // Bogotá
        'SYD': 'sydney',       // Sydney
        'MEL': 'melbourne',    // Melbourne
        'NRT': 'tokyo',        // Tóquio - Narita
        'HND': 'tokyo',        // Tóquio - Haneda
        'ICN': 'seoul',        // Seul - Incheon
        'PEK': 'beijing',      // Pequim
        'PVG': 'shanghai',     // Xangai - Pudong
        'HKG': 'hong_kong',    // Hong Kong
        'BKK': 'bangkok',      // Bangkok
        'SIN': 'singapore',    // Singapura
        'DXB': 'dubai',        // Dubai
        'DOH': 'doha',         // Doha
        'IST': 'istanbul',     // Istambul
    };

    /**
     * Converte código de aeroporto para código de cidade
     * @param {string} airportCode - Código IATA do aeroporto
     * @returns {string} - Código da cidade correspondente
     */
    function getCityCodeFromAirport(airportCode) {
        return airportToCityMap[airportCode] || airportCode.toLowerCase();
    }

    /**
     * Formata data para o formato esperado pelo Trip.com (MM-DD-YYYY)
     * @param {string} dateString - Data no formato YYYY-MM-DD
     * @returns {string} - Data no formato MM-DD-YYYY
     */
    function formatDateForTrip(dateString) {
        if (!dateString) return '';
        const [year, month, day] = dateString.split('-');
        return `${month}-${day}-${year}`;
    }

    /**
     * Carrega iframe do Trip.com com os parâmetros fornecidos
     * @param {Object} params - Parâmetros da busca
     * @param {string} params.origin - Código IATA do aeroporto de origem
     * @param {string} params.destination - Código IATA do aeroporto de destino
     * @param {string} params.departureDate - Data de ida (YYYY-MM-DD)
     * @param {string} params.returnDate - Data de volta (YYYY-MM-DD), opcional
     * @param {number} params.adults - Número de adultos, padrão 1
     * @param {string} containerSelector - Seletor CSS do contêiner para o iframe
     * @returns {string} - URL gerada para o Trip.com
     */
    function loadTripComIframe(params, containerSelector) {
        console.log("Carregando iframe do Trip.com com parâmetros:", params);
        
        const origin = params.origin;
        const destination = params.destination;
        const departureDate = params.departureDate;
        const returnDate = params.returnDate;
        const adults = params.adults || 1;
        
        // Obter os códigos de cidade
        const dcity = getCityCodeFromAirport(origin);
        const acity = getCityCodeFromAirport(destination);
        
        // Formatar datas
        const formattedDepartureDate = formatDateForTrip(departureDate);
        const formattedReturnDate = formatDateForTrip(returnDate);
        
        // Construir a URL do Trip.com
        const tripUrl = `https://br.trip.com/flights/showfarefirst?dcity=${dcity}&acity=${acity}&ddate=${formattedDepartureDate}&dairport=${origin}${returnDate ? '&rdate=' + formattedReturnDate + '&triptype=rt' : '&triptype=ow'}&class=y&quantity=${adults}&locale=pt-BR&curr=BRL`;
        
        console.log("URL do Trip.com gerada:", tripUrl);
        
        // Criar iframe e inseri-lo no contêiner
        const container = document.querySelector(containerSelector);
        if (container) {
            const iframe = document.createElement('iframe');
            iframe.src = tripUrl;
            iframe.style.width = '100%';
            iframe.style.height = '800px';
            iframe.style.border = 'none';
            iframe.id = 'tripWidget';
            
            // Limpar o contêiner e adicionar o iframe
            container.innerHTML = '';
            container.appendChild(iframe);
            
            console.log("Iframe do Trip.com adicionado ao contêiner");
        } else {
            console.error("Contêiner não encontrado:", containerSelector);
        }
        
        return tripUrl;
    }

    /**
     * Extrai os resultados de voos do iframe do Trip.com
     * @returns {Promise<Array>} - Promise com array de resultados de voos
     */
    function extractFlightResults() {
        return new Promise((resolve, reject) => {
            console.log("Iniciando extração de resultados de voos");
            
            try {
                // Tentar obter resultados do DOM do iframe
                const iframe = document.getElementById('tripWidget');
                if (iframe && iframe.contentDocument) {
                    console.log("Iframe acessível, tentando extrair resultados");
                    
                    // Esta parte pode não funcionar devido a restrições de CORS
                    // É mantida como referência para o caso de alguns browsers permitirem
                    try {
                        const flightCards = iframe.contentDocument.querySelectorAll('.flight-card');
                        if (flightCards && flightCards.length > 0) {
                            console.log(`Encontrados ${flightCards.length} cards de voos`);
                            
                            const results = Array.from(flightCards).map((card, index) => {
                                try {
                                    const airline = card.querySelector('.airline-name')?.textContent.trim() || 'Não identificada';
                                    const price = card.querySelector('.price-amount')?.textContent.trim() || '0';
                                    const duration = card.querySelector('.duration')?.textContent.trim() || '';
                                    
                                    return {
                                        id: `flight-${index}`,
                                        airline: airline,
                                        price: parseFloat(price.replace(/[^\d,]/g, '').replace(',', '.')),
                                        duration: duration,
                                        raw_data: card.outerHTML
                                    };
                                } catch (err) {
                                    console.error("Erro ao extrair dados do card:", err);
                                    return null;
                                }
                            }).filter(item => item !== null);
                            
                            console.log(`Extraídos ${results.length} resultados de voos`);
                            resolve(results);
                            return;
                        }
                    } catch (corsError) {
                        console.warn("Erro de CORS ao tentar acessar o conteúdo do iframe:", corsError);
                    }
                }
                
                // Não foi possível extrair dados do iframe devido a restrições de CORS
                console.warn("Não foi possível extrair dados do iframe, buscando DADOS REAIS da API TravelPayouts");
                
                // Array temporário para armazenar os resultados que virão da API
                let results = [];
                
                // Buscar dados EXCLUSIVAMENTE da API TravelPayouts - SEM FALLBACK para dados simulados
                fetch('/api/travelpayouts/test')
                    .then(response => response.json())
                    .then(data => {
                        console.log("Dados reais obtidos da API TravelPayouts:", data);
                        if (data.success && data.data && data.data.length > 0) {
                            // Converter os dados para o formato esperado
                            const apiResults = data.data.map((flight, index) => {
                                return {
                                    id: `tp-real-${index}`,
                                    airline: flight.airline || flight.carrier || 'Não identificada',
                                    price: parseFloat(flight.price),
                                    duration: flight.duration_to || flight.total_duration || '?',
                                    departure_time: flight.departure_at || flight.departure || '?',
                                    arrival_time: flight.arrival_at || flight.arrival || '?',
                                    stops: flight.transfers || flight.stops || 0,
                                    source: 'TravelPayouts API (Dados Reais)'
                                };
                            });
                            
                            console.log(`Obtidos ${apiResults.length} resultados reais da API`);
                            resolve(apiResults);
                        } else {
                            // NUNCA usar dados simulados - informar que não há dados disponíveis
                            console.error("Nenhum dado obtido da API TravelPayouts");
                            resolve([]);  // Retorna array vazio ao invés de dados simulados
                        }
                    })
                    .catch(error => {
                        console.error("Erro ao buscar dados da API:", error);
                        resolve([]);  // Retorna array vazio em caso de erro - NUNCA dados simulados
                    });
            } catch (error) {
                console.error("Erro ao extrair resultados de voos:", error);
                reject(error);
            }
        });
    }

    /**
     * Envia os resultados da busca para o servidor
     * @param {string} sessionId - ID da sessão do chat
     * @param {Array} results - Resultados da busca
     * @param {string} tripUrl - URL da busca no Trip.com
     * @returns {Promise} - Promise da requisição
     */
    function sendResultsToServer(sessionId, results, tripUrl) {
        console.log(`Enviando ${results.length} resultados para o servidor`);
        
        return fetch('/api/hidden-search/save-results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                flights: results,
                session_id: sessionId,
                url: tripUrl
            })
        });
    }

    // Exportar funções públicas
    return {
        getCityCodeFromAirport,
        formatDateForTrip,
        loadTripComIframe,
        extractFlightResults,
        sendResultsToServer
    };
})();
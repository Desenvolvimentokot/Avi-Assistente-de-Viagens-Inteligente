/**
 * Script para o botão que redireciona para o Trip.com
 * Este script cria um botão que redireciona para a página de busca do Trip.com
 * com os parâmetros fornecidos.
 */

class TripComButton {
    /**
     * Cria uma instância do botão do Trip.com
     * @param {HTMLElement} container - Elemento onde o botão será adicionado
     * @param {Object} options - Opções de configuração
     * @param {string} options.origin - Código IATA do aeroporto de origem
     * @param {string} options.destination - Código IATA do aeroporto de destino
     * @param {string} options.departureDate - Data de ida (YYYY-MM-DD)
     * @param {string} options.returnDate - Data de volta (YYYY-MM-DD), opcional
     * @param {number} options.adults - Número de adultos, padrão 1
     * @param {string} options.text - Texto do botão, padrão 'Ver no Trip.com'
     * @param {string} options.className - Classes CSS para o botão
     */
    constructor(container, options) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = Object.assign({
            origin: 'GRU',
            destination: 'JFK',
            departureDate: this.getTomorrowDate(),
            returnDate: '',
            adults: 1,
            text: 'Ver no Trip.com',
            className: 'trip-com-button'
        }, options);
        
        this.airportToCityMap = {
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
            'LAX': 'los_angeles',  // Los Angeles
            'MIA': 'miami',        // Miami
            'LHR': 'london',       // Londres - Heathrow
            'CDG': 'paris',        // Paris - Charles de Gaulle
            'FCO': 'rome',         // Roma - Fiumicino
            'MAD': 'madrid',       // Madri
            'BCN': 'barcelona',    // Barcelona
            'FRA': 'frankfurt',    // Frankfurt
            'AMS': 'amsterdam',    // Amsterdã
        };
        
        this.init();
    }
    
    /**
     * Obtém a data de amanhã no formato YYYY-MM-DD
     * @returns {string} - Data de amanhã
     */
    getTomorrowDate() {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const year = tomorrow.getFullYear();
        const month = String(tomorrow.getMonth() + 1).padStart(2, '0');
        const day = String(tomorrow.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    /**
     * Converte código de aeroporto para código de cidade
     * @param {string} airportCode - Código IATA do aeroporto
     * @returns {string} - Código da cidade correspondente
     */
    getCityCodeFromAirport(airportCode) {
        return this.airportToCityMap[airportCode] || airportCode.toLowerCase();
    }
    
    /**
     * Formata data para o formato esperado pelo Trip.com (MM-DD-YYYY)
     * @param {string} dateString - Data no formato YYYY-MM-DD
     * @returns {string} - Data no formato MM-DD-YYYY
     */
    formatDateForTrip(dateString) {
        if (!dateString) return '';
        const [year, month, day] = dateString.split('-');
        return `${month}-${day}-${year}`;
    }
    
    /**
     * Constrói a URL do Trip.com com os parâmetros fornecidos
     * @returns {string} - URL para o Trip.com
     */
    buildTripUrl() {
        const dcity = this.getCityCodeFromAirport(this.options.origin);
        const acity = this.getCityCodeFromAirport(this.options.destination);
        const formattedDepartureDate = this.formatDateForTrip(this.options.departureDate);
        const formattedReturnDate = this.formatDateForTrip(this.options.returnDate);
        
        return `https://br.trip.com/flights/showfarefirst?dcity=${dcity}&acity=${acity}&ddate=${formattedDepartureDate}&dairport=${this.options.origin}${this.options.returnDate ? '&rdate=' + formattedReturnDate + '&triptype=rt' : '&triptype=ow'}&class=y&quantity=${this.options.adults}&locale=pt-BR&curr=BRL`;
    }
    
    /**
     * Inicializa o botão do Trip.com
     */
    init() {
        // Criar o botão
        const button = document.createElement('a');
        button.href = this.buildTripUrl();
        button.className = this.options.className;
        button.textContent = this.options.text;
        button.target = '_blank';
        button.rel = 'noopener noreferrer';
        
        // Estilos inline básicos (podem ser substituídos via CSS)
        Object.assign(button.style, {
            display: 'inline-block',
            padding: '10px 15px',
            backgroundColor: '#0062cc',
            color: 'white',
            borderRadius: '4px',
            textDecoration: 'none',
            fontWeight: 'bold',
            cursor: 'pointer',
            textAlign: 'center',
            margin: '10px 0'
        });
        
        // Adicionar evento de clique para rastreamento
        button.addEventListener('click', this.handleClick.bind(this));
        
        // Adicionar o botão ao contêiner
        if (this.container) {
            this.container.appendChild(button);
        } else {
            console.error('Contêiner não encontrado para o botão do Trip.com');
        }
    }
    
    /**
     * Manipula o evento de clique no botão
     * @param {Event} event - Evento de clique
     */
    handleClick(event) {
        // Rastrear clique via Google Analytics ou outro sistema
        if (window.gtag) {
            window.gtag('event', 'click', {
                'event_category': 'trip_com',
                'event_label': 'redirect',
                'value': 1
            });
        }
        
        // Você pode adicionar mais lógica aqui se necessário
        console.log('Clique no botão do Trip.com:', {
            url: event.target.href,
            params: {
                origin: this.options.origin,
                destination: this.options.destination,
                departureDate: this.options.departureDate,
                returnDate: this.options.returnDate,
                adults: this.options.adults
            }
        });
    }
    
    /**
     * Atualiza as opções do botão e reconstrói a URL
     * @param {Object} newOptions - Novas opções
     */
    updateOptions(newOptions) {
        this.options = Object.assign(this.options, newOptions);
        
        // Atualizar a URL do botão
        const button = this.container.querySelector('.' + this.options.className);
        if (button) {
            button.href = this.buildTripUrl();
            button.textContent = this.options.text;
        }
    }
    
    /**
     * Remove o botão do DOM
     */
    destroy() {
        const button = this.container.querySelector('.' + this.options.className);
        if (button) {
            button.removeEventListener('click', this.handleClick);
            button.remove();
        }
    }
}

// Exportar para uso global
window.TripComButton = TripComButton;
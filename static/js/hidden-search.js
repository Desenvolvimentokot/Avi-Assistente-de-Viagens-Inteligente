/**
 * Script para gerenciar a busca oculta de voos usando iframe invisível
 * Este script é carregado na página de chat e gerencia o ciclo de vida do iframe
 * que vai carregar o widget Trip.com invisível.
 */

(function() {
    // Estado do iframe invisível
    let hiddenFrame = null;
    let searchInProgress = false;
    let searchTimeout = null;

    // Referências para elementos da UI
    const chatContainer = document.getElementById('chat-messages') || document.body;
    
    /**
     * Inicia uma busca oculta de voos
     * @param {string} origin Código IATA de origem
     * @param {string} destination Código IATA de destino
     * @param {string} departureDate Data de partida (YYYY-MM-DD)
     * @param {string} returnDate Data de retorno (opcional)
     * @param {number} adults Número de adultos
     * @returns {Promise} Promise que resolve quando a busca é iniciada
     */
    function startHiddenSearch(origin, destination, departureDate, returnDate, adults = 1) {
        // Evitar múltiplas buscas simultâneas
        if (searchInProgress) {
            console.log('Busca já em andamento, aguarde...');
            return Promise.reject('Busca já em andamento');
        }
        
        // Mostrar indicador de carregamento
        showLoadingIndicator('Buscando os melhores voos para você...');
        
        // Marcar busca como em andamento
        searchInProgress = true;
        
        // Enviar requisição para iniciar busca
        return fetch('/api/hidden-flight-search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                origin: origin,
                destination: destination,
                departure_date: departureDate,
                return_date: returnDate,
                adults: adults
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                throw new Error(data.message || 'Erro ao iniciar busca');
            }
            
            // Criar e configurar iframe invisível
            createHiddenFrame(data.url);
            
            // Configurar timeout para evitar que a busca fique presa
            setSearchTimeout();
            
            return data;
        })
        .catch(error => {
            console.error('Erro ao iniciar busca oculta:', error);
            hideLoadingIndicator();
            searchInProgress = false;
            throw error;
        });
    }
    
    /**
     * Cria um iframe invisível para carregar a página de busca
     * @param {string} url URL da página de busca
     */
    function createHiddenFrame(url) {
        // Remover iframe anterior, se existir
        if (hiddenFrame && hiddenFrame.parentNode) {
            hiddenFrame.parentNode.removeChild(hiddenFrame);
        }
        
        // Criar novo iframe
        hiddenFrame = document.createElement('iframe');
        hiddenFrame.style.width = '0';
        hiddenFrame.style.height = '0';
        hiddenFrame.style.border = 'none';
        hiddenFrame.style.position = 'absolute';
        hiddenFrame.style.left = '-9999px';
        hiddenFrame.style.top = '-9999px';
        hiddenFrame.style.opacity = '0';
        hiddenFrame.style.pointerEvents = 'none';
        hiddenFrame.setAttribute('title', 'Busca de voos invisível');
        hiddenFrame.setAttribute('aria-hidden', 'true');
        
        // Configurar URL
        hiddenFrame.src = url;
        
        // Adicionar ao DOM
        document.body.appendChild(hiddenFrame);
        
        console.log('Iframe invisível criado para URL:', url);
    }
    
    /**
     * Configura um timeout para a busca, para evitar que fique presa
     */
    function setSearchTimeout() {
        // Limpar timeout anterior, se existir
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Configurar novo timeout (60 segundos)
        searchTimeout = setTimeout(() => {
            console.log('Timeout da busca atingido (60s)');
            
            // Remover iframe
            if (hiddenFrame && hiddenFrame.parentNode) {
                hiddenFrame.parentNode.removeChild(hiddenFrame);
                hiddenFrame = null;
            }
            
            // Resetar estado
            searchInProgress = false;
            
            // Esconder indicador de carregamento
            hideLoadingIndicator();
            
            // Adicionar mensagem de erro ao chat
            addErrorMessageToChat('Não consegui encontrar voos para o seu destino. Pode tentar novamente ou buscar outro destino?');
        }, 60000);
    }
    
    /**
     * Finaliza a busca oculta e limpa recursos
     */
    function finishSearch() {
        // Limpar timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
            searchTimeout = null;
        }
        
        // Remover iframe
        if (hiddenFrame && hiddenFrame.parentNode) {
            hiddenFrame.parentNode.removeChild(hiddenFrame);
            hiddenFrame = null;
        }
        
        // Resetar estado
        searchInProgress = false;
        
        // Esconder indicador de carregamento
        hideLoadingIndicator();
    }
    
    /**
     * Verifica se há resultados de voos disponíveis
     * @returns {Promise} Promise que resolve com os resultados, se disponíveis
     */
    function checkFlightResults() {
        return fetch('/api/chat-flight-results', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                // Encontrou resultados
                finishSearch();
                return data.results;
            }
            
            // Sem resultados disponíveis ainda
            return null;
        })
        .catch(error => {
            console.error('Erro ao verificar resultados:', error);
            return null;
        });
    }
    
    /**
     * Mostra indicador de carregamento
     * @param {string} message Mensagem a ser exibida
     */
    function showLoadingIndicator(message) {
        // Verificar se já existe um indicador
        let loadingIndicator = document.getElementById('search-loading-indicator');
        
        if (!loadingIndicator) {
            // Criar indicador
            loadingIndicator = document.createElement('div');
            loadingIndicator.id = 'search-loading-indicator';
            loadingIndicator.className = 'loading-indicator';
            
            // Criar spinner
            const spinner = document.createElement('div');
            spinner.className = 'loading-spinner';
            loadingIndicator.appendChild(spinner);
            
            // Criar texto
            const text = document.createElement('p');
            text.className = 'loading-text';
            loadingIndicator.appendChild(text);
            
            // Estilizar
            loadingIndicator.style.display = 'flex';
            loadingIndicator.style.flexDirection = 'column';
            loadingIndicator.style.alignItems = 'center';
            loadingIndicator.style.justifyContent = 'center';
            loadingIndicator.style.padding = '15px';
            loadingIndicator.style.margin = '10px 0';
            loadingIndicator.style.backgroundColor = '#f5f7fa';
            loadingIndicator.style.borderRadius = '8px';
            
            spinner.style.border = '4px solid #f3f3f3';
            spinner.style.borderTop = '4px solid #2681ff';
            spinner.style.borderRadius = '50%';
            spinner.style.width = '30px';
            spinner.style.height = '30px';
            spinner.style.animation = 'spin 1s linear infinite';
            
            // Inserir estilo de animação se ainda não existir
            if (!document.getElementById('loading-spinner-style')) {
                const style = document.createElement('style');
                style.id = 'loading-spinner-style';
                style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
                document.head.appendChild(style);
            }
            
            // Adicionar ao chat
            chatContainer.appendChild(loadingIndicator);
        }
        
        // Atualizar texto
        const textElement = loadingIndicator.querySelector('.loading-text');
        if (textElement) {
            textElement.textContent = message;
        }
    }
    
    /**
     * Esconde o indicador de carregamento
     */
    function hideLoadingIndicator() {
        const loadingIndicator = document.getElementById('search-loading-indicator');
        if (loadingIndicator && loadingIndicator.parentNode) {
            loadingIndicator.parentNode.removeChild(loadingIndicator);
        }
    }
    
    /**
     * Adiciona uma mensagem de erro ao chat
     * @param {string} message Mensagem de erro
     */
    function addErrorMessageToChat(message) {
        // Esta função depende da implementação específica do chat
        // Aqui assumimos que existe uma função global para isso
        if (typeof addMessageToChat === 'function') {
            addMessageToChat(message, 'bot');
        } else {
            // Fallback: criar elemento de mensagem
            const messageElement = document.createElement('div');
            messageElement.className = 'message bot-message';
            messageElement.textContent = message;
            chatContainer.appendChild(messageElement);
            
            // Scroll para a nova mensagem
            messageElement.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    // Expor funções públicas
    window.hiddenFlightSearch = {
        start: startHiddenSearch,
        finish: finishSearch,
        checkResults: checkFlightResults
    };
})();
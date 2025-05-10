/**
 * Cliente para API do Widget de Voos
 * 
 * Este script fornece uma interface para interagir com a API de busca
 * de voos usando o widget headless do Trip.com (via TravelPayouts)
 */

// Função global para busca de voos - pode ser chamada pelo chat ou botões
window.aviSearchFlights = function(searchParams) {
    // Verificar parâmetros obrigatórios
    if (!searchParams.origin || !searchParams.destination || !searchParams.departure_date) {
        console.error('Parâmetros incompletos para busca de voos');
        return;
    }
    
    // Criar objeto de busca completo com valores padrão para campos opcionais
    const searchObject = {
        origin: searchParams.origin,
        destination: searchParams.destination,
        departure_date: searchParams.departure_date,
        return_date: searchParams.return_date || null,
        adults: searchParams.adults || 1
    };
    
    // Adicionar indicadores visuais de loading
    showFlightSearchingUI();
    
    // Iniciar busca via API
    fetch('/widget-api/start_search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(searchObject)
    })
    .then(response => response.json())
    .then(data => {
        if (data.search_id) {
            // Busca iniciada com sucesso - começar a verificar status
            checkSearchStatus(data.search_id);
        } else {
            // Erro ao iniciar busca
            showSearchError("Não foi possível iniciar a busca de voos");
        }
    })
    .catch(error => {
        console.error('Erro ao iniciar busca:', error);
        showSearchError("Erro ao conectar ao serviço de busca");
    });
};

// Função para verificar status da busca de voos
function checkSearchStatus(searchId) {
    // Atualizar mensagem de progresso
    updateSearchProgress("Buscando melhores ofertas...", 30);
    
    // Verificar status atual
    fetch(`/widget-api/check_status/${searchId}`)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'complete') {
            // Busca concluída - obter resultados
            getSearchResults(searchId);
        } else if (data.status === 'error') {
            // Erro na busca
            showSearchError(data.message || "Erro durante a busca de voos");
        } else {
            // Busca ainda em andamento - atualizar progresso e verificar novamente
            const progressMsg = data.message || "Comparando preços...";
            const progressPct = data.progress || 50;
            updateSearchProgress(progressMsg, progressPct);
            
            // Verificar novamente após 2 segundos
            setTimeout(() => checkSearchStatus(searchId), 2000);
        }
    })
    .catch(error => {
        console.error('Erro ao verificar status:', error);
        showSearchError("Erro ao verificar progresso da busca");
    });
}

// Função para obter resultados da busca
function getSearchResults(searchId) {
    // Atualizar mensagem de progresso
    updateSearchProgress("Carregando resultados...", 90);
    
    // Obter resultados
    fetch(`/widget-api/get_results/${searchId}`)
    .then(response => response.json())
    .then(data => {
        if (data.flights && data.flights.length > 0) {
            // Temos resultados - exibir na interface
            hideLoadingUI();
            
            // Verificar se função para exibição em chat existe
            if (typeof window.displayFlightCardsInChat === 'function') {
                window.displayFlightCardsInChat(data.flights);
            }
            
            // Verificar se função para exibição em painel lateral existe
            if (typeof window.displayFlightsInPanel === 'function') {
                window.displayFlightsInPanel(data.flights);
            }
        } else {
            // Sem resultados
            showSearchError("Não encontramos voos para esta rota nas datas selecionadas");
        }
    })
    .catch(error => {
        console.error('Erro ao obter resultados:', error);
        showSearchError("Erro ao carregar resultados da busca");
    });
}

// Função para mostrar UI de carregamento
function showFlightSearchingUI() {
    // Se estiver em uma página com chat, mostrar loading no chat
    if (document.querySelector('.chat-messages')) {
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'message assistant-message';
        loadingMessage.id = 'flight-search-loading';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        content.innerHTML = `
            <div class="flight-search-progress">
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: 10%"></div>
                </div>
                <p class="progress-message">Iniciando busca de voos...</p>
            </div>
        `;
        
        loadingMessage.appendChild(content);
        document.querySelector('.chat-messages').appendChild(loadingMessage);
        document.querySelector('.chat-messages').scrollTop = document.querySelector('.chat-messages').scrollHeight;
    }
    
    // Se estiver em uma página com painel lateral, mostrar loading no painel
    if (document.getElementById('flight-results-container')) {
        const container = document.getElementById('flight-results-container');
        container.innerHTML = `
            <div class="loading-panel">
                <div class="spinner"></div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: 10%"></div>
                </div>
                <p class="message">Iniciando busca de voos...</p>
            </div>
        `;
    }
}

// Função para atualizar progresso da busca
function updateSearchProgress(message, percent) {
    // Atualizar no chat
    const chatLoading = document.getElementById('flight-search-loading');
    if (chatLoading) {
        const progressBar = chatLoading.querySelector('.progress-bar');
        const progressMessage = chatLoading.querySelector('.progress-message');
        
        if (progressBar) progressBar.style.width = `${percent}%`;
        if (progressMessage) progressMessage.textContent = message;
        
        // Scroll para mostrar mensagem de loading
        const chatMessages = document.querySelector('.chat-messages');
        if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Atualizar no painel lateral
    const panelLoading = document.querySelector('.loading-panel');
    if (panelLoading) {
        const progressBar = panelLoading.querySelector('.progress-bar');
        const progressMessage = panelLoading.querySelector('.message');
        
        if (progressBar) progressBar.style.width = `${percent}%`;
        if (progressMessage) progressMessage.textContent = message;
    }
}

// Função para esconder UI de carregamento
function hideLoadingUI() {
    // Remover do chat
    const chatLoading = document.getElementById('flight-search-loading');
    if (chatLoading) chatLoading.remove();
    
    // Remover do painel lateral
    const panelLoading = document.querySelector('.loading-panel');
    if (panelLoading) panelLoading.remove();
}

// Função para mostrar erro de busca
function showSearchError(message) {
    // Esconder loading
    hideLoadingUI();
    
    // Mostrar erro no chat
    if (document.querySelector('.chat-messages')) {
        const errorMessage = document.createElement('div');
        errorMessage.className = 'message assistant-message';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = `
            <div class="error-message">
                <p><i class="fas fa-exclamation-triangle"></i> ${message}</p>
                <p>Por favor, tente novamente com diferentes datas ou destinos.</p>
            </div>
        `;
        
        errorMessage.appendChild(content);
        document.querySelector('.chat-messages').appendChild(errorMessage);
        document.querySelector('.chat-messages').scrollTop = document.querySelector('.chat-messages').scrollHeight;
    }
    
    // Mostrar erro no painel lateral
    if (document.getElementById('flight-results-container')) {
        document.getElementById('flight-results-container').innerHTML = `
            <div class="error-message">
                <p><i class="fas fa-exclamation-triangle"></i> ${message}</p>
                <p>Por favor, tente novamente com diferentes datas ou destinos.</p>
            </div>
        `;
    }
}
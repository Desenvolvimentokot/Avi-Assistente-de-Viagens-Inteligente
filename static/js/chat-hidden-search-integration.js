/**
 * Script para integrar a busca oculta de voos com o chat da AVI
 * Este script coordena a comunicação entre o chat.js e o hidden-search.js
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando integração de busca oculta com chat');
    
    // Verifica se as dependências estão presentes
    if (!window.hiddenFlightSearch) {
        console.error('Erro: módulo hiddenFlightSearch não encontrado!');
        return;
    }
    
    // Intervalo em milissegundos para verificar os resultados
    const CHECK_INTERVAL = 2000;
    
    // Armazena o ID do intervalo para poder cancelá-lo
    let checkInterval = null;
    
    // Flag para controlar se uma busca está em andamento
    let searchInProgress = false;
    
    // Flag para indicar se estamos esperando resultados para serem usados pelo chat
    let waitingForResults = false;
    
    // Função para iniciar uma busca oculta
    function startHiddenSearch(origin, destination, departureDate, returnDate, adults = 1) {
        if (searchInProgress) {
            console.log('Busca já em andamento, ignorando nova solicitação');
            return Promise.reject('Busca já em andamento');
        }
        
        console.log(`Iniciando busca oculta: ${origin} → ${destination}, ida: ${departureDate}${returnDate ? ', volta: ' + returnDate : ''}`);
        
        searchInProgress = true;
        waitingForResults = true;
        
        // Adicionar mensagem informativa ao chat
        if (typeof addMessage === 'function') {
            addMessage('Buscando as melhores opções de voos para você... Isso pode levar alguns instantes.', false);
        }
        
        // Iniciar a busca oculta
        return window.hiddenFlightSearch.start(origin, destination, departureDate, returnDate, adults)
            .then(data => {
                console.log('Busca oculta iniciada com sucesso:', data);
                
                // Iniciar verificação periódica de resultados
                startCheckingResults();
                
                return data;
            })
            .catch(error => {
                console.error('Erro ao iniciar busca oculta:', error);
                searchInProgress = false;
                waitingForResults = false;
                
                // Adicionar mensagem de erro ao chat
                if (typeof addMessage === 'function') {
                    addMessage('Desculpe, encontrei um problema ao buscar voos. Por favor, tente novamente.', false);
                }
                
                throw error;
            });
    }
    
    // Função para iniciar verificação periódica de resultados
    function startCheckingResults() {
        // Limpar intervalo anterior, se existir
        if (checkInterval) {
            clearInterval(checkInterval);
        }
        
        // Configurar novo intervalo
        checkInterval = setInterval(() => {
            checkForResults();
        }, CHECK_INTERVAL);
        
        // Configurar timeout de segurança (60 segundos)
        setTimeout(() => {
            if (searchInProgress && waitingForResults) {
                // Ainda estamos buscando após 60s, algo deu errado
                clearInterval(checkInterval);
                searchInProgress = false;
                waitingForResults = false;
                
                // Adicionar mensagem de timeout ao chat
                if (typeof addMessage === 'function') {
                    addMessage('Não consegui encontrar voos para este destino dentro do tempo limite. Por favor, tente novamente ou escolha outro destino.', false);
                }
            }
        }, 60000);
    }
    
    // Função para verificar se há resultados disponíveis
    function checkForResults() {
        if (!waitingForResults) {
            // Se não estamos esperando resultados, cancelar o intervalo
            clearInterval(checkInterval);
            return;
        }
        
        console.log('Verificando resultados de voos...');
        
        window.hiddenFlightSearch.checkResults()
            .then(results => {
                if (results && results.length > 0) {
                    // Encontramos resultados!
                    console.log('Resultados de voos encontrados:', results);
                    
                    // Limpar flags e intervalo
                    clearInterval(checkInterval);
                    searchInProgress = false;
                    waitingForResults = false;
                    
                    // Processar resultados
                    processFlightResults(results);
                } else {
                    console.log('Nenhum resultado encontrado ainda, continuando a verificar...');
                }
            })
            .catch(error => {
                console.error('Erro ao verificar resultados:', error);
            });
    }
    
    // Função para processar os resultados de voos
    function processFlightResults(results) {
        console.log('Processando resultados de voos para exibição no chat');
        
        // Formatar os resultados para exibição
        let formattedResults = formatFlightResults(results);
        
        // Adicionar mensagem com os resultados ao chat
        if (typeof addMessage === 'function') {
            addMessage(formattedResults, false);
        }
        
        // Se existir a função para acionar o painel lateral, chamá-la
        triggerFlightPanel(results);
    }
    
    // Função para formatar os resultados de voos para exibição no chat
    function formatFlightResults(results) {
        if (!results || results.length === 0) {
            return 'Não encontrei voos disponíveis para este destino.';
        }
        
        let formattedText = '✅ **Encontrei as seguintes opções de voos para você:**\n\n';
        
        results.forEach((flight, index) => {
            const airline = flight.airline || 'Companhia aérea';
            const origin = flight.origin || 'Origem';
            const destination = flight.destination || 'Destino';
            const departDate = flight.departure_at ? new Date(flight.departure_at).toLocaleDateString('pt-BR') : 'Data de partida';
            const price = typeof flight.price === 'number' ? flight.price.toFixed(2) : flight.price;
            
            formattedText += `**Opção ${index + 1}:** ${airline} - ${origin} para ${destination}\n`;
            formattedText += `📅 ${departDate} | 💰 R$ ${price}\n\n`;
        });
        
        formattedText += 'Posso te ajudar com mais detalhes sobre estas opções ou buscar outras alternativas.';
        
        return formattedText;
    }
    
    // Função para acionar o painel lateral com os resultados
    function triggerFlightPanel(results) {
        // Verificar se o painel lateral existe
        if (window.flightPanel) {
            console.log('Acionando painel lateral com resultados de voos');
            
            // Configurar os resultados no formato esperado pelo painel
            const formattedResults = results.map(flight => {
                return {
                    // Adaptar o formato dos dados conforme necessário
                    airline: flight.airline,
                    flight_number: flight.flight_number,
                    origin: flight.origin,
                    destination: flight.destination,
                    departure_at: flight.departure_at,
                    arrival_at: flight.arrival_at,
                    price: flight.price,
                    currency: 'BRL'
                };
            });
            
            // Configurar os dados no painel e exibi-lo
            window.flightPanel.setFlightData(formattedResults);
            window.flightPanel.show();
        } else {
            console.log('Painel lateral não disponível');
        }
    }
    
    // Expor as funções para o escopo global
    window.hiddenSearchIntegration = {
        startSearch: startHiddenSearch,
        checkResults: checkForResults,
        cancelSearch: function() {
            if (checkInterval) {
                clearInterval(checkInterval);
            }
            searchInProgress = false;
            waitingForResults = false;
            window.hiddenFlightSearch.finish();
        }
    };
    
    // Monitorar mensagens que indicam intenção de busca
    // Isso será integrado pelo backend via API
    console.log('Integração de busca oculta inicializada com sucesso');
});
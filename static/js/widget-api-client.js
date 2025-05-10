/**
 * Widget API Client
 * 
 * Cliente JavaScript para interagir com a API de busca headless usando 
 * o widget Trip.com/TravelPayouts.
 */

class WidgetApiClient {
    constructor() {
        this.baseUrl = window.location.origin;
        this.activeSearchId = null;
        this.pollingInterval = null;
    }

    /**
     * Inicia uma busca de voos usando o widget headless
     * 
     * @param {Object} params - Parâmetros de busca
     * @param {string} params.origin - Código IATA da origem (ex: 'GRU')
     * @param {string} params.destination - Código IATA do destino (ex: 'JFK')
     * @param {string} params.departure_date - Data de ida (formato: 'YYYY-MM-DD')
     * @param {string} [params.return_date] - Data de volta (formato: 'YYYY-MM-DD')
     * @param {number} [params.adults=1] - Número de adultos
     * @param {Function} onStatus - Callback para atualização de status
     * @param {Function} onComplete - Callback para quando a busca for concluída
     * @param {Function} onError - Callback para quando ocorrer um erro
     */
    startSearch(params, onStatus, onComplete, onError) {
        // Cancelar busca anterior se houver
        this.stopPolling();
        
        console.log('Iniciando busca de voos:', params);
        
        // Enviar solicitação para iniciar a busca
        fetch(`${this.baseUrl}/api/widget/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'error') {
                if (onError) onError(data.message);
                return;
            }
            
            this.activeSearchId = data.search_id;
            console.log('Busca iniciada, ID:', this.activeSearchId);
            
            if (onStatus) onStatus('searching', 'Busca iniciada, aguardando resultados...');
            
            // Iniciar polling para verificar o status da busca
            this.startPolling(onStatus, onComplete, onError);
        })
        .catch(error => {
            console.error('Erro ao iniciar busca:', error);
            if (onError) onError('Falha ao iniciar busca: ' + error.message);
        });
    }
    
    /**
     * Inicia polling para verificar o status da busca
     */
    startPolling(onStatus, onComplete, onError) {
        // Verificar se já existe um polling ativo
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        // Variáveis para controle de polling
        let attempts = 0;
        const maxAttempts = 60; // 60 tentativas = 30 segundos com intervalo de 500ms
        
        // Iniciar polling
        this.pollingInterval = setInterval(() => {
            attempts++;
            
            // Verificar se atingiu o número máximo de tentativas
            if (attempts > maxAttempts) {
                clearInterval(this.pollingInterval);
                if (onError) onError('Tempo limite de busca excedido');
                return;
            }
            
            // Chamar API para verificar status
            this.checkStatus(
                status => {
                    if (status === 'complete') {
                        clearInterval(this.pollingInterval);
                        this.fetchResults(onComplete, onError);
                    } else if (status === 'error') {
                        clearInterval(this.pollingInterval);
                        if (onError) onError('Erro durante a busca');
                    } else {
                        if (onStatus) onStatus('searching', `Buscando voos... (${attempts}/${maxAttempts})`);
                    }
                },
                error => {
                    clearInterval(this.pollingInterval);
                    if (onError) onError(error);
                }
            );
        }, 500); // Verificar a cada 500ms
    }
    
    /**
     * Para o polling de status
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
    
    /**
     * Verifica o status de uma busca
     */
    checkStatus(onSuccess, onError) {
        if (!this.activeSearchId) {
            if (onError) onError('Nenhuma busca ativa');
            return;
        }
        
        fetch(`${this.baseUrl}/api/widget/status/${this.activeSearchId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'error') {
                    if (onError) onError(data.message);
                    return;
                }
                
                if (onSuccess) onSuccess(data.status, data);
            })
            .catch(error => {
                console.error('Erro ao verificar status:', error);
                if (onError) onError('Falha ao verificar status: ' + error.message);
            });
    }
    
    /**
     * Busca os resultados de uma busca
     */
    fetchResults(onSuccess, onError) {
        if (!this.activeSearchId) {
            if (onError) onError('Nenhuma busca ativa');
            return;
        }
        
        fetch(`${this.baseUrl}/api/widget/results/${this.activeSearchId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'error') {
                    if (onError) onError(data.message);
                    return;
                }
                
                if (onSuccess) onSuccess(data.results, data);
            })
            .catch(error => {
                console.error('Erro ao buscar resultados:', error);
                if (onError) onError('Falha ao buscar resultados: ' + error.message);
            });
    }
}

// Exportar cliente para uso global
window.widgetApiClient = new WidgetApiClient();
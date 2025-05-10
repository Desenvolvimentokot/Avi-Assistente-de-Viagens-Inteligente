/**
 * Widget API Client
 * 
 * Cliente JavaScript para interagir com a API de busca headless usando 
 * o widget Trip.com/TravelPayouts.
 */

class WidgetApiClient {
    constructor() {
        this.baseUrl = '/widget';
        this.searchId = null;
        this.pollingInterval = null;
        this.pollingDelay = 2000; // 2 segundos
        this.maxPollingAttempts = 30; // 60 segundos total (30 * 2s)
        this.currentAttempt = 0;
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
        // Validar parâmetros obrigatórios
        if (!params.origin || !params.destination || !params.departure_date) {
            onError('Parâmetros de busca incompletos. É necessário fornecer origem, destino e data de ida.');
            return;
        }

        // Callback para atualização de status inicial
        onStatus('searching', 'Iniciando busca de voos...');
        
        // Fazer requisição para iniciar a busca
        fetch(`${this.baseUrl}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro ao iniciar busca: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Armazenar ID da busca
            this.searchId = data.search_id;
            
            // Atualizar status
            onStatus('searching', 'Busca iniciada, aguardando resultados...');
            
            // Iniciar polling para verificar status
            this.startPolling(onStatus, onComplete, onError);
        })
        .catch(error => {
            console.error('Erro ao iniciar busca:', error);
            onError(error.message || 'Erro desconhecido ao iniciar busca');
        });
    }

    /**
     * Inicia polling para verificar o status da busca
     */
    startPolling(onStatus, onComplete, onError) {
        this.currentAttempt = 0;
        
        // Limpar intervalo anterior se existir
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        // Criar novo intervalo de polling
        this.pollingInterval = setInterval(() => {
            this.currentAttempt++;
            
            // Verificar se atingiu o número máximo de tentativas
            if (this.currentAttempt > this.maxPollingAttempts) {
                clearInterval(this.pollingInterval);
                onError('Tempo limite excedido para obter resultados. Por favor, tente novamente mais tarde.');
                return;
            }
            
            // Verificar status da busca
            this.checkStatus(
                // Callback de sucesso
                (statusData) => {
                    // Calcular progresso com base no status
                    const progress = statusData.progress || Math.floor((this.currentAttempt / this.maxPollingAttempts) * 100);
                    
                    // Atualizar mensagem de status
                    onStatus('searching', statusData.message || 'Buscando voos...', progress);
                    
                    // Se a busca estiver concluída, buscar resultados
                    if (statusData.status === 'complete') {
                        clearInterval(this.pollingInterval);
                        
                        // Buscar resultados
                        this.fetchResults(
                            // Callback de sucesso
                            (results) => {
                                onComplete(results);
                            },
                            // Callback de erro
                            (error) => {
                                onError(error);
                            }
                        );
                    }
                },
                // Callback de erro
                (error) => {
                    clearInterval(this.pollingInterval);
                    onError(error);
                }
            );
        }, this.pollingDelay);
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
        if (!this.searchId) {
            onError('ID de busca não disponível');
            return;
        }
        
        fetch(`${this.baseUrl}/status/${this.searchId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erro ao verificar status: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                onSuccess(data);
            })
            .catch(error => {
                console.error('Erro ao verificar status:', error);
                onError(error.message || 'Erro desconhecido ao verificar status');
            });
    }

    /**
     * Busca os resultados de uma busca
     */
    fetchResults(onSuccess, onError) {
        if (!this.searchId) {
            onError('ID de busca não disponível');
            return;
        }
        
        fetch(`${this.baseUrl}/results/${this.searchId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erro ao buscar resultados: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                onSuccess(data.flights || []);
            })
            .catch(error => {
                console.error('Erro ao buscar resultados:', error);
                onError(error.message || 'Erro desconhecido ao buscar resultados');
            });
    }
}

// Criar e exportar instância global
window.widgetApiClient = new WidgetApiClient();
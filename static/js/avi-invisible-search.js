/**
 * Script para integrar a busca invisível (iframe oculto) com o chat da AVI.
 * Este script monitora as mensagens do usuário, detecta intenções de busca de voos,
 * e coordena a busca invisível através do iframe oculto.
 */

(function() {
    // Estado da busca
    let searchInProgress = false;
    let lastExtractedFlightInfo = null;

    // Referências para elementos da UI - inicializadas apenas quando o DOM estiver pronto
    let messageInput;
    let sendButton;
    
    // Função para inicializar os elementos UI quando o DOM estiver pronto
    function initializeUIElements() {
        // Verificar se estamos em uma página que tem o chat
        if (!document.querySelector('.chat-container')) {
            console.log('Chat não encontrado nesta página, pulando inicialização');
            return;
        }
        
        messageInput = document.querySelector('.message-input');
        sendButton = document.querySelector('.send-button');

        // Monitorar o evento de envio de mensagem apenas se os elementos existirem
        if (sendButton && messageInput) {
            console.log('Elementos de UI encontrados, configurando event listeners');
            
            // Interceptar envio de mensagem (botão)
            const originalSendButtonClick = sendButton.onclick;
            sendButton.onclick = function(event) {
                handleUserMessage();
                
                // Chamar o handler original
                if (originalSendButtonClick) {
                    originalSendButtonClick.call(this, event);
                }
            };

            // Interceptar tecla Enter no input - usando try/catch para evitar erros
            try {
                messageInput.addEventListener('keypress', function(event) {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        handleUserMessage();
                        // Não precisamos chamar preventDefault() ou stopPropagation()
                        // porque estamos apenas observando, não substituindo o comportamento
                    }
                });
            } catch (error) {
                console.error("Erro ao configurar listener de keypress:", error);
            }
        } else {
            console.log('Elementos de UI não encontrados, tentando novamente em 1s');
            // Tentar novamente após um atraso (máximo 5 tentativas)
            if (!window.uiInitAttempts) {
                window.uiInitAttempts = 1;
            } else {
                window.uiInitAttempts++;
            }
            
            if (window.uiInitAttempts <= 5) {
                setTimeout(initializeUIElements, 1000);
            } else {
                console.log('Desistindo após 5 tentativas de encontrar elementos UI');
            }
        }
    }
    
    // Inicializar elementos da UI quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeUIElements);
    } else {
        initializeUIElements();
    }

    // Handler para processar mensagem do usuário
    function handleUserMessage() {
        // Verificar se o elemento existe antes de acessar
        if (!messageInput) {
            console.warn('messageInput não está disponível');
            return;
        }
        
        const message = messageInput.value.trim();
        if (!message) return;

        // Fazer requisição para o endpoint de extração de informações
        checkFlightSearchIntent(message);
    }

    // Verificar se a mensagem tem intenção de busca de voos
    function checkFlightSearchIntent(message) {
        fetch('/api/chat-extract-flight', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                context: window.chatContext || {} // Usar contexto do chat, se disponível
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.has_flight_intent) {
                console.log("💡 Intenção de busca de voos detectada:", data.flight_info);
                
                // Salvar informações extraídas
                lastExtractedFlightInfo = data.flight_info;
                
                // Se tiver informações suficientes, iniciar busca
                if (data.flight_info && data.flight_info.ready_for_search) {
                    initiateInvisibleSearch(data.flight_info);
                }
            }
        })
        .catch(error => {
            console.error("Erro ao verificar intenção de busca:", error);
        });
    }

    // Mostrar barra de carregamento na interface
    function showLoadingIndicator() {
        // Verificar se já existe um indicador
        if (document.getElementById('avi-loading-indicator')) {
            return;
        }
        
        // Criar um elemento de indicador de carregamento
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'avi-loading-indicator';
        loadingDiv.style.position = 'fixed';
        loadingDiv.style.top = '10px';
        loadingDiv.style.left = '50%';
        loadingDiv.style.transform = 'translateX(-50%)';
        loadingDiv.style.backgroundColor = '#2681ff';
        loadingDiv.style.color = 'white';
        loadingDiv.style.padding = '10px 20px';
        loadingDiv.style.borderRadius = '20px';
        loadingDiv.style.zIndex = '9999';
        loadingDiv.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        loadingDiv.style.display = 'flex';
        loadingDiv.style.alignItems = 'center';
        loadingDiv.style.gap = '10px';
        
        // Adicionar spinner
        const spinner = document.createElement('div');
        spinner.style.width = '20px';
        spinner.style.height = '20px';
        spinner.style.border = '3px solid rgba(255,255,255,0.3)';
        spinner.style.borderTop = '3px solid white';
        spinner.style.borderRadius = '50%';
        spinner.style.animation = 'avi-spin 1s linear infinite';
        
        // Adicionar estilo de animação
        const style = document.createElement('style');
        style.textContent = '@keyframes avi-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
        document.head.appendChild(style);
        
        // Texto do indicador
        const text = document.createElement('span');
        text.textContent = 'Buscando voos...';
        
        // Montar indicador
        loadingDiv.appendChild(spinner);
        loadingDiv.appendChild(text);
        document.body.appendChild(loadingDiv);
        
        // Configurar remoção automática após 60 segundos (segurança)
        setTimeout(() => {
            if (document.getElementById('avi-loading-indicator')) {
                document.getElementById('avi-loading-indicator').remove();
            }
        }, 60000);
    }
    
    // Remover barra de carregamento
    function hideLoadingIndicator() {
        const indicator = document.getElementById('avi-loading-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    // Iniciar busca invisível usando o iframe oculto
    function initiateInvisibleSearch(flightInfo) {
        if (searchInProgress) {
            console.log("Busca já em andamento, ignorando nova solicitação");
            return;
        }

        console.log("🔍 Iniciando busca invisível:", flightInfo);
        searchInProgress = true;
        
        // Mostrar indicador de carregamento
        showLoadingIndicator();

        // Obter ID de sessão do cookie ou localStorage
        const sessionId = getCookie('flai_session_id') || localStorage.getItem('chat_session_id');

        // Fazer requisição ao endpoint de início de busca
        fetch('/api/initiate-hidden-search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                flight_info: flightInfo,
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.trigger_hidden_search) {
                // Atualizar ID de sessão se necessário
                if (data.session_id) {
                    localStorage.setItem('chat_session_id', data.session_id);
                    setCookie('flai_session_id', data.session_id, 30);
                }
                
                // Iniciar busca oculta usando o objeto correto da integração
                if (window.hiddenSearchIntegration) {
                    console.log("Usando hiddenSearchIntegration para iniciar busca");
                    window.hiddenSearchIntegration.startSearch(
                        flightInfo.origin,
                        flightInfo.destination,
                        flightInfo.departure_date,
                        flightInfo.return_date,
                        flightInfo.adults || 1
                    ).then(() => {
                        console.log("Busca iniciada com sucesso via hiddenSearchIntegration");
                    }).catch(error => {
                        console.error("Erro ao iniciar busca oculta:", error);
                        searchInProgress = false;
                    });
                } else if (window.hiddenFlightSearch) {
                    console.log("Usando hiddenFlightSearch para iniciar busca");
                    window.hiddenFlightSearch.start(
                        flightInfo.origin,
                        flightInfo.destination,
                        flightInfo.departure_date,
                        flightInfo.return_date,
                        flightInfo.adults || 1
                    ).then(() => {
                        console.log("Busca iniciada com sucesso via hiddenFlightSearch");
                    }).catch(error => {
                        console.error("Erro ao iniciar busca oculta:", error);
                        searchInProgress = false;
                    });
                } else {
                    console.error("Nenhum módulo de busca oculta encontrado");
                    searchInProgress = false;
                }
            } else {
                console.log("Não foi possível iniciar busca:", data.message);
                searchInProgress = false;
            }
        })
        .catch(error => {
            console.error("Erro ao iniciar busca:", error);
            searchInProgress = false;
        });
    }

    // Funções auxiliares para manipulação de cookies
    function setCookie(name, value, days) {
        let expires = "";
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + (value || "") + expires + "; path=/";
    }

    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    // Expor funções públicas
    window.aviInvisibleSearch = {
        checkIntent: checkFlightSearchIntent,
        startSearch: initiateInvisibleSearch,
        getLastFlightInfo: function() {
            return lastExtractedFlightInfo;
        }
    };

    console.log("🔄 AVI Invisible Search inicializado");
})();
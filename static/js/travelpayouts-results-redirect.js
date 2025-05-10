/**
 * TravelPayouts Results Redirect
 * 
 * Script para tratar o botão que redireciona para a página de resultados da TravelPayouts.
 * Escuta cliques em botões com a classe 'travelpayouts-results-btn' e extrai os parâmetros
 * para construir a URL de redirecionamento.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Inicializa a detecção de botões de resultados
    initResultsButtons();

    // Se estamos no chat, adiciona um observador para detectar novos botões que podem aparecer
    if (document.getElementById('chat-messages')) {
        setupMutationObserver();
    }
    
    console.log("[tp] entrypoint init");
});

/**
 * Inicializa os botões de resultados existentes na página
 */
function initResultsButtons() {
    const buttons = document.querySelectorAll('.travelpayouts-results-btn');
    buttons.forEach(button => {
        button.addEventListener('click', handleResultsButtonClick);
    });
    console.log(`[tp] Inicializados ${buttons.length} botões de resultados.`);
    
    // Também inicializar os botões antigos (para compatibilidade)
    initLegacyButtons();
}

/**
 * Inicializa os botões antigos da Amadeus para conversão automática
 */
function initLegacyButtons() {
    try {
        const legacyButtons = document.querySelectorAll('.amadeus-results-btn');
        if (legacyButtons && legacyButtons.length > 0) {
            legacyButtons.forEach(button => {
                if (button) {
                    // Converter para a nova classe
                    button.classList.remove('amadeus-results-btn');
                    button.classList.add('travelpayouts-results-btn');
                    
                    // Adicionar handler para o clique
                    button.addEventListener('click', handleResultsButtonClick);
                }
            });
            
            console.log(`[tp] link_switcher convert links`);
        }
    } catch (error) {
        console.log(`[tp] Aviso: não foi possível converter botões antigos: ${error.message}`);
    }
}

/**
 * Configura um observador de mutações para detectar novos botões adicionados ao chat
 */
function setupMutationObserver() {
    try {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) {
            console.log('[tp] Aviso: elemento chat-messages não encontrado');
            return;
        }
        
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                        if (node && node.nodeType === 1) { // Elemento
                            try {
                                // Verificar botões novos
                                const newButtons = node.querySelectorAll('.travelpayouts-results-btn');
                                if (newButtons && newButtons.length > 0) {
                                    newButtons.forEach(button => {
                                        if (button) {
                                            button.addEventListener('click', handleResultsButtonClick);
                                            console.log('[tp] Novo botão de resultados detectado e inicializado.');
                                        }
                                    });
                                }
                                
                                // Converter botões legados
                                const legacyButtons = node.querySelectorAll('.amadeus-results-btn');
                                if (legacyButtons && legacyButtons.length > 0) {
                                    legacyButtons.forEach(button => {
                                        if (button) {
                                            button.classList.remove('amadeus-results-btn');
                                            button.classList.add('travelpayouts-results-btn');
                                            button.addEventListener('click', handleResultsButtonClick);
                                            console.log('[tp] Botão legado convertido e inicializado.');
                                        }
                                    });
                                }
                            } catch (err) {
                                console.log(`[tp] Erro ao processar nó: ${err.message}`);
                            }
                        }
                    });
                }
            });
        });
        
        observer.observe(chatContainer, { childList: true, subtree: true });
        console.log('[tp] link_switcher init');
    } catch (error) {
        console.log(`[tp] Aviso: não foi possível configurar o observador de mutações: ${error.message}`);
    }
}

/**
 * Manipula o clique no botão de resultados
 * @param {Event} event - Evento de clique
 */
function handleResultsButtonClick(event) {
    event.preventDefault();
    
    const button = event.currentTarget;
    
    // Extrair os parâmetros do botão
    const origin = button.getAttribute('data-origin');
    const destination = button.getAttribute('data-destination');
    const departureDate = button.getAttribute('data-departure');
    const adults = button.getAttribute('data-adults');
    
    // CORREÇÃO CRÍTICA: Ignorar o sessionId do botão e usar o que está armazenado no localStorage
    // Isso garante que usamos sempre o ID de sessão correto independente do que a AVI retornar
    let sessionId = localStorage.getItem('chat_session_id');
    
    // Usar ID de sessão do chat armazenado no localStorage ou gerar um se não existir
    if (!sessionId) {
        // Se não encontrar no localStorage, tentar obter do contexto do chat
        sessionId = window.chatSessionId;
    }
    
    // Garantia final: se mesmo assim não tivermos um ID, gerar um novo
    if (!sessionId || sessionId === 'undefined' || sessionId === 'null' || 
        sessionId === '12345' || sessionId === 'SESSION_ID_ATUAL') {
        sessionId = 'session-' + Math.random().toString(36).substring(2, 12);
        console.log('[tp] Gerado novo ID de sessão: ' + sessionId);
    }
    
    console.log('[tp] Clique em botão de resultados detectado.');
    console.log(`[tp] Parâmetros: ${origin} → ${destination}, Data: ${departureDate}, Adultos: ${adults}`);
    console.log(`[tp] Usando session_id confiável: ${sessionId}`);
    
    // Construir a URL para a página de resultados
    let url = `/travelpayouts-results?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`;
    
    if (departureDate) {
        url += `&departure_date=${encodeURIComponent(departureDate)}`;
    }
    
    if (adults) {
        url += `&adults=${encodeURIComponent(adults)}`;
    }
    
    // SEMPRE usar o sessionId validado
    url += `&session_id=${encodeURIComponent(sessionId)}`;
    
    console.log(`[tp] Redirecionando para: ${url}`);
    
    // Abrir a página de resultados em uma nova aba para manter a conversa com a AVI
    window.open(url, '_blank');
}
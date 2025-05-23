/**
 * [COMPATIBILIDADE LEGADA] Amadeus Results Redirect
 * 
 * Script mantido apenas para compatibilidade com páginas antigas.
 * Todos os redirecionamentos agora vão para a página de resultados da TravelPayouts.
 * Escuta cliques em botões com a classe 'amadeus-results-btn' e extrai os parâmetros
 * para construir a URL de redirecionamento.
 * 
 * AVISO: Este arquivo será removido em versões futuras. 
 * Use travelpayouts-results-redirect.js em vez disso.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Inicializa a detecção de botões de resultados
    initResultsButtons();

    // Se estamos no chat, adiciona um observador para detectar novos botões que podem aparecer
    if (document.getElementById('chat-messages')) {
        setupMutationObserver();
    }
});

/**
 * Inicializa os botões de resultados existentes na página
 */
function initResultsButtons() {
    try {
        const buttons = document.querySelectorAll('.amadeus-results-btn');
        if (buttons && buttons.length > 0) {
            buttons.forEach(button => {
                if (button) {
                    button.addEventListener('click', handleResultsButtonClick);
                }
            });
            console.log(`[Amadeus Redirect] Inicializados ${buttons.length} botões de resultados.`);
        } else {
            console.log('[Amadeus Redirect] Nenhum botão para inicializar.');
        }
    } catch (error) {
        console.log(`[Amadeus Redirect] Erro ao inicializar botões: ${error.message}`);
    }
}

/**
 * Configura um observador de mutações para detectar novos botões adicionados ao chat
 */
function setupMutationObserver() {
    try {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) {
            console.log('[Amadeus Redirect] Container de chat não encontrado.');
            return;
        }
        
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                        try {
                            if (node && node.nodeType === 1) { // Elemento
                                const newButtons = node.querySelectorAll('.amadeus-results-btn');
                                if (newButtons && newButtons.length > 0) {
                                    newButtons.forEach(button => {
                                        if (button) {
                                            button.addEventListener('click', handleResultsButtonClick);
                                            console.log('[Amadeus Redirect] Novo botão de resultados detectado e inicializado.');
                                        }
                                    });
                                }
                            }
                        } catch (err) {
                            console.log(`[Amadeus Redirect] Erro ao processar nó: ${err.message}`);
                        }
                    });
                }
            });
        });
        
        observer.observe(chatContainer, { childList: true, subtree: true });
        console.log('[Amadeus Redirect] Observador de mutações configurado para o chat.');
    } catch (error) {
        console.log(`[Amadeus Redirect] Erro ao configurar observador: ${error.message}`);
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
        console.log('[Amadeus Redirect] Gerado novo ID de sessão: ' + sessionId);
    }
    
    console.log('[Amadeus Redirect] Clique em botão de resultados detectado.');
    console.log(`[Amadeus Redirect] Parâmetros: ${origin} → ${destination}, Data: ${departureDate}, Adultos: ${adults}`);
    console.log(`[Amadeus Redirect] Usando session_id confiável: ${sessionId}`);
    
    // Construir a URL para a página de resultados (agora apontando para TravelPayouts)
    let url = `/travelpayouts-results?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`;
    
    if (departureDate) {
        url += `&departure_date=${encodeURIComponent(departureDate)}`;
    }
    
    if (adults) {
        url += `&adults=${encodeURIComponent(adults)}`;
    }
    
    // SEMPRE usar o sessionId validado
    url += `&session_id=${encodeURIComponent(sessionId)}`;
    
    console.log(`[Amadeus Redirect] Redirecionando para TravelPayouts: ${url}`);
    
    // Abrir a página de resultados em uma nova aba para manter a conversa com a AVI
    window.open(url, '_blank');
}
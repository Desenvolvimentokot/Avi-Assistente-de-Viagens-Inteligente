
/**
 * Auto-redirect para a página do widget Trip.com
 * Este script monitora as respostas do chat e redireciona automaticamente
 * quando os dados de viagem são confirmados.
 */

(function() {
    // Verificar se estamos na página de chat
    if (!document.querySelector('.chat-messages')) return;
    
    // Função para verificar novas mensagens e detectar confirmação
    function checkForConfirmation() {
        // Observar mudanças no contêiner de mensagens
        const chatMessages = document.querySelector('.chat-messages');
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Verificar se a última mensagem contém confirmação
                    const lastMessage = chatMessages.lastElementChild;
                    if (lastMessage && lastMessage.classList.contains('assistant-message')) {
                        const messageText = lastMessage.textContent.toLowerCase();
                        
                        // Verificar se há mensagem de confirmação
                        if (
                            (messageText.includes('confirmado') || messageText.includes('confirmei')) && 
                            messageText.includes('dados') && 
                            (messageText.includes('voo') || messageText.includes('viagem'))
                        ) {
                            // Buscar botões de resultados na última mensagem
                            const resultButtons = lastMessage.querySelectorAll('.flight-results-button');
                            
                            if (resultButtons.length > 0) {
                                console.log('Confirmação detectada! Dados confirmados, abrindo página de resultados...');
                                
                                // Clicar automaticamente no primeiro botão de resultados
                                setTimeout(() => {
                                    resultButtons[0].click();
                                }, 1500); // Pequeno delay para garantir que o usuário veja a confirmação
                            }
                        }
                    }
                }
            });
        });
        
        // Configurar o observador
        observer.observe(chatMessages, { childList: true });
        
        console.log('📊 Monitoramento de confirmação de viagem iniciado');
    }
    
    // Iniciar quando o DOM estiver completamente carregado
    document.addEventListener('DOMContentLoaded', function() {
        checkForConfirmation();
    });
    
    // Caso o DOM já esteja carregado
    if (document.readyState === 'interactive' || document.readyState === 'complete') {
        checkForConfirmation();
    }
})();

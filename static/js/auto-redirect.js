
/**
 * Auto-Redirect Script
 * 
 * Este script facilita o redirecionamento automático para a página de resultados do Trip.com
 * quando o usuário confirma os dados da viagem.
 */

(function() {
    console.log("Auto-redirect script carregado");

    // Função para verificar novas mensagens e detectar confirmação
    function checkForConfirmation() {
        // Observar mudanças no contêiner de mensagens
        const chatMessages = document.querySelector('.chat-messages');
        if (!chatMessages) {
            console.log("Container de mensagens não encontrado, tentando novamente em 1 segundo...");
            setTimeout(checkForConfirmation, 1000);
            return;
        }
        
        console.log("Monitorando mensagens do chat para redirecionamento automático");
        
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && node.classList.contains('assistant-message')) {
                            const messageText = node.textContent.toLowerCase();
                            
                            // Verificar se há mensagem de confirmação
                            if ((messageText.includes('confirmado') || messageText.includes('confirmei')) && 
                                messageText.includes('dados') && 
                                (messageText.includes('voo') || messageText.includes('viagem'))) {
                                
                                console.log('Confirmação detectada! Procurando botões de resultados...');
                                
                                // Procurar botões de resultados na mensagem
                                setTimeout(() => {
                                    const resultButtons = node.querySelectorAll('a.travelpayouts-results-btn');
                                    console.log(`Encontrados ${resultButtons.length} botões de resultados`);
                                    
                                    if (resultButtons.length > 0) {
                                        console.log('Clicando automaticamente no primeiro botão de resultados em 1.5 segundos...');
                                        
                                        setTimeout(() => {
                                            try {
                                                resultButtons[0].click();
                                                console.log('Botão clicado automaticamente!');
                                            } catch (err) {
                                                console.error('Erro ao clicar no botão:', err);
                                            }
                                        }, 1500);
                                    }
                                }, 1000);
                            }
                        }
                    });
                }
            });
        });
        
        // Configurar o observador
        observer.observe(chatMessages, { 
            childList: true,
            subtree: true 
        });
        
        console.log('📊 Monitoramento de confirmação de viagem iniciado');
    }
    
    // Função global para abrir a página de resultados
    window.openTripResultsPage = function(origin, destination, departureDate, returnDate, adults) {
        // Construir a URL para a página de resultados
        let url = `/travelpayouts-results?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`;

        if (departureDate) {
            url += `&departure_date=${encodeURIComponent(departureDate)}`;
        }

        if (returnDate) {
            url += `&return_date=${encodeURIComponent(returnDate)}`;
        }

        if (adults) {
            url += `&adults=${encodeURIComponent(adults)}`;
        }

        console.log(`Redirecionando para resultados: ${url}`);
        window.open(url, '_blank');
    };

    // Iniciar quando o DOM estiver completamente carregado
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkForConfirmation);
    } else {
        // O DOM já está pronto
        checkForConfirmation();
    }
})();

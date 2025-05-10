/**
 * TravelPayouts Results Redirect
 * 
 * Este script adiciona funcionalidade aos botões de redirecionamento para a 
 * página de resultados de voos da TravelPayouts.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Função para inicializar os botões no carregamento da página e em futuras atualizações
    function initializeButtons() {
        // Selecionar todos os botões de resultados TravelPayouts
        const buttons = document.querySelectorAll('.travelpayouts-results-btn');
        
        buttons.forEach(button => {
            // Evitar duplicação de event listeners
            if (button.getAttribute('data-initialized') === 'true') return;
            
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Obter parâmetros de busca dos atributos data-*
                const origin = button.getAttribute('data-origin');
                const destination = button.getAttribute('data-destination');
                const departure = button.getAttribute('data-departure');
                const returnDate = button.getAttribute('data-return') || '';
                const adults = button.getAttribute('data-adults') || '1';
                const sessionId = button.getAttribute('data-session') || '';
                
                // Opção 1: Redirecionar para a página de resultados
                const resultsUrl = `/travelpayouts-results?origin=${origin}&destination=${destination}&departure=${departure}&return=${returnDate}&adults=${adults}&session=${sessionId}`;
                
                // Opção 2: Iniciar busca inline usando widget API (se disponível)
                if (typeof window.aviSearchFlights === 'function') {
                    // Construir objeto de parâmetros
                    const searchParams = {
                        origin: origin,
                        destination: destination,
                        departure_date: departure,
                        adults: parseInt(adults)
                    };
                    
                    // Adicionar data de retorno se existir
                    if (returnDate) {
                        searchParams.return_date = returnDate;
                    }
                    
                    // Iniciar busca de voos com exibição no chat
                    window.aviSearchFlights(searchParams);
                } else {
                    // Fallback: redirecionar para página de resultados
                    window.location.href = resultsUrl;
                }
            });
            
            // Marcar botão como inicializado
            button.setAttribute('data-initialized', 'true');
        });
    }
    
    // Inicializar botões no carregamento da página
    initializeButtons();
    
    // Observar mudanças no DOM para inicializar novos botões (como em respostas de chat)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // Verificar se foram adicionados novos botões
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    if (node.nodeType === 1 && node.matches('.travelpayouts-results-btn')) {
                        initializeButtons();
                        break;
                    } else if (node.nodeType === 1 && node.querySelectorAll) {
                        if (node.querySelectorAll('.travelpayouts-results-btn').length > 0) {
                            initializeButtons();
                            break;
                        }
                    }
                }
            }
        });
    });
    
    // Configurar o observador para observar todo o documento
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});
// Script para testar o painel de resultados de voos
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar botão de teste ao DOM
    const testButton = document.createElement('button');
    testButton.id = 'test-flight-panel';
    testButton.innerText = 'Testar Painel de Voos';
    testButton.style.position = 'fixed';
    testButton.style.top = '10px';
    testButton.style.right = '10px';
    testButton.style.zIndex = '9999';
    testButton.style.padding = '8px 12px';
    testButton.style.background = '#4a90e2';
    testButton.style.color = 'white';
    testButton.style.border = 'none';
    testButton.style.borderRadius = '4px';
    testButton.style.cursor = 'pointer';
    
    // Adicionar ao body
    document.body.appendChild(testButton);
    
    // Adicionar evento de clique
    testButton.addEventListener('click', function() {
        console.log("Disparando evento de teste para o painel de voos");
        
        // Simular evento para mostrar o painel com dados de teste
        document.dispatchEvent(new CustomEvent('showFlightResults', {
            detail: {
                sessionId: 'test'
            }
        }));
    });
    
    console.log("Botão de teste do painel de voos adicionado");
});
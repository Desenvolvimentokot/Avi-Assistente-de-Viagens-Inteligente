` tags. The intention is to correct issues with auto-redirection and the `openTripResultsPage` function.

```python
<replit_final_file>
/**
 * Auto-Redirect Script
 * 
 * Este script facilita o redirecionamento automático para a página de resultados do Trip.com
 * quando o usuário confirma os dados da viagem.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Auto-redirect script carregado");

    // Esta função será chamada quando o usuário confirmar os dados da viagem
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

    // Procurar botões de resultados na página
    function checkForResultButtons() {
        const resultButtons = document.querySelectorAll('a.travelpayouts-results-btn');

        if (resultButtons.length > 0) {
            console.log(`Encontrados ${resultButtons.length} botões de resultados na página`);

            // Adicionar event listeners para cada botão
            resultButtons.forEach(button => {
                console.log('Adicionando event listener ao botão de resultados');

                button.addEventListener('click', function(event) {
                    event.preventDefault();

                    // Extrair os parâmetros do botão
                    const origin = this.getAttribute('data-origin');
                    const destination = this.getAttribute('data-destination');
                    const departureDate = this.getAttribute('data-departure');
                    const returnDate = this.getAttribute('data-return');
                    const adults = this.getAttribute('data-adults') || '1';

                    console.log(`Clique no botão de resultados! Parâmetros: ${origin} → ${destination}`);

                    // Chamar a função de redirecionamento
                    openTripResultsPage(origin, destination, departureDate, returnDate, adults);
                });
            });
        }
    }

    // Verificar periodicamente se novos botões foram adicionados
    setInterval(checkForResultButtons, 2000);

    // Também verificar quando o DOM é modificado
    const observer = new MutationObserver(function(mutations) {
        checkForResultButtons();
    });

    // Iniciar observação de mudanças no DOM
    observer.observe(document.body, { 
        childList: true, 
        subtree: true 
    });
});
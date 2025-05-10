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

    // Não interferir com os listeners de eventos existentes do chat
});
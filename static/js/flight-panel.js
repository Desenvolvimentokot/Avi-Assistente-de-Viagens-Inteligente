/**
 * PAINEL DE RESULTADOS REMOVIDO
 * Agora todos os resultados são mostrados na página dedicada travelpayouts-results
 * 
 * Este arquivo foi mantido apenas para evitar erros de referência, mas todo o 
 * comportamento do painel lateral foi removido conforme solicitado.
 */
class FlightPanel {
    constructor() {
        console.log("Painel de voos desativado - agora a aplicação usa redirecionamento para página de resultados");
        window.flightPanel = this;
    }
    
    // Métodos vazios para compatibilidade
    init() { return; }
    createPanel() { return; }
    createToggleButton() { return; }
    setupEventListeners() { return; }
    show() { return; }
    hide() { return; }
    toggle() { return; }
    showLoading() { return; }
    hideLoading() { return; }
    loadFlightData() { return; }
    displayResults() { return; }
    addPanelStyles() { return; }
}

// Inicializar o novo "não-painel" para compatibilidade
document.addEventListener('DOMContentLoaded', function() {
    new FlightPanel();
});
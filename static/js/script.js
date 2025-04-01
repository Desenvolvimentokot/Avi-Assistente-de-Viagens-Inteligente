document.addEventListener('DOMContentLoaded', function() {
    const chatTab = document.getElementById('chat-tab');
    const plansTab = document.getElementById('plans-tab');
    const profileTab = document.getElementById('profile-tab');

    const chatSection = document.getElementById('chat-section');
    const plansSection = document.getElementById('plans-section');
    const profileSection = document.getElementById('profile-section');

    // Toggle para o menu lateral
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('minimized');

            // Salvar estado no localStorage
            if (sidebar.classList.contains('minimized')) {
                localStorage.setItem('sidebar-minimized', 'true');
            } else {
                localStorage.setItem('sidebar-minimized', 'false');
            }
        });

        // Verificar estado salvo no localStorage
        if (localStorage.getItem('sidebar-minimized') === 'true') {
            sidebar.classList.add('minimized');
        }
    }

    // Função para alternar entre as abas
    function switchTab(tab, section) {
        // Remover classe 'active' de todas as abas
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });

        // Remover classe 'active' de todas as seções
        document.querySelectorAll('.content-section').forEach(item => {
            item.classList.remove('active');
        });

        // Adicionar classe 'active' à aba e seção selecionadas
        tab.classList.add('active');
        section.classList.add('active');
    }
});
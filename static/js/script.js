document.addEventListener('DOMContentLoaded', function() {
    // Controle da barra lateral (sidebar)
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    
    if (sidebarToggle) {
        // Verificar se há estado salvo no localStorage
        if (localStorage.getItem('sidebar-minimized') === 'true') {
            sidebar.classList.add('minimized');
            if (mainContent) {
                mainContent.style.marginLeft = '60px';
                mainContent.style.width = 'calc(100% - 60px)';
            }
        }
        
        // Adicionar evento de clique ao botão de toggle
        sidebarToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            sidebar.classList.toggle('minimized');
            
            // Ajustar o conteúdo principal
            if (mainContent) {
                if (sidebar.classList.contains('minimized')) {
                    mainContent.style.marginLeft = '60px';
                    mainContent.style.width = 'calc(100% - 60px)';
                    localStorage.setItem('sidebar-minimized', 'true');
                } else {
                    mainContent.style.marginLeft = '220px';
                    mainContent.style.width = 'calc(100% - 220px)';
                    localStorage.setItem('sidebar-minimized', 'false');
                }
            }
        });
    }
    
    // Seletores de abas
    const chatTab = document.getElementById('chat-tab');
    const plansTab = document.getElementById('plans-tab');
    const profileTab = document.getElementById('profile-tab');
    
    const chatSection = document.getElementById('chat-section');
    const plansSection = document.getElementById('plans-section');
    const profileSection = document.getElementById('profile-section');
    
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
    
    // Adicionar eventos de clique às abas
    if (chatTab && chatSection) {
        chatTab.addEventListener('click', function() {
            switchTab(chatTab, chatSection);
        });
    }
    
    if (plansTab && plansSection) {
        plansTab.addEventListener('click', function() {
            switchTab(plansTab, plansSection);
        });
    }
    
    if (profileTab && profileSection) {
        profileTab.addEventListener('click', function() {
            switchTab(profileTab, profileSection);
        });
    }
});
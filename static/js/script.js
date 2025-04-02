document.addEventListener('DOMContentLoaded', function() {
    // Logo dropdown toggle
    const logoButton = document.getElementById('logo-button');
    const dropdownMenu = document.getElementById('dropdown-menu');
    const headerContainer = document.querySelector('.header-container');

    if (logoButton && dropdownMenu) {
        logoButton.addEventListener('click', function(event) {
            event.stopPropagation();
            dropdownMenu.classList.toggle('show');
            
            // Animação suave do menu
            if (dropdownMenu.classList.contains('show')) {
                // Adiciona classe para ajustar o layout
                headerContainer.classList.add('menu-open');
            } else {
                // Remove classe após animação
                setTimeout(() => {
                    headerContainer.classList.remove('menu-open');
                }, 300); // Tempo da transição
            }
        });

        // Fechar dropdown ao clicar fora dele
        document.addEventListener('click', function(event) {
            if (!dropdownMenu.contains(event.target) && !logoButton.contains(event.target)) {
                dropdownMenu.classList.remove('show');
                
                // Remove classe após animação
                setTimeout(() => {
                    headerContainer.classList.remove('menu-open');
                }, 300); // Tempo da transição
            }
        });
    }

    // Função para alternar entre as abas
    function switchTab(tabId) {
        // Esconder todas as seções de conteúdo
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Exibir a seção selecionada
        document.getElementById(tabId).classList.add('active');

        // Atualizar classe ativa dos itens de navegação no dropdown
        document.querySelectorAll('.nav-item-dropdown').forEach(item => {
            item.classList.remove('active');
        });

        // Adicionar classe ativa ao item clicado no dropdown
        const activeTab = document.querySelector(`[id="${tabId.replace('-section', '-tab-dropdown')}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }
    }

    // Configurar event listeners para as abas no dropdown
    document.getElementById('chat-tab-dropdown').addEventListener('click', function() {
        switchTab('chat-section');
        dropdownMenu.classList.remove('show');
        headerContainer.classList.remove('menu-open');
    });

    document.getElementById('plans-tab-dropdown').addEventListener('click', function() {
        switchTab('plans-section');
        dropdownMenu.classList.remove('show');
        headerContainer.classList.remove('menu-open');
    });

    document.getElementById('profile-tab-dropdown').addEventListener('click', function() {
        switchTab('profile-section');
        dropdownMenu.classList.remove('show');
        headerContainer.classList.remove('menu-open');
    });

    // Event listener para o botão de nova conversa no dropdown
    const addConversationDropdown = document.querySelector('.add-conversation-dropdown');
    if (addConversationDropdown) {
        addConversationDropdown.addEventListener('click', function() {
            console.log('Nova conversa iniciada');
            dropdownMenu.classList.remove('show');
            headerContainer.classList.remove('menu-open');
        });
    }

    // Event listener para botões de modo de conversa
    document.querySelectorAll('.mode-button').forEach(button => {
        button.addEventListener('click', function() {
            document.querySelectorAll('.mode-button').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
});
document.addEventListener('DOMContentLoaded', function() {
    // Logo dropdown toggle
    const logoButton = document.getElementById('logo-button');
    const dropdownMenu = document.getElementById('dropdown-menu');

    if (logoButton && dropdownMenu) {
        logoButton.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        // Fechar o dropdown quando clicar fora dele
        document.addEventListener('click', function(e) {
            if (!dropdownMenu.contains(e.target) && e.target !== logoButton) {
                dropdownMenu.classList.remove('show');
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
    });

    document.getElementById('plans-tab-dropdown').addEventListener('click', function() {
        switchTab('plans-section');
        dropdownMenu.classList.remove('show');
    });

    document.getElementById('profile-tab-dropdown').addEventListener('click', function() {
        switchTab('profile-section');
        dropdownMenu.classList.remove('show');
    });

    // Event listener para o botão de nova conversa no dropdown
    const addConversationDropdown = document.querySelector('.add-conversation-dropdown');
    if (addConversationDropdown) {
        addConversationDropdown.addEventListener('click', function() {
            console.log('Nova conversa iniciada');
            dropdownMenu.classList.remove('show');
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
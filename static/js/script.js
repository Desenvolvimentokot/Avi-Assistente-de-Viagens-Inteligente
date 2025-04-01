document.addEventListener('DOMContentLoaded', function() {
    // Função para alternar entre as abas
    function switchTab(tabId) {
        // Esconder todas as seções de conteúdo
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Exibir a seção selecionada
        document.getElementById(tabId).classList.add('active');

        // Atualizar classe ativa dos itens de navegação
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });

        // Adicionar classe ativa ao item clicado
        document.querySelector(`[id="${tabId.replace('-section', '-tab')}"]`).classList.add('active');
    }

    // Configurar event listeners para as abas
    document.getElementById('chat-tab').addEventListener('click', function() {
        switchTab('chat-section');
    });

    document.getElementById('plans-tab').addEventListener('click', function() {
        switchTab('plans-section');
    });

    document.getElementById('profile-tab').addEventListener('click', function() {
        switchTab('profile-section');
    });

    // Event listener para o botão de nova conversa
    document.querySelector('.add-conversation').addEventListener('click', function() {
        // Implementar lógica para nova conversa
        console.log('Nova conversa iniciada');
    });

    // Event listener para botões de modo de conversa
    document.querySelectorAll('.mode-button').forEach(button => {
        button.addEventListener('click', function() {
            document.querySelectorAll('.mode-button').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
        });
    });

    // Toggle de minimizar a sidebar
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('minimized');

            // Ajusta a rotação do ícone de toggle
            const icon = this.querySelector('i');
            if (sidebar.classList.contains('minimized')) {
                icon.style.transform = 'rotate(180deg)';
                if (mainContent) {
                    mainContent.style.marginLeft = '60px';
                    mainContent.style.width = 'calc(100% - 60px)';
                }
            } else {
                icon.style.transform = 'rotate(0deg)';
                if (mainContent) {
                    mainContent.style.marginLeft = '220px';
                    mainContent.style.width = 'calc(100% - 220px)';
                }
            }
        });
    }

    // Ativar a expansão no hover
    if (sidebar) {
        sidebar.addEventListener('mouseenter', function() {
            if (this.classList.contains('minimized')) {
                // Apenas efeitos visuais no hover, sem remover a classe minimized
                this.style.width = '220px';
            }
        });

        sidebar.addEventListener('mouseleave', function() {
            if (this.classList.contains('minimized')) {
                this.style.width = '60px';
            }
        });
    }
});
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
    const logoContainer = document.querySelector('.logo-container');
    const navItems = document.querySelectorAll('.nav-item span');

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
                
                // Esconder textos imediatamente para evitar deslocamento
                navItems.forEach(span => {
                    span.style.display = 'none';
                });
                
                // Garantir que a logo fique visível e bem posicionada
                if (logoContainer) {
                    logoContainer.style.zIndex = '30'; 
                }
            } else {
                icon.style.transform = 'rotate(0deg)';
                if (mainContent) {
                    mainContent.style.marginLeft = '220px';
                    mainContent.style.width = 'calc(100% - 220px)';
                }
                
                // Mostrar textos novamente
                navItems.forEach(span => {
                    span.style.display = 'inline';
                });
                
                // Restaurar posição normal da logo
                if (logoContainer) {
                    logoContainer.style.zIndex = '30';
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
                
                // Mostrar textos dos itens de navegação ao passar o mouse
                navItems.forEach(span => {
                    span.style.display = 'inline';
                    // Atraso pequeno para suavizar a transição
                    setTimeout(() => {
                        span.style.opacity = '1';
                    }, 100);
                });
            }
        });

        sidebar.addEventListener('mouseleave', function() {
            if (this.classList.contains('minimized')) {
                this.style.width = '60px';
                
                // Esconder textos dos itens de navegação ao sair
                navItems.forEach(span => {
                    span.style.opacity = '0';
                    // Atraso para que o texto desapareça após a animação de largura
                    setTimeout(() => {
                        span.style.display = 'none';
                    }, 200);
                });
            }
        });
    }
});
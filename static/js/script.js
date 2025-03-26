document.addEventListener('DOMContentLoaded', function() {
    // Elementos DOM
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const content = document.getElementById('content');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const loginButton = document.getElementById('login-button');
    const signupButton = document.getElementById('signup-button');
    const loginModal = document.getElementById('login-modal');
    const signupModal = document.getElementById('signup-modal');
    const closeButtons = document.querySelectorAll('.close-modal');
    const newConversationButton = document.getElementById('new-conversation');
    const profileForm = document.getElementById('profile-form');
    const sidebarNavItems = document.querySelectorAll('.sidebar-nav-item');
    const quickSearchModeBtn = document.getElementById('quick-search-mode');
    const fullPlanningModeBtn = document.getElementById('full-planning-mode');

    // State variables
    let isSidebarCollapsed = false;
    let currentConversationId = null;
    let activeSection = 'chat';
    let userLoggedIn = false;
    let userProfile = {};
    let conversations = [];
    let plans = [];
    let chatMode = 'quick-search'; // Modo padrão: 'quick-search' ou 'full-planning'
    let chatContext = {
        mode: 'quick-search',
        quickSearchStep: 0,
        quickSearchData: {},
        fullPlanningStep: 0,
        fullPlanningData: {}
    };
    let useLocalProcessing = true;  // Define se usamos processamento local (demo) ou a API

    // Toggle sidebar
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            isSidebarCollapsed = !isSidebarCollapsed;

            // Atualizar ícone do botão
            if (isSidebarCollapsed) {
                sidebarToggle.innerHTML = '<i class="fas fa-chevron-right"></i>';
            } else {
                sidebarToggle.innerHTML = '<i class="fas fa-chevron-left"></i>';
            }

            // Expandir/encolher conteúdo principal
            content.classList.toggle('expanded');
        });
    }

    // Navegação entre seções
    sidebarNavItems.forEach(item => {
        item.addEventListener('click', function() {
            const section = this.getAttribute('data-section');
            showSection(section);
        });
    });

    // Funcionalidade de chat
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });
    }

    // Habilitar envio de mensagem com a tecla Enter
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Botões de modo de chat
    if (quickSearchModeBtn) {
        quickSearchModeBtn.addEventListener('click', function() {
            setChatMode('quick-search');
        });
    }

    if (fullPlanningModeBtn) {
        fullPlanningModeBtn.addEventListener('click', function() {
            setChatMode('full-planning');
        });
    }

    // Botão de nova conversa
    if (newConversationButton) {
        newConversationButton.addEventListener('click', function() {
            startNewConversation();
        });
    }

    // Modais de login e cadastro
    if (loginButton) {
        loginButton.addEventListener('click', function() {
            showModal(loginModal);
        });
    }

    if (signupButton) {
        signupButton.addEventListener('click', function() {
            showModal(signupModal);
        });
    }

    // Fechar modais
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            hideModal(modal);
        });
    });

    // Formulário de perfil
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveProfile();
        });
    }

    // Funções de exibição
    function showSection(section) {
        // Atualizar seção ativa na navegação
        sidebarNavItems.forEach(item => {
            if (item.getAttribute('data-section') === section) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Esconder todas as seções de conteúdo
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Mostrar seção específica
        const targetSection = document.getElementById(`${section}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // Mostrar/esconder seções específicas na sidebar
        document.querySelectorAll('.sidebar-section').forEach(section => {
            section.classList.remove('active');
        });

        if (section === 'chat' || section === 'plans') {
            const targetSidebarSection = document.getElementById(`${section}s-section`);
            if (targetSidebarSection) {
                targetSidebarSection.classList.add('active');
            }
        }

        activeSection = section;
    }

    function showModal(modal) {
        if (modal) {
            modal.classList.add('active');
        }
    }

    function hideModal(modal) {
        if (modal) {
            modal.classList.remove('active');
        }
    }

    function setChatMode(mode) {
        // Atualizar botões
        if (mode === 'quick-search') {
            quickSearchModeBtn.classList.add('active');
            fullPlanningModeBtn.classList.remove('active');
        } else {
            quickSearchModeBtn.classList.remove('active');
            fullPlanningModeBtn.classList.add('active');
        }

        // Atualizar estado
        chatMode = mode;
        chatContext.mode = mode;

        // Atualizar a mensagem de boas-vindas
        const welcomeMessage = document.getElementById('welcome-message');
        if (welcomeMessage) {
            const welcomeContent = welcomeMessage.querySelector('.message-content');
            if (welcomeContent) {
                welcomeContent.innerHTML = `
                    <p>Você está no modo: <strong>${mode === 'quick-search' ? 'Busca Rápida' : 'Planejamento Completo'}</strong></p>
                    <p>${mode === 'quick-search' 
                        ? 'Neste modo, podemos encontrar rapidamente os melhores voos para a sua viagem.' 
                        : 'Neste modo, vamos criar um plano completo de viagem, incluindo voos, hotéis e atividades.'}
                    </p>
                    <p>Como posso ajudar?</p>
                `;
            }
        }
    }

    // Funções de chat
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Adicionar mensagem do usuário ao chat
        addMessageToChat(message, true);
        messageInput.value = '';

        // Ajustar altura do textarea
        messageInput.style.height = 'auto';

        // Processar mensagem e obter resposta
        processMessage(message);
    }

    function processMessage(message) {
        // Mostrar indicador de "digitando..."
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message assistant typing';
        typingIndicator.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p><i class="fas fa-spinner fa-spin"></i> Digitando...</p>
            </div>
        `;
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        if (useLocalProcessing) {
            // Simulação de resposta local para demonstração
            setTimeout(() => {
                // Remover indicador de digitação
                chatMessages.removeChild(typingIndicator);

                // Processar resposta com base no modo de chat
                let response;
                if (chatMode === 'quick-search') {
                    response = processQuickSearchResponse(message);
                } else {
                    response = processFullPlanningResponse(message);
                }

                // Adicionar resposta ao chat
                addMessageToChat(response, false);

                // Salvar conversa (local)
                saveConversationLocal(message, response);
            }, 1500);
        } else {
            // Chamada à API real
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message,
                    conversation_id: currentConversationId,
                    context: chatContext
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remover indicador de digitação
                chatMessages.removeChild(typingIndicator);

                // Adicionar resposta ao chat
                addMessageToChat(data.response, false);

                // Atualizar ID da conversa e contexto
                if (data.conversation_id) {
                    currentConversationId = data.conversation_id;
                }
                if (data.context) {
                    chatContext = data.context;
                }

                // Processar ações específicas (ex: busca de voos)
                if (data.action) {
                    processAction(data.action);
                }

                // Atualizar lista de conversas
                loadConversations();
            })
            .catch(error => {
                console.log("Error getting chat response:", error);
                chatMessages.removeChild(typingIndicator);
                addMessageToChat("Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.", false);
            });
        }
    }

    function processQuickSearchResponse(message) {
        // Processar resposta real da API e adicionar botões interativos para compra
        let processedResponse = message;

        // Verificar se a mensagem contém informações de voo
        if (message.includes("voo") || message.includes("passagem") || message.includes("Companhia")) {
            // Adicionar botões de compra ao final da mensagem
            processedResponse += `\n\n<div class="action-buttons">
                <button class="btn btn-primary flight-purchase-btn" onclick="handleFlightPurchase('voo123')">
                    <i class="fas fa-shopping-cart"></i> Comprar esta passagem
                </button>
                <button class="btn btn-outline flight-compare-btn">
                    <i class="fas fa-balance-scale"></i> Comparar preços
                </button>
            </div>`;
        }

        return processedResponse;
    }

    function processFullPlanningResponse(message) {
        // Simula o processamento no modo de planejamento completo
        chatContext.fullPlanningStep = chatContext.fullPlanningStep || 0;
        let response = '';

        switch (chatContext.fullPlanningStep) {
            case 0:
                response = "Qual é o destino principal da sua viagem e há outros lugares que deseja visitar?";
                chatContext.fullPlanningStep = 1;
                break;
            case 1:
                // Simular processamento do destino
                chatContext.fullPlanningData.destinations = message;
                response = "Qual a data de início e qual a duração aproximada da sua viagem?";
                chatContext.fullPlanningStep = 2;
                break;
            case 2:
                // Simular processamento da data e duração
                chatContext.fullPlanningData.dateAndDuration = message;
                response = "Quantas pessoas estarão viajando e há alguma preferência específica (classe de voo, tipo de hospedagem)?";
                chatContext.fullPlanningStep = 3;
                break;
            case 3:
                // Simular processamento do número de pessoas e preferências
                chatContext.fullPlanningData.peopleAndPreferences = message;
                response = "Você possui um orçamento definido ou deseja encontrar as melhores ofertas disponíveis?";
                chatContext.fullPlanningStep = 4;
                break;
            case 4:
                // Simular processamento do orçamento
                chatContext.fullPlanningData.budget = message;
                response = "Você deseja incluir passeios ou experiências especiais? Se sim, quais atividades lhe interessam?";
                chatContext.fullPlanningStep = 5;
                break;
            case 5:
                // Simular processamento das atividades e gerar plano
                chatContext.fullPlanningData.activities = message;

                // Gerar plano completo
                response = `
                    <h3>Seu Plano de Viagem Personalizado</h3>
                    <p>Baseado nas suas preferências, elaborei um plano completo para ${chatContext.fullPlanningData.destinations}:</p>

                    <div class="travel-plan">
                        <div class="travel-plan-section">
                            <h4>Informações Gerais</h4>
                            <ul>
                                <li><strong>Destino:</strong> ${chatContext.fullPlanningData.destinations}</li>
                                <li><strong>Data/Duração:</strong> ${chatContext.fullPlanningData.dateAndDuration}</li>
                                <li><strong>Viajantes:</strong> ${chatContext.fullPlanningData.peopleAndPreferences}</li>
                                <li><strong>Orçamento:</strong> ${chatContext.fullPlanningData.budget}</li>
                            </ul>
                        </div>

                        <div class="travel-plan-section">
                            <h4>Voos Recomendados</h4>
                            <div class="plan-card">
                                <div class="plan-card-header">
                                    <span class="airline">LATAM</span>
                                    <span class="price">R$ 1.250,00</span>
                                </div>
                                <div class="plan-card-content">
                                    <p><strong>Ida:</strong> São Paulo → Rio de Janeiro, 09:00 - 10:30</p>
                                    <p><strong>Volta:</strong> Rio de Janeiro → São Paulo, 18:00 - 19:30</p>
                                </div>
                                <button class="btn-book">Reservar</button>
                            </div>
                        </div>

                        <div class="travel-plan-section">
                            <h4>Hospedagem Recomendada</h4>
                            <div class="plan-card">
                                <div class="plan-card-header">
                                    <span class="hotel-name">Hotel Copacabana Palace</span>
                                    <span class="price">R$ 850,00/noite</span>
                                </div>
                                <div class="plan-card-content">
                                    <p><strong>Localização:</strong> Av. Atlântica, Copacabana</p>
                                    <p><strong>Classificação:</strong> 5 estrelas</p>
                                    <p><strong>Comodidades:</strong> Café da manhã, Wi-Fi, Piscina</p>
                                </div>
                                <button class="btn-book">Reservar</button>
                            </div>
                        </div>

                        <div class="travel-plan-section">
                            <h4>Atividades Recomendadas</h4>
                            <ul>
                                <li>Visita ao Cristo Redentor (½ dia)</li>
                                <li>Tour pelo Pão de Açúcar (½ dia)</li>
                                <li>Passeio pelas praias de Copacabana e Ipanema (1 dia)</li>
                                <li>Visita ao Jardim Botânico (½ dia)</li>
                            </ul>
                        </div>
                    </div>

                    <p>Deseja salvar este plano ou fazer alguma modificação?</p>
                    <div class="plan-actions">
                        <button class="btn-save-plan">Salvar Plano</button>
                        <button class="btn-download-pdf">Baixar PDF</button>
                    </div>
                `;

                // Adicionar listeners aos botões do plano (em uma aplicação real, isso seria feito de forma mais elegante)
                setTimeout(() => {
                    const savePlanBtn = document.querySelector('.btn-save-plan');
                    const downloadPdfBtn = document.querySelector('.btn-download-pdf');

                    if (savePlanBtn) {
                        savePlanBtn.addEventListener('click', function() {
                            addMessageToChat("Plano salvo com sucesso! Você pode acessá-lo na seção 'Planos'.", false);
                        });
                    }

                    if (downloadPdfBtn) {
                        downloadPdfBtn.addEventListener('click', function() {
                            addMessageToChat("O PDF do seu plano foi gerado e está pronto para download.", false);
                        });
                    }
                }, 100);

                chatContext.fullPlanningStep = 6;
                break;
            default:
                response = "Como posso ajudar com seu planejamento de viagem? Deseja começar um novo plano?";
                chatContext.fullPlanningStep = 0;
                break;
        }

        return response;
    }

    function addMessageToChat(message, isUser) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(isUser ? 'user' : 'assistant');

        const avatar = document.createElement('div');
        avatar.classList.add('message-avatar');
        avatar.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.classList.add('message-content');

        // Verificar se a mensagem contém HTML
        if (message.includes('<div') || message.includes('<button')) {
            content.innerHTML = message;
        } else {
            // Formatar texto simples, preservando quebras de linha
            content.innerHTML = message.replace(/\n/g, '<br>');
        }

        messageElement.appendChild(avatar);
        messageElement.appendChild(content);

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Inicializar botões interativos, se existirem
        const purchaseButtons = messageElement.querySelectorAll('.flight-purchase-btn');
        purchaseButtons.forEach(button => {
            button.addEventListener('click', function() {
                const flightId = this.getAttribute('data-flight-id') || 'voo123';
                const feedbackMsg = handleFlightPurchase(flightId);
                const feedbackElement = document.createElement('div');
                feedbackElement.classList.add('purchase-feedback');
                feedbackElement.textContent = feedbackMsg;
                this.parentNode.appendChild(feedbackElement);
            });
        });
    }

    function saveConversationLocal(userMessage, assistantResponse) {
        const now = new Date();
        const conversationTitle = userMessage.substring(0, 30) + (userMessage.length > 30 ? '...' : '');

        if (!currentConversationId) {
            // Nova conversa
            currentConversationId = Date.now().toString();
            const newConversation = {
                id: currentConversationId,
                title: conversationTitle,
                created_at: now.toISOString(),
                last_updated: now.toISOString(),
                messages: [
                    {
                        id: Date.now().toString() + '1',
                        content: userMessage,
                        is_user: true,
                        timestamp: now.toISOString()
                    },
                    {
                        id: Date.now().toString() + '2',
                        content: assistantResponse,
                        is_user: false,
                        timestamp: new Date(now.getTime() + 1000).toISOString()
                    }
                ]
            };

            conversations.unshift(newConversation);

            // Atualizar a lista de conversas na interface
            updateConversationsList();
        } else {
            // Conversa existente
            const conversation = conversations.find(c => c.id === currentConversationId);
            if (conversation) {
                conversation.last_updated = now.toISOString();
                conversation.messages.push(
                    {
                        id: Date.now().toString() + '1',
                        content: userMessage,
                        is_user: true,
                        timestamp: now.toISOString()
                    },
                    {
                        id: Date.now().toString() + '2',
                        content: assistantResponse,
                        is_user: false,
                        timestamp: new Date(now.getTime() + 1000).toISOString()
                    }
                );

                // Reordenar conversas (a mais recente primeiro)
                conversations.sort((a, b) => new Date(b.last_updated) - new Date(a.last_updated));

                // Atualizar a lista de conversas na interface
                updateConversationsList();
            }
        }
    }

    function startNewConversation() {
        // Limpar o chat
        chatMessages.innerHTML = `
            <div class="message assistant" id="welcome-message">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <p>Olá! Eu sou Flai, seu assistente de viagens virtual. Como posso ajudar você hoje?</p>
                    <p>Escolha uma das modalidades acima:</p>
                    <ul>
                        <li><strong>Busca Rápida</strong>: Para encontrar os melhores voos rapidamente.</li>
                        <li><strong>Planejamento Completo</strong>: Para criar um itinerário detalhado com voos, hotéis e atrações.</li>
                    </ul>
                </div>
            </div>
        `;

        // Resetar o ID da conversa atual
        currentConversationId = null;

        // Resetar o contexto do chat
        chatContext = {
            mode: chatMode,
            quickSearchStep: 0,
            quickSearchData: {},
            fullPlanningStep: 0,
            fullPlanningData: {}
        };

        // Focar no campo de mensagem
        messageInput.focus();
    }

    function updateConversationsList() {
        const conversationsList = document.getElementById('conversations-list');
        if (!conversationsList) return;

        // Limpar lista atual
        conversationsList.innerHTML = '';

        // Template para item de conversa
        const template = document.getElementById('conversation-item-template');

        // Adicionar conversas à lista
        conversations.forEach(conversation => {
            // Clonar o template
            const conversationItem = template.content.cloneNode(true);

            // Configurar o item
            const item = conversationItem.querySelector('.sidebar-item');
            item.setAttribute('data-id', conversation.id);

            const title = conversationItem.querySelector('.sidebar-item-title');
            title.textContent = conversation.title;

            const date = new Date(conversation.last_updated);
            const subtitle = conversationItem.querySelector('.sidebar-item-subtitle');
            subtitle.textContent = date.toLocaleDateString();

            // Adicionar evento de clique
            item.addEventListener('click', function() {
                loadConversation(conversation.id);
            });

            // Adicionar à lista
            conversationsList.appendChild(conversationItem);
        });
    }

    function loadConversation(conversationId) {
        const conversation = conversations.find(c => c.id === conversationId);
        if (!conversation) return;

        // Definir conversa atual
        currentConversationId = conversationId;

        // Limpar chat
        chatMessages.innerHTML = '';

        // Adicionar mensagens
        conversation.messages.forEach(message => {
            addMessageToChat(message.content, message.is_user);
        });

        // Focar no campo de mensagem
        messageInput.focus();
    }

    // Funcionalidades de autenticação
    function login(email, password) {
        // Implementação simulada de login
        fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                userLoggedIn = true;
                userProfile = data.user;
                hideModal(loginModal);
                updateUIAfterLogin();
                loadUserData();
            } else {
                alert(data.error || 'Erro ao fazer login. Verifique suas credenciais.');
            }
        })
        .catch(error => {
            console.log("Usuário não está logado:", error);
            // Em modo de demonstração, simular login bem-sucedido
            if (useLocalProcessing) {
                userLoggedIn = true;
                userProfile = {
                    name: 'Usuário Demo',
                    email: email || 'usuario@exemplo.com'
                };
                hideModal(loginModal);
                updateUIAfterLogin();
            } else {
                alert('Erro ao fazer login. Por favor, tente novamente.');
            }
        });
    }

    function signup(name, email, password, passwordConfirm) {
        // Validar senha
        if (password !== passwordConfirm) {
            alert('As senhas não coincidem.');
            return;
        }

        // Implementação simulada de cadastro
        fetch('/api/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Cadastro realizado com sucesso! Faça login para continuar.');
                hideModal(signupModal);
                showModal(loginModal);
            } else {
                alert(data.error || 'Erro ao criar conta. Tente novamente.');
            }
        })
        .catch(error => {
            console.log("Erro no cadastro:", error);
            // Em modo de demonstração, simular cadastro bem-sucedido
            if (useLocalProcessing) {
                alert('Cadastro realizado com sucesso! Faça login para continuar.');
                hideModal(signupModal);
                showModal(loginModal);
            } else {
                alert('Erro ao criar conta. Por favor, tente novamente.');
            }
        });
    }

    function updateUIAfterLogin() {
        // Atualizar botões de login/cadastro
        const headerActions = document.querySelector('.header-actions');
        if (headerActions) {
            headerActions.innerHTML = `
                <span class="user-greeting">Olá, ${userProfile.name || 'Usuário'}</span>
                <button id="logout-button" class="btn btn-outline"><i class="fas fa-sign-out-alt"></i> Sair</button>
            `;

            // Adicionar evento ao botão de logout
            const logoutButton = document.getElementById('logout-button');
            if (logoutButton) {
                logoutButton.addEventListener('click', logout);
            }
        }
    }

    function logout() {
        fetch('/api/logout')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                userLoggedIn = false;
                userProfile = {};
                location.reload(); // Recarregar página para resetar estado
            }
        })
        .catch(error => {
            console.log("Erro ao fazer logout:", error);
            // Em modo de demonstração, simular logout bem-sucedido
            if (useLocalProcessing) {
                userLoggedIn = false;
                userProfile = {};
                location.reload();
            }
        });
    }

    function loadUserData() {
        // Carregar dados do usuário após login
        Promise.all([
            loadConversations(),
            loadPlans(),
            loadProfile()
        ]).then(() => {
            console.log('Dados do usuário carregados com sucesso.');
        }).catch(error => {
            console.log('Erro ao carregar dados do usuário:', error);
        });
    }

    function loadConversations() {
        return new Promise((resolve, reject) => {
            fetch('/api/conversations')
            .then(response => response.json())
            .then(data => {
                conversations = data;
                updateConversationsList();
                resolve(data);
            })
            .catch(error => {
                console.log("Error loading conversations:", error);
                // Em modo de demonstração, usar dados locais
                if (useLocalProcessing) {
                    // Manter conversas atuais ou inicializar vazias
                    if (!conversations.length) {
                        conversations = [];
                    }
                    resolve(conversations);
                } else {
                    reject(error);
                }
            });
        });
    }

    function loadPlans() {
        return new Promise((resolve, reject) => {
            fetch('/api/plans')
            .then(response => response.json())
            .then(data => {
                plans = data;
                updatePlansList();
                resolve(data);
            })
            .catch(error => {
                console.log("Error loading plans:", error);
                // Em modo de demonstração, usar dados locais
                if (useLocalProcessing) {
                    plans = [];
                    resolve(plans);
                } else {
                    reject(error);
                }
            });
        });
    }

    function loadProfile() {
        return new Promise((resolve, reject) => {
            fetch('/api/profile')
            .then(response => response.json())
            .then(data => {
                userProfile = data;
                updateProfileForm();
                resolve(data);
            })
            .catch(error => {
                console.log("Error loading profile:", error);
                // Em modo de demonstração, manter perfil atual
                if (useLocalProcessing) {
                    resolve(userProfile);
                } else {
                    reject(error);
                }
            });
        });
    }

    function updateProfileForm() {
        if (!profileForm) return;

        // Preencher campos do formulário com dados do perfil
        document.getElementById('profile-name').value = userProfile.name || '';
        document.getElementById('profile-email').value = userProfile.email || '';
        document.getElementById('profile-phone').value = userProfile.phone || '';

        // Preferências
        if (userProfile.preferences) {
            document.getElementById('profile-preferred-destinations').value = userProfile.preferences.preferred_destinations || '';
            document.getElementById('profile-accommodation-type').value = userProfile.preferences.accommodation_type || '';
            document.getElementById('profile-budget').value = userProfile.preferences.budget || '';
        }
    }

    function saveProfile() {
        const name = document.getElementById('profile-name').value;
        const email = document.getElementById('profile-email').value;
        const phone = document.getElementById('profile-phone').value;
        const preferredDestinations = document.getElementById('profile-preferred-destinations').value;
        const accommodationType = document.getElementById('profile-accommodation-type').value;
        const budget = document.getElementById('profile-budget').value;

        const profileData = {
            name,
            email,
            phone,
            preferences: {
                preferred_destinations: preferredDestinations,
                accommodation_type: accommodationType,
                budget
            }
        };

        fetch('/api/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                userProfile = data.profile;
                alert('Perfil atualizado com sucesso!');
            } else {
                alert(data.error || 'Erro ao atualizar perfil. Tente novamente.');
            }
        })
        .catch(error => {
            console.log("Error saving profile:", error);
            // Em modo de demonstração, simular sucesso
            if (useLocalProcessing) {
                userProfile = profileData;
                alert('Perfil atualizado com sucesso! (Modo demo)');
            } else {
                alert('Erro ao atualizar perfil. Por favor, tente novamente.');
            }
        });
    }

    function updatePlansList() {
        const plansList = document.getElementById('plans-list');
        if (!plansList) return;

        // Limpar lista atual
        plansList.innerHTML = '';

        // Template para item de plano
        const template = document.getElementById('plan-item-template');

        // Adicionar planos à lista
        plans.forEach(plan => {
            // Clonar o template
            const planItem = template.content.cloneNode(true);

            // Configurar o item
            const item = planItem.querySelector('.sidebar-item');
            item.setAttribute('data-id', plan.id);

            const title = planItem.querySelector('.sidebar-item-title');
            title.textContent = plan.title;

            const subtitle = planItem.querySelector('.sidebar-item-subtitle');
            subtitle.textContent = plan.destination;

            // Adicionar evento de clique
            item.addEventListener('click', function() {
                loadPlan(plan.id);
            });

            // Adicionar à lista
            plansList.appendChild(planItem);
        });
    }

    function loadPlan(planId) {
        const plan = plans.find(p => p.id === planId);
        if (!plan) return;

        // Mostrar seção de detalhes do plano
        showSection('plans-detail');

        // Preencher detalhes do plano
        const planDetails = document.getElementById('plan-details');
        if (planDetails) {
            planDetails.innerHTML = `
                <h3>${plan.title}</h3>
                <div class="plan-info">
                    <p><strong>Destino:</strong> ${plan.destination}</p>
                    <p><strong>Data Início:</strong> ${plan.start_date || 'Não definida'}</p>
                    <p><strong>Data Fim:</strong> ${plan.end_date || 'Não definida'}</p>
                </div>
                <div class="plan-details-content">
                    ${plan.details || 'Nenhum detalhe disponível.'}
                </div>
                <div class="plan-actions">
                    <button class="btn btn-primary" id="download-plan-pdf">Baixar PDF</button>
                    <button class="btn btn-outline" id="edit-plan">Editar</button>
                    <button class="btn btn-danger" id="delete-plan">Excluir</button>
                </div>
            `;

            // Adicionar eventos aos botões
            document.getElementById('download-plan-pdf').addEventListener('click', function() {
                downloadPlanPDF(planId);
            });

            document.getElementById('edit-plan').addEventListener('click', function() {
                editPlan(planId);
            });

            document.getElementById('delete-plan').addEventListener('click', function() {
                deletePlan(planId);
            });
        }
    }

    function downloadPlanPDF(planId) {
        window.location.href = `/api/plan/${planId}/pdf`;
    }

    function editPlan(planId) {
        alert('Funcionalidade de edição em desenvolvimento.');
    }

    function deletePlan(planId) {
        if (confirm('Tem certeza que deseja excluir este plano?')) {
            fetch(`/api/plan/${planId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remover plano da lista
                    plans = plans.filter(p => p.id !== planId);
                    updatePlansList();

                    // Voltar para a lista de planos
                    showSection('plans');

                    alert('Plano excluído com sucesso!');
                } else {
                    alert(data.error || 'Erro ao excluir plano.');
                }
            })
            .catch(error => {
                console.log("Error deleting plan:", error);
                // Em modo de demonstração, simular sucesso
                if (useLocalProcessing) {
                    plans = plans.filter(p => p.id !== planId);
                    updatePlansList();
                    showSection('plans');
                    alert('Plano excluído com sucesso! (Modo demo)');
                } else {
                    alert('Erro ao excluir plano. Por favor, tente novamente.');
                }
            });
        }
    }

    // Inicialização
    function init() {
        // Checar se usuário está logado
        fetch('/api/profile')
        .then(response => {
            if (response.ok) return response.json();
            throw new Error('Não autenticado');
        })
        .then(data => {
            userLoggedIn = true;
            userProfile = data;
            updateUIAfterLogin();
            loadUserData();
        })
        .catch(error => {
            // Usuário não está logado, manter UI padrão
            console.log("Usuário não está logado:", error);

            // Em modo de demonstração, carregar dados de exemplo
            if (useLocalProcessing) {
                // Simular conversas de exemplo
                conversations = [
                    {
                        id: '1',
                        title: 'Planejando viagem para Paris',
                        created_at: '2023-04-15T10:30:00Z',
                        last_updated: '2023-04-15T11:45:00Z',
                        messages: [
                            {
                                id: '1-1',
                                content: 'Olá, estou planejando uma viagem para Paris. Pode me ajudar?',
                                is_user: true,
                                timestamp: '2023-04-15T10:30:00Z'
                            },
                            {
                                id: '1-2',
                                content: 'Claro! Paris é um destino incrível. Quando você planeja viajar e por quanto tempo?',
                                is_user: false,
                                timestamp: '2023-04-15T10:31:00Z'
                            }
                        ]
                    },
                    {
                        id: '2',
                        title: 'Viagem para a praia',
                        created_at: '2023-04-10T14:20:00Z',
                        last_updated: '2023-04-10T15:30:00Z',
                        messages: [
                            {
                                id: '2-1',
                                content: 'Quero ir para alguma praia no nordeste em julho. Sugestões?',
                                is_user: true,
                                timestamp: '2023-04-10T14:20:00Z'
                            },
                            {
                                id: '2-2',
                                content: 'Julho é uma ótima época para visitar o nordeste! Recomendo Porto de Galinhas, Morro de São Paulo ou Jericoacoara. Você tem alguma preferência?',
                                is_user: false,
                                timestamp: '2023-04-10T14:22:00Z'
                            }
                        ]
                    }
                ];

                // Atualizar UI
                updateConversationsList();
            }
        });

        // Configurar eventos dos formulários modais
        document.getElementById('login-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            login(email, password);
        });

        document.getElementById('signup-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const name = document.getElementById('signup-name').value;
            const email = document.getElementById('signup-email').value;
            const password = document.getElementById('signup-password').value;
            const passwordConfirm = document.getElementById('signup-password-confirm').value;
            signup(name, email, password, passwordConfirm);
        });

        // Inicializar modo de chat
        setChatMode('quick-search');

        // Monitoramento de preços
        loadPriceMonitors();
        // Verificar preços a cada minuto
        setInterval(checkPrices, 60000);
    }

    // Funções para monitoramento de preços
    function loadPriceMonitors() {
        fetch('/api/price-monitor')
        .then(response => response.json())
        .then(data => {
            console.log(`Carregados: ${data.flights.length + data.hotels.length} ofertas e ${data.alerts.length} alertas`);
            // Atualizar UI com os dados (implementação futura)
        })
        .catch(error => {
            // Usuário não logado ou outro erro
            console.log("Carregados: 0 ofertas e 0 alertas");
        });
    }

    function checkPrices() {
        console.log("Verificando preços para 0 ofertas monitoradas");
        // Implementação futura
    }

    // Funções auxiliares
    function formatDateTime(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleString('pt-BR', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function handleFlightPurchase(flightId) {
        // Esta função será chamada quando o usuário clicar em comprar passagem
        console.log(`Iniciando compra do voo ID: ${flightId}`);

        // Mostrar uma mensagem ao usuário
        const message = "Redirecionando para o site da companhia aérea para finalizar sua compra...";

        // Simular redirecionamento (em produção, isto levaria para um link de afiliado real)
        setTimeout(() => {
            alert("Em um ambiente de produção, você seria redirecionado para o site parceiro para finalizar a compra.");
            // Aqui você pode adicionar o código para redirecionar para um link de afiliado real
            // window.open('https://parceiro.com.br/compra?flight=' + flightId, '_blank');
        }, 1000);

        return message;
    }


    // Iniciar aplicação
    init();
});
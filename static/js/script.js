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

    // State variables
    let isSidebarCollapsed = false;
    let currentConversationId = null;
    let activeSection = 'chat';
    let userLoggedIn = false;
    let userProfile = {};
    let conversations = [];
    let plans = [];

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

    // Adicionar evento para tecla Enter no campo de mensagem
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            // Verificar se a tecla pressionada é Enter e não tem Shift pressionado (para permitir quebras de linha com Shift+Enter)
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault(); // Impedir o comportamento padrão (quebra de linha)
                sendMessage(); // Enviar a mensagem
            }
        });
    }

    // Função para enviar mensagem
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Adicionar mensagem do usuário ao chat
        addMessageToChat(message, true);

        // Limpar campo de input
        messageInput.value = '';

        // Enviar mensagem para a API e receber resposta
        getChatResponse(message);
    }

    // Função para adicionar mensagem ao chat
    function addMessageToChat(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user' : 'message assistant';

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';

        // Adicionar ícone baseado em quem está falando
        avatarDiv.innerHTML = isUser 
            ? '<i class="fas fa-user"></i>' 
            : '<i class="fas fa-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `<p>${message}</p>`;

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        chatMessages.appendChild(messageDiv);

        // Scroll para a última mensagem
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Função para obter resposta do chat
    function getChatResponse(userMessage) {
        const data = {
            message: userMessage,
        };

        // Adicionar ID da conversa, se existir
        if (currentConversationId) {
            data.conversation_id = currentConversationId;
        }

        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.response) {
                // Adicionar resposta do assistente ao chat
                addMessageToChat(data.response, false);

                // Atualizar ID da conversa se for uma nova conversa
                if (data.conversation_id && !currentConversationId) {
                    currentConversationId = data.conversation_id;

                    // Recarregar lista de conversas
                    loadConversations();
                }
            } else if (data.error) {
                addMessageToChat('Erro: ' + data.error, false);
            }
        })
        .catch(error => {
            console.error('Error getting chat response:', error);
            addMessageToChat('Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde.', false);
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

    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            hideModal(this.closest('.modal'));
        });
    });

    // Fechar modal ao clicar fora
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            hideModal(e.target);
        }
    });

    // Funções auxiliares para modais
    function showModal(modal) {
        modal.style.display = 'flex';
    }

    function hideModal(modal) {
        modal.style.display = 'none';
    }

    // Função para mudar entre seções
    function showSection(section) {
        // Atualizar item ativo na navegação
        sidebarNavItems.forEach(item => {
            if (item.getAttribute('data-section') === section) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Seção do sidebar
        const sidebarSections = document.querySelectorAll('.sidebar-section');
        sidebarSections.forEach(section => {
            section.classList.remove('active');
        });

        if (section === 'chat') {
            document.getElementById('conversations-section').classList.add('active');
        } else if (section === 'plans') {
            document.getElementById('plans-section').classList.add('active');
        }

        // Seções de conteúdo
        const contentSections = document.querySelectorAll('.content-section');
        contentSections.forEach(s => {
            s.classList.remove('active');
        });

        if (section === 'chat') {
            document.getElementById('chat-section').classList.add('active');
        } else if (section === 'plans') {
            document.getElementById('plans-detail-section').classList.add('active');
        } else if (section === 'profile') {
            document.getElementById('profile-section').classList.add('active');
        }

        activeSection = section;
    }

    // Carregar conversas
    function loadConversations() {
        fetch('/api/conversations')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Error loading conversations');
        })
        .then(data => {
            conversations = data.conversations || [];
            renderConversationsList();
        })
        .catch(error => {
            console.error('Error loading conversations:', error);
        });
    }

    // Renderizar lista de conversas
    function renderConversationsList() {
        const conversationsList = document.getElementById('conversations-list');
        if (!conversationsList) return;

        // Limpar lista
        conversationsList.innerHTML = '';

        // Adicionar cada conversa à lista
        conversations.forEach(conversation => {
            const template = document.getElementById('conversation-item-template');
            const clone = document.importNode(template.content, true);

            const item = clone.querySelector('.sidebar-item');
            item.setAttribute('data-id', conversation.id);

            const title = clone.querySelector('.sidebar-item-title');
            title.textContent = conversation.title;

            const date = new Date(conversation.created_at);
            const subtitle = clone.querySelector('.sidebar-item-subtitle');
            subtitle.textContent = date.toLocaleDateString();

            // Destacar conversa ativa
            if (currentConversationId === conversation.id) {
                item.classList.add('active');
            }

            // Adicionar evento de clique
            item.addEventListener('click', function() {
                loadConversation(conversation.id);
            });

            conversationsList.appendChild(clone);
        });
    }

    // Carregar conversa específica
    function loadConversation(conversationId) {
        fetch(`/api/conversations/${conversationId}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Error loading conversation');
        })
        .then(data => {
            // Limpar chat atual
            chatMessages.innerHTML = '';

            // Atualizar ID da conversa atual
            currentConversationId = conversationId;

            // Carregar mensagens
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    addMessageToChat(msg.content, msg.is_user);
                });
            }

            // Atualizar lista de conversas para destacar a conversa ativa
            renderConversationsList();

            // Mostrar seção de chat
            showSection('chat');
        })
        .catch(error => {
            console.error('Error loading conversation:', error);
            alert('Erro ao carregar conversa. Por favor, tente novamente.');
        });
    }

    // Nova conversa
    if (newConversationButton) {
        newConversationButton.addEventListener('click', function() {
            // Limpar chat atual
            chatMessages.innerHTML = '';

            // Adicionar mensagem de boas-vindas
            addMessageToChat('Olá! Eu sou Flai, seu assistente de viagens virtual. Como posso ajudar você hoje?', false);

            // Resetar ID da conversa atual
            currentConversationId = null;

            // Mostrar seção de chat
            showSection('chat');
        });
    }

    // Carregar planos de viagem
    function loadPlans() {
        fetch('/api/plans')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Error loading plans');
        })
        .then(data => {
            plans = data;
            renderPlansList();
        })
        .catch(error => {
            console.error('Error loading plans:', error);
        });
    }

    // Renderizar lista de planos
    function renderPlansList() {
        const plansList = document.getElementById('plans-list');
        if (!plansList) return;

        // Limpar lista
        plansList.innerHTML = '';

        // Adicionar cada plano à lista
        plans.forEach(plan => {
            const template = document.getElementById('plan-item-template');
            const clone = document.importNode(template.content, true);

            const item = clone.querySelector('.sidebar-item');
            item.setAttribute('data-id', plan.id);

            const title = clone.querySelector('.sidebar-item-title');
            title.textContent = plan.title;

            const subtitle = clone.querySelector('.sidebar-item-subtitle');
            subtitle.textContent = plan.destination;

            // Adicionar evento de clique
            item.addEventListener('click', function() {
                loadPlan(plan.id);
            });

            plansList.appendChild(clone);
        });
    }

    // Carregar plano específico
    function loadPlan(planId) {
        fetch(`/api/plan/${planId}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Error loading plan');
        })
        .then(data => {
            renderPlanDetails(data);
            showSection('plans');
        })
        .catch(error => {
            console.error('Error loading plan:', error);
            alert('Erro ao carregar plano. Por favor, tente novamente.');
        });
    }

    // Renderizar detalhes do plano
    function renderPlanDetails(plan) {
        const planDetails = document.getElementById('plan-details');

        // Criar HTML para o plano
        const html = `
            <div class="plan-header">
                <h3>${plan.title}</h3>
                <span class="plan-destination">${plan.destination}</span>
                <div class="plan-dates">
                    ${plan.start_date ? `<span>De: ${plan.start_date}</span>` : ''}
                    ${plan.end_date ? `<span>Até: ${plan.end_date}</span>` : ''}
                </div>
            </div>
            <div class="plan-content">
                <div class="plan-description">
                    <h4>Detalhes</h4>
                    <p>${plan.details || 'Sem detalhes disponíveis.'}</p>
                </div>

                <div class="plan-flights">
                    <h4>Voos</h4>
                    ${plan.flights && plan.flights.length > 0 
                        ? `<ul>${plan.flights.map(flight => `
                            <li>
                                <div class="flight-item">
                                    <div class="flight-header">
                                        <span class="flight-airline">${flight.airline} ${flight.flight_number}</span>
                                        <span class="flight-price">${flight.price} ${flight.currency}</span>
                                    </div>
                                    <div class="flight-route">
                                        ${flight.departure_location} → ${flight.arrival_location}
                                    </div>
                                    <div class="flight-times">
                                        <span>Partida: ${new Date(flight.departure_time).toLocaleString()}</span>
                                        <span>Chegada: ${new Date(flight.arrival_time).toLocaleString()}</span>
                                    </div>
                                </div>
                            </li>`).join('')}
                        </ul>`
                        : '<p>Nenhum voo selecionado.</p>'
                    }
                </div>

                <div class="plan-accommodations">
                    <h4>Acomodações</h4>
                    ${plan.accommodations && plan.accommodations.length > 0 
                        ? `<ul>${plan.accommodations.map(acc => `
                            <li>
                                <div class="accommodation-item">
                                    <div class="accommodation-header">
                                        <span class="accommodation-name">${acc.name}</span>
                                        <span class="accommodation-price">${acc.price_per_night} ${acc.currency}/noite</span>
                                    </div>
                                    <div class="accommodation-location">${acc.location}</div>
                                    <div class="accommodation-dates">
                                        <span>Check-in: ${acc.check_in}</span>
                                        <span>Check-out: ${acc.check_out}</span>
                                    </div>
                                    <div class="accommodation-stars">
                                        ${'★'.repeat(acc.stars)}${'☆'.repeat(5 - acc.stars)}
                                    </div>
                                </div>
                            </li>`).join('')}
                        </ul>`
                        : '<p>Nenhuma acomodação selecionada.</p>'
                    }
                </div>
            </div>
        `;

        planDetails.innerHTML = html;
    }

    // Carregar perfil do usuário
    function loadProfile() {
        fetch('/api/profile')
        .then(response => {
            if (response.ok) {
                return response.json();
                userLoggedIn = true;
            }
            throw new Error('User not logged in');
        })
        .then(data => {
            userProfile = data;
            populateProfileForm();
        })
        .catch(error => {
            console.error('Error loading profile:', error);
            userLoggedIn = false;
        });
    }

    // Preencher formulário de perfil
    function populateProfileForm() {
        if (!userProfile) return;

        document.getElementById('profile-name').value = userProfile.name || '';
        document.getElementById('profile-email').value = userProfile.email || '';
        document.getElementById('profile-phone').value = userProfile.phone || '';

        if (userProfile.preferences) {
            document.getElementById('profile-preferred-destinations').value = userProfile.preferences.preferred_destinations || '';
            document.getElementById('profile-accommodation-type').value = userProfile.preferences.accommodation_type || '';
            document.getElementById('profile-budget').value = userProfile.preferences.budget || '';
        }
    }

    // Submissão do formulário de perfil
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!userLoggedIn) {
                alert('Você precisa estar logado para salvar suas preferências.');
                return;
            }

            const formData = new FormData(this);
            const data = {
                name: formData.get('name'),
                email: formData.get('email'),
                phone: formData.get('phone'),
                preferences: {
                    preferred_destinations: formData.get('preferred_destinations'),
                    accommodation_type: formData.get('accommodation_type'),
                    budget: formData.get('budget')
                }
            };

            fetch('/api/profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Error saving profile');
            })
            .then(data => {
                alert('Perfil salvo com sucesso!');
                userProfile = data.profile;
            })
            .catch(error => {
                console.error('Error saving profile:', error);
                alert('Erro ao salvar perfil. Por favor, tente novamente.');
            });
        });
    }

    // Inicialização
    loadConversations();
    loadPlans();
    loadProfile();

    // Monitoramento de preços
    let monitoredOffers = {
        flights: [],
        hotels: [],
        alerts: []
    };

    // Carregar ofertas monitoradas
    function loadMonitoredOffers() {
        try {
            fetch('/api/price-monitor')
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('User not logged in');
            })
            .then(data => {
                monitoredOffers = data;
                console.log(`Carregados: ${monitoredOffers.flights.length + monitoredOffers.hotels.length} ofertas e ${monitoredOffers.alerts.length} alertas`);
            })
            .catch(error => {
                console.log('Usuário não está logado:', error);
            });
        } catch (e) {
            console.error('Erro ao carregar ofertas monitoradas:', e);
        }
    }

    // Verificar preços periodicamente (a cada 10 minutos)
    function schedulePriceCheck() {
        try {
            console.log(`Verificando preços para ${monitoredOffers.flights.length + monitoredOffers.hotels.length} ofertas monitoradas`);

            // Se houver ofertas monitoradas, verificar preços
            if (monitoredOffers.flights.length > 0 || monitoredOffers.hotels.length > 0) {
                fetch('/api/price-monitor/check', {
                    method: 'POST'
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    }
                    throw new Error('Error checking prices');
                })
                .then(data => {
                    // Recarregar ofertas após verificação
                    loadMonitoredOffers();

                    // Notificar usuário se houve alterações significativas de preço
                    if (data.alerts && data.alerts.length > 0) {
                        // Implementar notificação
                    }
                })
                .catch(error => {
                    console.error('Error checking prices:', error);
                });
            }
        } catch (e) {
            console.error('Erro ao verificar preços:', e);
        }
    }

    // Iniciar monitoramento de preços
    loadMonitoredOffers();
    setInterval(schedulePriceCheck, 600000); // 10 minutos
});
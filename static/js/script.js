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

            // Mudar o ícone dependendo do estado
            const icon = sidebarToggle.querySelector('i');
            if (isSidebarCollapsed) {
                icon.classList.remove('fa-chevron-left');
                icon.classList.add('fa-chevron-right');
            } else {
                icon.classList.remove('fa-chevron-right');
                icon.classList.add('fa-chevron-left');
            }
        });
    }

    // Navegação da barra lateral
    sidebarNavItems.forEach(item => {
        item.addEventListener('click', function() {
            const section = this.getAttribute('data-section');

            // Atualizar a classe ativa no item da barra lateral
            sidebarNavItems.forEach(navItem => {
                navItem.classList.remove('active');
            });
            this.classList.add('active');

            // Mostrar a seção correspondente
            showSection(section);

            // Atualizar o conteúdo da barra lateral com base na seção
            updateSidebarContent(section);
        });
    });

    // Função para mostrar a seção correspondente
    function showSection(section) {
        activeSection = section;

        // Esconder todas as seções
        const contentSections = document.querySelectorAll('.content-section');
        contentSections.forEach(section => {
            section.classList.remove('active');
        });

        // Mostrar a seção correspondente
        const sectionToShow = document.getElementById(`${section}-section`);
        if (sectionToShow) {
            sectionToShow.classList.add('active');
        }
    }

    // Atualizar o conteúdo da barra lateral com base na seção
    function updateSidebarContent(section) {
        const conversationsSection = document.getElementById('conversations-section');
        const plansSection = document.getElementById('plans-section');

        // Esconder todas as seções da barra lateral
        if (conversationsSection) conversationsSection.classList.remove('active');
        if (plansSection) plansSection.classList.remove('active');

        // Mostrar a seção correspondente
        if (section === 'chat' && conversationsSection) {
            conversationsSection.classList.add('active');
            loadConversations(); // Carregar conversas
        } else if (section === 'plans' && plansSection) {
            plansSection.classList.add('active');
            loadPlans(); // Carregar planos
        }
    }

    // Abrir modal
    function openModal(modal) {
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    // Fechar modal
    function closeModal(modal) {
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Event listeners para modais
    if (loginButton) {
        loginButton.addEventListener('click', function() {
            openModal(loginModal);
        });
    }

    if (signupButton) {
        signupButton.addEventListener('click', function() {
            openModal(signupModal);
        });
    }

    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });

    // Clicar fora do modal para fechar
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            closeModal(event.target);
        }
    });

    // Processar formulário de login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;

            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    userLoggedIn = true;
                    userProfile = data.user;
                    closeModal(loginModal);

                    // Atualizar UI para usuário logado
                    updateUIForLoggedInUser();

                    // Carregar dados do usuário
                    loadUserData();
                } else {
                    alert(data.error || 'Erro ao fazer login');
                }
            })
            .catch(error => {
                console.error('Error logging in:', error);
                alert('Erro ao fazer login. Por favor, tente novamente.');
            });
        });
    }

    // Atualizar UI para usuário logado
    function updateUIForLoggedInUser() {
        if (loginButton) loginButton.style.display = 'none';
        if (signupButton) signupButton.style.display = 'none';

        // Mostrar saudação ao usuário
        const headerActions = document.querySelector('.header-actions');
        if (headerActions) {
            const userGreeting = document.createElement('div');
            userGreeting.classList.add('user-greeting');
            userGreeting.innerHTML = `
                <span>Olá, ${userProfile.name || 'Usuário'}</span>
                <button id="logout-button" class="btn btn-outline btn-sm">
                    <i class="fas fa-sign-out-alt"></i> Sair
                </button>
            `;
            headerActions.innerHTML = '';
            headerActions.appendChild(userGreeting);

            // Adicionar event listener para o botão de logout
            const logoutButton = document.getElementById('logout-button');
            if (logoutButton) {
                logoutButton.addEventListener('click', logout);
            }
        }
    }

    // Função de logout
    function logout() {
        fetch('/logout')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                userLoggedIn = false;
                userProfile = {};

                // Resetar UI
                window.location.reload();
            }
        })
        .catch(error => {
            console.error('Error logging out:', error);
        });
    }

    // Carregar dados do usuário (conversas, planos, perfil)
    function loadUserData() {
        loadConversations();
        loadPlans();
        loadProfile();
    }

    // Verificar se o usuário já está logado ao carregar a página
    function checkLoginStatus() {
        fetch('/api/profile')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Usuário não está logado');
        })
        .then(data => {
            userLoggedIn = true;
            userProfile = data;
            updateUIForLoggedInUser();
            loadUserData();
        })
        .catch(error => {
            console.log('Usuário não está logado:', error);
            // Não precisamos mostrar erro, pois é esperado quando não está logado
        });
    }

    // Carregar perfil do usuário
    function loadProfile() {
        fetch('/api/profile')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Erro ao carregar perfil');
        })
        .then(data => {
            userProfile = data;

            // Preencher formulário de perfil
            const nameInput = document.getElementById('profile-name');
            const emailInput = document.getElementById('profile-email');
            const phoneInput = document.getElementById('profile-phone');
            const destinationsInput = document.getElementById('profile-preferred-destinations');
            const accommodationSelect = document.getElementById('profile-accommodation-type');
            const budgetSelect = document.getElementById('profile-budget');

            if (nameInput) nameInput.value = data.name || '';
            if (emailInput) emailInput.value = data.email || '';
            if (phoneInput) phoneInput.value = data.phone || '';

            if (data.preferences) {
                if (destinationsInput) destinationsInput.value = data.preferences.preferred_destinations || '';
                if (accommodationSelect) accommodationSelect.value = data.preferences.accommodation_type || '';
                if (budgetSelect) budgetSelect.value = data.preferences.budget || '';
            }
        })
        .catch(error => {
            console.error('Error loading profile:', error);
        });
    }

    // Processar formulário de perfil
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const name = document.getElementById('profile-name').value;
            const email = document.getElementById('profile-email').value;
            const phone = document.getElementById('profile-phone').value;
            const preferredDestinations = document.getElementById('profile-preferred-destinations').value;
            const accommodationType = document.getElementById('profile-accommodation-type').value;
            const budget = document.getElementById('profile-budget').value;

            const profileData = {
                name: name,
                email: email,
                phone: phone,
                preferences: {
                    preferred_destinations: preferredDestinations,
                    accommodation_type: accommodationType,
                    budget: budget
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
                    alert('Perfil atualizado com sucesso!');
                    userProfile = data.profile;
                } else {
                    alert(data.error || 'Erro ao atualizar perfil');
                }
            })
            .catch(error => {
                console.error('Error updating profile:', error);
                alert('Erro ao atualizar perfil. Por favor, tente novamente.');
            });
        });
    }

    // Formulário de chat
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const message = messageInput.value.trim();
            if (message) {
                addMessageToChat(message, true);
                messageInput.value = '';

                // Ajustar altura do textarea
                messageInput.style.height = 'auto';

                // Enviar mensagem para o servidor
                sendMessage(message);
            }
        });
    }

    // Auto-resize para o textarea de mensagem
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    // Adicionar mensagem ao chat
    function addMessageToChat(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user' : 'assistant');

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${isUser ? 'fa-user' : 'fa-robot'}"></i>
            </div>
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;

        chatMessages.appendChild(messageDiv);

        // Rolar para o final
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Enviar mensagem para o servidor
    function sendMessage(message) {
        const data = {
            message: message
        };

        // Se estiver em uma conversa existente, adicionar o ID
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
        .then(response => response.json())
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
            addMessageToChat('Desculpe, ocorreu um erro ao processar sua mensagem.', false);
        });
    }

    // Carregar conversas do usuário
    function loadConversations() {
        fetch('/api/conversations')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Error loading conversations');
        })
        .then(data => {
            conversations = data;
            renderConversationsList();
        })
        .catch(error => {
            console.log('Error loading conversations:', error);
        });
    }

    // Renderizar lista de conversas
    function renderConversationsList() {
        const conversationsList = document.getElementById('conversations-list');
        if (!conversationsList) return;

        conversationsList.innerHTML = '';

        if (conversations.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.classList.add('empty-list-message');
            emptyMessage.textContent = 'Nenhuma conversa iniciada';
            conversationsList.appendChild(emptyMessage);
            return;
        }

        // Usar o template para criar itens na lista
        const template = document.getElementById('conversation-item-template');

        conversations.forEach(conversation => {
            const item = document.importNode(template.content, true).querySelector('.sidebar-item');

            item.setAttribute('data-id', conversation.id);
            item.querySelector('.sidebar-item-title').textContent = conversation.title;
            item.querySelector('.sidebar-item-subtitle').textContent = conversation.last_updated;

            // Marcar a conversa atual como ativa
            if (conversation.id === currentConversationId) {
                item.classList.add('active');
            }

            item.addEventListener('click', function() {
                // Carregar conversa
                loadConversation(conversation.id);
            });

            conversationsList.appendChild(item);
        });
    }

    // Carregar uma conversa específica
    function loadConversation(conversationId) {
        fetch(`/api/conversation/${conversationId}/messages`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Error loading conversation');
        })
        .then(data => {
            // Limpar chat atual
            chatMessages.innerHTML = '';

            // Adicionar mensagens ao chat
            data.forEach(message => {
                addMessageToChat(message.content, message.is_user);
            });

            // Atualizar ID da conversa atual
            currentConversationId = conversationId;

            // Atualizar UI para mostrar conversa ativa
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

        plansList.innerHTML = '';

        if (plans.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.classList.add('empty-list-message');
            emptyMessage.textContent = 'Nenhum plano de viagem criado';
            plansList.appendChild(emptyMessage);
            return;
        }

        // Usar o template para criar itens na lista
        const template = document.getElementById('plan-item-template');

        plans.forEach(plan => {
            const item = document.importNode(template.content, true).querySelector('.sidebar-item');

            item.setAttribute('data-id', plan.id);
            item.querySelector('.sidebar-item-title').textContent = plan.title;
            item.querySelector('.sidebar-item-subtitle').textContent = plan.destination;

            item.addEventListener('click', function() {
                // Carregar detalhes do plano
                loadPlanDetails(plan.id);
            });

            plansList.appendChild(item);
        });
    }

    // Carregar detalhes de um plano
    function loadPlanDetails(planId) {
        fetch(`/api/plan/${planId}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Error loading plan details');
        })
        .then(plan => {
            const planDetailsContainer = document.getElementById('plan-details');
            if (!planDetailsContainer) return;

            // Formatar datas
            const startDate = plan.start_date || 'Data não definida';
            const endDate = plan.end_date || 'Data não definida';

            planDetailsContainer.innerHTML = `
                <div class="plan-header">
                    <h3>${plan.title}</h3>
                    <div class="plan-destination">
                        <i class="fas fa-map-marker-alt"></i> ${plan.destination}
                    </div>
                    <div class="plan-dates">
                        <i class="fas fa-calendar"></i> ${startDate} - ${endDate}
                    </div>
                </div>
                <div class="plan-content">
                    <h4>Detalhes</h4>
                    <p>${plan.details || 'Nenhum detalhe disponível'}</p>

                    <div class="plan-sections">
                        <div class="plan-section">
                            <h4>Voos</h4>
                            <div class="plan-flights-list">
                                ${renderFlightsList(plan.flights || [])}
                            </div>
                        </div>

                        <div class="plan-section">
                            <h4>Acomodações</h4>
                            <div class="plan-accommodations-list">
                                ${renderAccommodationsList(plan.accommodations || [])}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="plan-actions">
                    <button class="btn btn-primary" onclick="downloadPlanPDF(${plan.id})">
                        <i class="fas fa-download"></i> Baixar PDF
                    </button>
                </div>
            `;

            // Mostrar seção de detalhes do plano
            showSection('plans-detail');
        })
        .catch(error => {
            console.error('Error loading plan details:', error);
            alert('Erro ao carregar detalhes do plano. Por favor, tente novamente.');
        });
    }

    // Renderizar lista de voos
    function renderFlightsList(flights) {
        if (flights.length === 0) {
            return '<p class="empty-list-message">Nenhum voo adicionado</p>';
        }

        let html = '';

        flights.forEach(flight => {
            html += `
                <div class="flight-item">
                    <div class="flight-header">
                        <span class="flight-airline">${flight.airline}</span>
                        <span class="flight-number">${flight.flight_number}</span>
                    </div>
                    <div class="flight-route">
                        <div class="flight-location">
                            <div class="flight-time">${formatTime(flight.departure_time)}</div>
                            <div class="flight-city">${flight.departure_location}</div>
                        </div>
                        <div class="flight-divider">
                            <i class="fas fa-plane"></i>
                        </div>
                        <div class="flight-location">
                            <div class="flight-time">${formatTime(flight.arrival_time)}</div>
                            <div class="flight-city">${flight.arrival_location}</div>
                        </div>
                    </div>
                    <div class="flight-price">
                        <span>${flight.price} ${flight.currency}</span>
                    </div>
                </div>
            `;
        });

        return html;
    }

    // Renderizar lista de acomodações
    function renderAccommodationsList(accommodations) {
        if (accommodations.length === 0) {
            return '<p class="empty-list-message">Nenhuma acomodação adicionada</p>';
        }

        let html = '';

        accommodations.forEach(acc => {
            html += `
                <div class="accommodation-item">
                    <div class="accommodation-header">
                        <span class="accommodation-name">${acc.name}</span>
                        <div class="accommodation-stars">
                            ${renderStars(acc.stars)}
                        </div>
                    </div>
                    <div class="accommodation-location">
                        <i class="fas fa-map-marker-alt"></i> ${acc.location}
                    </div>
                    <div class="accommodation-dates">
                        <span>${acc.check_in || 'Data não definida'} - ${acc.check_out || 'Data não definida'}</span>
                    </div>
                    <div class="accommodation-price">
                        <span>${acc.price_per_night} ${acc.currency} / noite</span>
                    </div>
                </div>
            `;
        });

        return html;
    }

    // Renderizar estrelas para avaliação
    function renderStars(stars) {
        const starsCount = parseInt(stars) || 0;
        let html = '';

        for (let i = 0; i < 5; i++) {
            if (i < starsCount) {
                html += '<i class="fas fa-star"></i>';
            } else {
                html += '<i class="far fa-star"></i>';
            }
        }

        return html;
    }

    // Formatar hora
    function formatTime(timeString) {
        if (!timeString) return 'Horário não definido';

        try {
            const date = new Date(timeString);
            return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return timeString;
        }
    }

    // Função placeholder para baixar PDF
    window.downloadPlanPDF = function(planId) {
        alert('Função de download em PDF será implementada em breve.');
    };

    // Inicialização
    checkLoginStatus();
    showSection('chat');
});
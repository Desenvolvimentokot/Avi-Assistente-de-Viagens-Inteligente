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

    // Adicionar evento para tecla Enter no campo de mensagem
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            // Verificar se a tecla pressionada é Enter e não tem Shift pressionado (para permitir quebras de linha com Shift+Enter)
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault(); // Impedir o comportamento padrão (quebra de linha)
                sendMessage(); // Enviar a mensagem
            }
        });
    }

    // Função para enviar mensagem
    function sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();

        if (message === '') return;

        // Limpar input
        messageInput.value = '';

        // Adicionar mensagem do usuário à interface
        addMessageToChat(message, true);

        // Processar resposta se estivermos usando as modalidades de chat locais
        if (useLocalProcessing && (chatMode === 'quick-search' || chatMode === 'full-planning')) {
            processUserResponse(message);
            return;
        }

        // Desabilitar input durante processamento
        messageInput.disabled = true;
        document.getElementById('send-button').disabled = true;

        // Mostrar indicador de digitação
        showTypingIndicator();

        // Preparar objeto com contexto da conversa
        const chatContext = {
            mode: chatMode
        };

        if (chatMode === 'quick-search') {
            chatContext.quickSearchData = chatState.quickSearch.data;
            chatContext.quickSearchStep = chatState.quickSearch.step;
        } else if (chatMode === 'full-planning') {
            chatContext.fullPlanningData = chatState.fullPlanning.data;
            chatContext.fullPlanningStep = chatState.fullPlanning.step;
        }

        // Enviar para a API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId,
                context: chatContext
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remover indicador de digitação
            removeTypingIndicator();

            // Adicionar resposta do assistente
            addMessageToChat(data.response, false);

            // Se for uma nova conversa, atualizar o ID e adicionar à lista
            if (!currentConversationId && data.conversation_id) {
                currentConversationId = data.conversation_id;
                // Carregar conversas para atualizar a lista
                loadConversations();
            }

            // Atualizar estado com base na resposta da API
            if (data.context) {
                if (data.context.mode === 'quick-search' && data.context.quickSearchData) {
                    chatState.quickSearch.data = data.context.quickSearchData;
                    chatState.quickSearch.step = data.context.quickSearchStep;
                } else if (data.context.mode === 'full-planning' && data.context.fullPlanningData) {
                    chatState.fullPlanning.data = data.context.fullPlanningData;
                    chatState.fullPlanning.step = data.context.fullPlanningStep;
                }
            }

            // Processar ações especiais da resposta
            if (data.action) {
                handleChatAction(data.action);
            }

            // Reativar input
            messageInput.disabled = false;
            document.getElementById('send-button').disabled = false;
            messageInput.focus();
        })
        .catch(error => {
            console.error("Error getting chat response:", error);
            removeTypingIndicator();
            addMessageToChat("Desculpe, ocorreu um erro ao processar sua mensagem.", false);
            messageInput.disabled = false;
            document.getElementById('send-button').disabled = false;
        });
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
    //Esta função foi removida pois agora o processamento da resposta é feito na função sendMessage

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


    // Configurar alternância entre modos de chat
    const quickSearchBtn = document.getElementById('quick-search-mode');
    const fullPlanningBtn = document.getElementById('full-planning-mode');

    if (quickSearchBtn && fullPlanningBtn) {
        // Modo de busca rápida
        quickSearchBtn.addEventListener('click', function() {
            quickSearchBtn.classList.add('active');
            fullPlanningBtn.classList.remove('active');
            chatMode = 'quick-search';

            // Limpar chat e adicionar mensagem de boas-vindas para busca rápida
            clearChat();
            addMessageToChat("Ótimo! Vamos encontrar os melhores voos para você. Por favor, responda estas perguntas:", false);
            addMessageToChat("Quando você deseja viajar? (data de ida)", false);
        });

        // Modo de planejamento completo
        fullPlanningBtn.addEventListener('click', function() {
            fullPlanningBtn.classList.add('active');
            quickSearchBtn.classList.remove('active');
            chatMode = 'full-planning';

            // Limpar chat e adicionar mensagem de boas-vindas para planejamento
            clearChat();
            addMessageToChat("Excelente! Vamos criar um planejamento completo de viagem para você. Por favor, responda estas perguntas para começarmos:", false);
            addMessageToChat("Qual é o destino principal da sua viagem e há outros lugares que deseja visitar?", false);
        });
    }

    // Variáveis globais para o chat
    let currentConversationId = null;
    let chatMode = 'quick-search';  // Modo padrão

    let chatState = {
        quickSearch: {
            step: 0,
            data: {
                departureDate: null,
                returnDate: null,
                origin: null,
                destination: null,
                passengers: 1
            }
        },
        fullPlanning: {
            step: 0,
            data: {
                destinations: [],
                startDate: null,
                duration: null,
                travelers: 1,
                preferences: {},
                budget: null,
                activities: []
            }
        }
    };

    // Limpar o chat
    function clearChat() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
    }

    // Processar resposta do usuário baseado no modo e estado atual
    function processUserResponse(message) {
        if (chatMode === 'quick-search') {
            processQuickSearchResponse(message);
        } else if (chatMode === 'full-planning') {
            processFullPlanningResponse(message);
        }
    }

    // Processar resposta no modo de busca rápida
    function processQuickSearchResponse(message) {
        const step = chatState.quickSearch.step;

        switch (step) {
            case 0: // Data de ida
                // Tentar extrair a data de ida do formato DD/MM/YYYY
                const departureDateMatch = message.match(/(\d{1,2})[/-](\d{1,2})[/-](\d{4})/);
                if (departureDateMatch) {
                    const day = departureDateMatch[1].padStart(2, '0');
                    const month = departureDateMatch[2].padStart(2, '0');
                    const year = departureDateMatch[3];
                    chatState.quickSearch.data.departureDate = `${year}-${month}-${day}`;

                    // Próxima pergunta
                    chatState.quickSearch.step = 1;
                    addMessageToChat("Quando deseja voltar? (data de volta)", false);
                } else {
                    addMessageToChat("Por favor, informe a data no formato DD/MM/AAAA.", false);
                }
                break;

            case 1: // Data de volta
                const returnDateMatch = message.match(/(\d{1,2})[/-](\d{1,2})[/-](\d{4})/);
                if (returnDateMatch) {
                    const day = returnDateMatch[1].padStart(2, '0');
                    const month = returnDateMatch[2].padStart(2, '0');
                    const year = returnDateMatch[3];
                    chatState.quickSearch.data.returnDate = `${year}-${month}-${day}`;

                    // Próxima pergunta
                    chatState.quickSearch.step = 2;
                    addMessageToChat("De onde você irá sair e para onde deseja ir? (ex: São Paulo para Paris)", false);
                } else {
                    addMessageToChat("Por favor, informe a data no formato DD/MM/AAAA.", false);
                }
                break;

            case 2: // Origem e destino
                // Tentar extrair origem e destino
                const routeMatch = message.match(/([A-Za-zÀ-ÖØ-öø-ÿ\s]+)\s+(?:para|to|->)\s+([A-Za-zÀ-ÖØ-öø-ÿ\s]+)/i);
                if (routeMatch) {
                    chatState.quickSearch.data.origin = routeMatch[1].trim();
                    chatState.quickSearch.data.destination = routeMatch[2].trim();

                    // Buscar voos
                    addMessageToChat("Obrigado! Estou buscando as melhores ofertas de voos para você...", false);
                    searchFlights(chatState.quickSearch.data);
                } else {
                    addMessageToChat("Por favor, informe a origem e o destino no formato 'Cidade A para Cidade B'.", false);
                }
                break;
        }
    }

    // Processar resposta no modo de planejamento completo
    function processFullPlanningResponse(message) {
        const step = chatState.fullPlanning.step;

        switch (step) {
            case 0: // Destinos
                chatState.fullPlanning.data.destinations = message.split(',').map(dest => dest.trim());
                chatState.fullPlanning.step = 1;
                addMessageToChat("Qual a data de início e qual a duração aproximada da sua viagem?", false);
                break;

            case 1: // Data e duração
                // Tentar extrair data e duração
                const dateMatch = message.match(/(\d{1,2})[/-](\d{1,2})[/-](\d{4})/);
                const durationMatch = message.match(/(\d+)\s*(?:dias|semanas|meses|days|weeks)/i);

                if (dateMatch) {
                    const day = dateMatch[1].padStart(2, '0');
                    const month = dateMatch[2].padStart(2, '0');
                    const year = dateMatch[3];
                    chatState.fullPlanning.data.startDate = `${year}-${month}-${day}`;
                }

                if (durationMatch) {
                    chatState.fullPlanning.data.duration = parseInt(durationMatch[1]);
                }

                if (dateMatch || durationMatch) {
                    chatState.fullPlanning.step = 2;
                    addMessageToChat("Quantas pessoas estarão viajando e há alguma preferência específica (classe de voo, tipo de hospedagem)?", false);
                } else {
                    addMessageToChat("Por favor, informe a data no formato DD/MM/AAAA e a duração em dias.", false);
                }
                break;

            case 2: // Viajantes e preferências
                // Tentar extrair número de viajantes
                const travelersMatch = message.match(/(\d+)\s*(?:pessoas|person|people|viajantes|travelers)/i);
                if (travelersMatch) {
                    chatState.fullPlanning.data.travelers = parseInt(travelersMatch[1]);
                } else {
                    // Se não conseguir extrair, assume 1 viajante
                    chatState.fullPlanning.data.travelers = 1;
                }

                // Extrair preferências
                if (message.match(/econômica|economic|economy/i)) {
                    chatState.fullPlanning.data.preferences.flightClass = 'ECONOMY';
                } else if (message.match(/executiva|business/i)) {
                    chatState.fullPlanning.data.preferences.flightClass = 'BUSINESS';
                } else if (message.match(/primeira\s*classe|first\s*class/i)) {
                    chatState.fullPlanning.data.preferences.flightClass = 'FIRST';
                }

                if (message.match(/hotel|resort/i)) {
                    chatState.fullPlanning.data.preferences.accommodationType = 'HOTEL';
                } else if (message.match(/apartamento|apartment/i)) {
                    chatState.fullPlanning.data.preferences.accommodationType = 'APARTMENT';
                } else if (message.match(/hostel|albergue/i)) {
                    chatState.fullPlanning.data.preferences.accommodationType = 'HOSTEL';
                }

                chatState.fullPlanning.step = 3;
                addMessageToChat("Você possui um orçamento definido ou deseja encontrar as melhores ofertas disponíveis?", false);
                break;

            case 3: // Orçamento
                // Tentar extrair orçamento
                const budgetMatch = message.match(/(?:R\$|\$)\s*(\d+(?:,\d+)?(?:\.\d+)?)|(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:reais|dolares|euros|dollars|euros)/i);

                if (budgetMatch) {
                    // Pegar o valor capturado (grupo 1 ou grupo 2)
                    let budgetValue = budgetMatch[1] || budgetMatch[2];
                    // Normalizar formato (substituir vírgula por ponto para parsing)
                    budgetValue = budgetValue.replace(',', '.');
                    chatState.fullPlanning.data.budget = parseFloat(budgetValue);
                } else if (message.match(/melhor(?:es)?\s*oferta|best\s*offer|melhor(?:es)?\s*preço/i)) {
                    // Se o usuário quer as melhores ofertas, não define orçamento
                    chatState.fullPlanning.data.budget = null;
                }

                chatState.fullPlanning.step = 4;
                addMessageToChat("Você deseja incluir passeios ou experiências especiais? Se sim, quais atividades lhe interessam?", false);
                break;

            case 4: // Atividades
                if (!message.match(/(?:não|no|nenhum)/i)) {
                    // Se a resposta não for negativa, extrai atividades
                    chatState.fullPlanning.data.activities = message.split(',').map(activity => activity.trim());
                }

                // Gerar resumo do planejamento
                addMessageToChat("Obrigado por todas as informações! Estou preparando seu planejamento completo de viagem...", false);
                generateTravelPlan(chatState.fullPlanning.data);
                break;
        }
    }

    // Função para buscar voos
    function searchFlights(searchData) {
        // Simulação da busca (na implementação real, chamar a API Amadeus)
        showTypingIndicator();

        setTimeout(() => {
            removeTypingIndicator();

            // Simular resultados da busca
            const results = [
                {
                    airline: "Latam Airlines",
                    flightNumber: "LA8112",
                    departure: searchData.origin,
                    arrival: searchData.destination,
                    departureDate: searchData.departureDate,
                    returnDate: searchData.returnDate,
                    price: "R$ 3.850,00",
                    link: "#"
                },
                {
                    airline: "Gol Linhas Aéreas",
                    flightNumber: "G31024",
                    departure: searchData.origin,
                    arrival: searchData.destination,
                    departureDate: searchData.departureDate,
                    returnDate: searchData.returnDate,
                    price: "R$ 4.120,00",
                    link: "#"
                }
            ];

            // Exibir resultados
            let responseMessage = "Encontrei estas opções para você:\n\n";

            results.forEach((flight, index) => {
                responseMessage += `**Opção ${index + 1}**\n`;
                responseMessage += `Companhia: ${flight.airline}\n`;
                responseMessage += `Voo: ${flight.flightNumber}\n`;
                responseMessage += `Origem: ${flight.departure}\n`;
                responseMessage += `Destino: ${flight.arrival}\n`;
                responseMessage += `Ida: ${formatDate(flight.departureDate)}\n`;
                responseMessage += `Volta: ${formatDate(flight.returnDate)}\n`;
                responseMessage += `Preço: ${flight.price}\n\n`;
            });

            responseMessage += "Você deseja mais informações sobre alguma destas opções ou gostaria de verificar outras datas?";

            addMessageToChat(responseMessage, false);

            // Resetar o estado após a busca
            chatState.quickSearch.step = 0;
        }, 2000);
    }

    // Função para gerar planejamento de viagem
    function generateTravelPlan(planData) {
        // Simulação de geração de planejamento
        showTypingIndicator();

        setTimeout(() => {
            removeTypingIndicator();

            // Criar um resumo do planejamento
            let planSummary = "# Planejamento de Viagem: " + planData.destinations.join(", ") + "\n\n";

            planSummary += "## Informações Gerais\n";
            planSummary += "- **Destinos**: " + planData.destinations.join(", ") + "\n";
            planSummary += "- **Data de início**: " + (planData.startDate ? formatDate(planData.startDate) : "Não especificada") + "\n";
            planSummary += "- **Duração**: " + (planData.duration ? `${planData.duration} dias` : "Não especificada") + "\n";
            planSummary += "- **Viajantes**: " + planData.travelers + "\n";
            planSummary += "- **Orçamento**: " + (planData.budget ? `R$ ${planData.budget.toFixed(2)}` : "Melhores ofertas disponíveis") + "\n\n";

            planSummary += "## Preferências\n";
            planSummary += "- **Classe do voo**: " + (planData.preferences.flightClass || "Não especificada") + "\n";
            planSummary += "- **Tipo de hospedagem**: " + (planData.preferences.accommodationType || "Não especificada") + "\n\n";

            if (planData.activities && planData.activities.length > 0) {
                planSummary += "## Atividades de Interesse\n";
                planData.activities.forEach(activity => {
                    planSummary += "- " + activity + "\n";
                });
                planSummary += "\n";
            }

            // Simular itinerário
            planSummary += "## Itinerário Sugerido\n\n";

            const startDate = planData.startDate ? new Date(planData.startDate) : new Date();

            for (let day = 1; day <= (planData.duration || 5); day++) {
                const currentDate = new Date(startDate);
                currentDate.setDate(startDate.getDate() + day - 1);

                planSummary += `### Dia ${day} (${formatDate(currentDate.toISOString().split('T')[0])})\n`;

                if (day === 1) {
                    planSummary += "- Chegada em " + planData.destinations[0] + "\n";
                    planSummary += "- Check-in no hotel\n";
                    planSummary += "- Passeio de reconhecimento pela região\n";
                    planSummary += "- Jantar de boas-vindas\n\n";
                } else if (day === planData.duration) {
                    planSummary += "- Café da manhã no hotel\n";
                    planSummary += "- Tempo livre para compras\n";
                    planSummary += "- Check-out do hotel\n";
                    planSummary += "- Traslado para o aeroporto\n";
                    planSummary += "- Voo de volta\n\n";
                } else {
                    // Preencher com atividades simuladas
                    const activities = [
                        "Visita a museus",
                        "Tour pela cidade",
                        "Passeio de barco",
                        "Almoço em restaurante local",
                        "Visita a ponto turístico",
                        "Experiência gastronômica",
                        "Caminhada em parque natural",
                        "Compras no centro comercial"
                    ];

                    // Selecionar 3-4 atividades aleatórias
                    const numActivities = 3 + Math.floor(Math.random() * 2);
                    const dayActivities = [];

                    for (let i = 0; i < numActivities; i++) {
                        const randomIndex = Math.floor(Math.random() * activities.length);
                        dayActivities.push("- " + activities[randomIndex]);
                        activities.splice(randomIndex, 1);
                    }

                    planSummary += dayActivities.join("\n") + "\n\n";
                }
            }

            // Opções de acomodação simuladas
            planSummary += "## Opções de Acomodação\n\n";

            const accommodations = [
                {
                    name: "Hotel Central " + planData.destinations[0],
                    stars: 4,
                    pricePerNight: 350,
                    features: ["Wi-Fi grátis", "Café da manhã", "Piscina", "Academia"]
                },
                {
                    name: "Resort " + planData.destinations[0] + " Palace",
                    stars: 5,
                    pricePerNight: 580,
                    features: ["Wi-Fi grátis", "Café da manhã", "Piscina", "Academia", "Spa", "Restaurante 5 estrelas"]
                }
            ];

            accommodations.forEach((acc, index) => {
                planSummary += `### Opção ${index + 1}: ${acc.name}\n`;
                planSummary += `- **Classificação**: ${"★".repeat(acc.stars)}\n`;
                planSummary += `- **Preço por noite**: R$ ${acc.pricePerNight.toFixed(2)}\n`;
                planSummary += `- **Recursos**: ${acc.features.join(", ")}\n\n`;
            });

            // Simular opções de voo
            planSummary += "## Opções de Voo\n\n";

            const flights = [
                {
                    airline: "Latam Airlines",
                    outbound: {
                        flightNumber: "LA4587",
                        departure: "10:25",
                        arrival: "16:40",
                        duration: "6h 15min"
                    },
                    inbound: {
                        flightNumber: "LA4588",
                        departure: "18:30",
                        arrival: "00:45 (+1)",
                        duration: "6h 15min"
                    },
                    price: 3250
                },
                {
                    airline: "Gol Linhas Aéreas",
                    outbound: {
                        flightNumber: "G32451",
                        departure: "08:15",
                        arrival: "14:30",
                        duration: "6h 15min"
                    },
                    inbound: {
                        flightNumber: "G32452",
                        departure: "15:45",
                        arrival: "22:00",
                        duration: "6h 15min"
                    },
                    price: 2980
                }
            ];

            flights.forEach((flight, index) => {
                planSummary += `### Opção ${index + 1}: ${flight.airline}\n`;
                planSummary += "#### Voo de Ida\n";
                planSummary += `- **Voo**: ${flight.outbound.flightNumber}\n`;
                planSummary += `- **Partida**: ${flight.outbound.departure}\n`;
                planSummary += `- **Chegada**: ${flight.outbound.arrival}\n`;
                planSummary += `- **Duração**: ${flight.outbound.duration}\n\n`;

                planSummary += "#### Voo de Volta\n";
                planSummary += `- **Voo**: ${flight.inbound.flightNumber}\n`;
                planSummary += `- **Partida**: ${flight.inbound.departure}\n`;
                planSummary += `- **Chegada**: ${flight.inbound.arrival}\n`;
                planSummary += `- **Duração**: ${flight.inbound.duration}\n\n`;

                planSummary += `- **Preço total**: R$ ${flight.price.toFixed(2)}\n\n`;
            });

            // Adicionar estimativa de orçamento total
            const flightPrice = flights[0].price;
            const accommodationPrice = accommodations[0].pricePerNight * (planData.duration || 5);
            const foodAndTransportPrice = 150 * (planData.duration || 5);
            const activitiesPrice = 200 * (planData.duration || 5);
            const totalPrice = flightPrice + accommodationPrice + foodAndTransportPrice + activitiesPrice;

            planSummary += "## Estimativa de Orçamento\n\n";
            planSummary += `- **Voos**: R$ ${flightPrice.toFixed(2)}\n`;
            planSummary += `- **Hospedagem**: R$ ${accommodationPrice.toFixed(2)}\n`;
            planSummary += `- **Alimentação e Transporte**: R$ ${foodAndTransportPrice.toFixed(2)}\n`;
            planSummary += `- **Atividades e Passeios**: R$ ${activitiesPrice.toFixed(2)}\n`;
            planSummary += `- **Total Estimado**: R$ ${totalPrice.toFixed(2)}\n\n`;

            // Conclusão
            planSummary += "## Próximos Passos\n\n";
            planSummary += "Você gostaria de:\n";
            planSummary += "1. Salvar este planejamento\n";
            planSummary += "2. Ajustar algum detalhe\n";
            planSummary += "3. Gerar um PDF do planejamento\n";
            planSummary += "4. Receber alertas de preços para estas opções\n\n";
            planSummary += "Me avise como posso ajudá-lo a finalizar este planejamento!";

            addMessageToChat(planSummary, false);

            // Resetar o estado após a geração do plano
            chatState.fullPlanning.step = 0;
        }, 3000);
    }

    // Função para formatar data (YYYY-MM-DD para DD/MM/YYYY)
    function formatDate(dateString) {
        const parts = dateString.split('-');
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        return dateString;
    }

    // Função auxiliar para mostrar indicador de digitação
    function showTypingIndicator() {
        // Implementação para mostrar o indicador de digitação
        // ...
    }

    // Função auxiliar para remover indicador de digitação
    function removeTypingIndicator() {
        // Implementação para remover o indicador de digitação
        // ...
    }

    // Função para adicionar monitoramento de preço
    function addPriceMonitor(data) {
        // Implementação para adicionar monitoramento de preço
        // ...
    }

    // Função para buscar hotéis
    function searchHotels(searchData) {
        // Implementação para buscar hotéis
        // ...
    }


    // Carregar conversas existentes
    loadConversations();
});
// Variáveis globais
let currentConversationId = null;
let chatMode = 'quick-search'; // 'quick-search' ou 'full-planning'
let chatContext = {
    mode: 'quick-search',
    quickSearchStep: 0,
    quickSearchData: {},
    fullPlanningStep: 0,
    fullPlanningData: {}
};

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Selecionar elementos principais
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const quickSearchModeBtn = document.getElementById('quick-search-mode');
    const fullPlanningModeBtn = document.getElementById('full-planning-mode');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const conversationsList = document.getElementById('conversations-list');
    const newConversationBtn = document.getElementById('new-conversation');

    // Toggle sidebar
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        const isCollapsed = sidebar.classList.contains('collapsed');
        sidebarToggle.innerHTML = isCollapsed ? 
            '<i class="fas fa-chevron-right"></i>' : 
            '<i class="fas fa-chevron-left"></i>';
    });

    // Trocar entre modos de chat
    quickSearchModeBtn.addEventListener('click', function() {
        setActiveChatMode('quick-search');
    });

    fullPlanningModeBtn.addEventListener('click', function() {
        setActiveChatMode('full-planning');
    });

    // Enviar mensagem usando tecla Enter
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Ajustar altura do textarea quando o usuário digita
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Formulário de chat
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });

    // Navegação lateral
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const section = this.getAttribute('data-section');

            // Atualizar item ativo na navegação
            document.querySelectorAll('.sidebar-nav-item').forEach(navItem => {
                navItem.classList.remove('active');
            });
            this.classList.add('active');

            // Mostrar seção correta na barra lateral
            document.querySelectorAll('.sidebar-section').forEach(sectionEl => {
                sectionEl.classList.remove('active');
            });

            if (section === 'chat') {
                document.getElementById('conversations-section').classList.add('active');
            } else if (section === 'plans') {
                document.getElementById('plans-section').classList.add('active');
            }

            // Mostrar conteúdo correto
            document.querySelectorAll('.content-section').forEach(contentSection => {
                contentSection.classList.remove('active');
            });

            if (section === 'chat') {
                document.getElementById('chat-section').classList.add('active');
            } else if (section === 'plans') {
                document.getElementById('plans-detail-section').classList.add('active');
            } else if (section === 'profile') {
                document.getElementById('profile-section').classList.add('active');
            }
        });
    });

    // Nova conversa
    newConversationBtn.addEventListener('click', function() {
        currentConversationId = null;
        document.getElementById('chat-messages').innerHTML = '';
        addAssistantMessage("Olá! Eu sou Flai, seu assistente de viagens virtual. Como posso ajudar você hoje?");
        setActiveChatMode(chatMode); // Reiniciar o modo atual
    });

    // Carregar conversas existentes
    loadConversations();

    // Carregar planos de viagem
    loadPlans();

    // Carregar perfil do usuário
    loadProfile();

    // Modal de login
    document.getElementById('login-button').addEventListener('click', function() {
        document.getElementById('login-modal').style.display = 'flex';
    });

    // Modal de cadastro
    document.getElementById('signup-button').addEventListener('click', function() {
        document.getElementById('signup-modal').style.display = 'flex';
    });

    // Fechar modais
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });

    // Formulários de modal
    document.getElementById('login-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('login-modal').style.display = 'none';
                // Atualizar UI para usuário logado
                document.querySelector('.header-actions').innerHTML = `
                    <span class="user-greeting">Olá, ${data.user.name}</span>
                    <button id="logout-button" class="btn btn-outline"><i class="fas fa-sign-out-alt"></i> Sair</button>
                `;

                // Adicionar event listener para logout
                document.getElementById('logout-button').addEventListener('click', logout);

                // Recarregar dados
                loadConversations();
                loadPlans();
                loadProfile();
            } else {
                alert(data.error || 'Erro ao fazer login');
            }
        })
        .catch(error => {
            console.error('Erro no login:', error);
            alert('Erro ao fazer login. Tente novamente.');
        });
    });

    document.getElementById('signup-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const name = document.getElementById('signup-name').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const passwordConfirm = document.getElementById('signup-password-confirm').value;

        if (password !== passwordConfirm) {
            alert('As senhas não coincidem');
            return;
        }

        fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('signup-modal').style.display = 'none';
                alert('Conta criada com sucesso! Faça login para continuar.');

                // Mostrar modal de login
                document.getElementById('login-modal').style.display = 'flex';
                document.getElementById('login-email').value = email;
            } else {
                alert(data.error || 'Erro ao criar conta');
            }
        })
        .catch(error => {
            console.error('Erro no cadastro:', error);
            alert('Erro ao criar conta. Tente novamente.');
        });
    });

    // Formulário de perfil
    document.getElementById('profile-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const profileData = {
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
            body: JSON.stringify(profileData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Perfil atualizado com sucesso!');
            } else {
                alert(data.error || 'Erro ao atualizar perfil');
            }
        })
        .catch(error => {
            console.error('Erro ao atualizar perfil:', error);
            alert('Erro ao atualizar perfil. Tente novamente.');
        });
    });
});

// Função para enviar mensagem
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();

    if (message === '') {
        return;
    }

    // Adicionar mensagem do usuário ao chat
    addUserMessage(message);

    // Limpar input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Mostrar indicador de digitação
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'message assistant typing';
    typingIndicator.id = 'typing-indicator';
    typingIndicator.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    document.getElementById('chat-messages').appendChild(typingIndicator);

    // Rolar para o final do chat
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Enviar mensagem para o backend
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
        document.getElementById('typing-indicator').remove();

        // Atualizar ID da conversa
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
        }

        // Atualizar contexto do chat
        if (data.context) {
            chatContext = data.context;
        }

        // Processar resposta com base no modo do chat
        let processedResponse = data.response;
        if (chatContext.mode === 'quick-search') {
            processedResponse = processQuickSearchResponse(data.response);
        } else if (chatContext.mode === 'full-planning') {
            processedResponse = processFullPlanningResponse(data.response);
        }

        // Adicionar resposta do assistente
        addAssistantMessage(processedResponse);

        // Executar ação do chat, se houver
        if (data.action) {
            executeAction(data.action);
        }

        // Atualizar lista de conversas
        loadConversations();
    })
    .catch(error => {
        console.log('Error getting chat response:', error);

        // Remover indicador de digitação
        if (document.getElementById('typing-indicator')) {
            document.getElementById('typing-indicator').remove();
        }

        // Mostrar mensagem de erro
        addAssistantMessage("Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente mais tarde.");
    });
}

// Funções para adicionar mensagens ao chat
function addUserMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = 'message user';
    messageElement.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
        </div>
        <div class="message-avatar">
            <i class="fas fa-user"></i>
        </div>
    `;
    chatMessages.appendChild(messageElement);

    // Rolar para o final do chat
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addAssistantMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = 'message assistant';

    // Verificar se a mensagem contém HTML (para botões de ação, etc.)
    if (message.includes('<')) {
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                ${message}
            </div>
        `;
    } else {
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;
    }

    chatMessages.appendChild(messageElement);

    // Rolar para o final do chat
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Função para definir o modo de chat ativo
function setActiveChatMode(mode) {
    chatMode = mode;
    chatContext.mode = mode;

    // Resetar passo atual
    if (mode === 'quick-search') {
        chatContext.quickSearchStep = 0;
        chatContext.quickSearchData = {};
        document.getElementById('quick-search-mode').classList.add('active');
        document.getElementById('full-planning-mode').classList.remove('active');

        // Mensagem de boas-vindas para busca rápida
        if (!currentConversationId) {
            document.getElementById('chat-messages').innerHTML = '';
            addAssistantMessage(`
                <p>Você está no modo: <strong>Busca Rápida</strong></p>
                <p>Neste modo, podemos encontrar rapidamente os melhores voos para a sua viagem.</p>
                <p>Como posso ajudar?</p>
            `);
        }
    } else if (mode === 'full-planning') {
        chatContext.fullPlanningStep = 0;
        chatContext.fullPlanningData = {};
        document.getElementById('quick-search-mode').classList.remove('active');
        document.getElementById('full-planning-mode').classList.add('active');

        // Mensagem de boas-vindas para planejamento completo
        if (!currentConversationId) {
            document.getElementById('chat-messages').innerHTML = '';
            addAssistantMessage(`
                <p>Você está no modo: <strong>Planejamento Completo</strong></p>
                <p>Neste modo, vamos desenvolver um plano detalhado para sua viagem, incluindo voos, hospedagem e passeios.</p>
                <p>Como posso ajudar no seu planejamento?</p>
            `);
        }
    }
}

// Funções para processar respostas com base no modo de chat
function processQuickSearchResponse(message) {
    // Processar resposta para integrar botões de ação para compra direta
    if (message.includes("voo") || message.includes("passagem") || message.includes("companhia aérea") || 
        message.includes("Companhia") || message.includes("Argentina") || message.includes("primeira semana")) {

        // Simular uma oferta de passagem com dados da conversa
        const passagemHtml = `
            <div class="flight-offer-card">
                <div class="flight-offer-header">
                    <div class="airline-logo">
                        <img src="https://logodownload.org/wp-content/uploads/2016/12/latam-logo-0.png" alt="LATAM">
                    </div>
                    <div class="flight-price">
                        <span class="price-value">R$ 2.450,00</span>
                        <span class="price-installment">10x R$ 245,00 sem juros</span>
                    </div>
                </div>
                <div class="flight-details">
                    <div class="flight-route">
                        <div class="departure">
                            <span class="airport-code">GRU</span>
                            <span class="time">08:20</span>
                            <span class="date">01/06/2024</span>
                        </div>
                        <div class="flight-line">
                            <div class="line"></div>
                            <i class="fas fa-plane"></i>
                        </div>
                        <div class="arrival">
                            <span class="airport-code">EZE</span>
                            <span class="time">11:45</span>
                            <span class="date">01/06/2024</span>
                        </div>
                    </div>
                    <div class="flight-info">
                        <span class="duration"><i class="far fa-clock"></i> 3h 25min</span>
                        <span class="direct"><i class="fas fa-check-circle"></i> Voo direto</span>
                    </div>
                </div>
                <div class="flight-actions">
                    <button class="btn btn-primary" onclick="bookFlight('LATAM1234')">
                        <i class="fas fa-shopping-cart"></i> Comprar agora
                    </button>
                    <button class="btn btn-outline" onclick="addToMonitor('flight', {id: 'LATAM1234'})">
                        <i class="fas fa-bell"></i> Monitorar preço
                    </button>
                </div>
            </div>
        `;

        // Adicionar a oferta após a resposta do assistente
        return message + '<p>Encontrei esta opção para sua viagem:</p>' + passagemHtml;
    }

    return message;
}

function processFullPlanningResponse(message) {
    // Processar resposta para o modo de planejamento completo
    chatContext.fullPlanningStep = chatContext.fullPlanningStep || 0;

    // Se estivermos no último passo do planejamento, adicionar opções de voo e hotel
    if (chatContext.fullPlanningStep >= 4 && message.includes("orçamento") || message.includes("plano")) {
        // Adicionar opções de voo e hotel ao final da mensagem
        const opcoesHTML = `
            <div class="full-plan-options">
                <h4>Opções de Voo</h4>
                <div class="flight-option-card">
                    <div class="flight-option-header">
                        <div class="airline">
                            <img src="https://logodownload.org/wp-content/uploads/2016/12/latam-logo-0.png" alt="LATAM">
                            <span>LATAM Airlines</span>
                        </div>
                        <div class="price">R$ 2.780,00</div>
                    </div>
                    <div class="flight-option-details">
                        <div class="route-info">
                            <div class="route">
                                <div class="from">
                                    <div class="code">GRU</div>
                                    <div class="time">08:45</div>
                                </div>
                                <div class="arrow">
                                    <i class="fas fa-long-arrow-alt-right"></i>
                                </div>
                                <div class="to">
                                    <div class="code">EZE</div>
                                    <div class="time">12:10</div>
                                </div>
                            </div>
                            <div class="date">
                                <i class="far fa-calendar-alt"></i> 01/06/2024
                            </div>
                        </div>
                        <div class="flight-info">
                            <div class="duration">
                                <i class="far fa-clock"></i> 3h 25min
                            </div>
                            <div class="type">
                                <i class="fas fa-plane"></i> Direto
                            </div>
                        </div>
                    </div>
                    <div class="flight-option-actions">
                        <button class="btn btn-primary" onclick="bookFlight('LATAM4567')">
                            <i class="fas fa-check"></i> Selecionar este voo
                        </button>
                    </div>
                </div>

                <h4>Opções de Hospedagem</h4>
                <div class="hotel-option-card">
                    <div class="hotel-option-header">
                        <div class="hotel-name">Hotel Alvear Palace</div>
                        <div class="hotel-stars">
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                        </div>
                    </div>
                    <div class="hotel-option-image">
                        <img src="https://media-cdn.tripadvisor.com/media/photo-s/16/31/d0/63/alvear-palace-hotel.jpg" alt="Hotel Alvear Palace">
                    </div>
                    <div class="hotel-option-details">
                        <div class="location">
                            <i class="fas fa-map-marker-alt"></i> Recoleta, Buenos Aires
                        </div>
                        <div class="rating">
                            <span class="score">9.6</span> Excelente (230 avaliações)
                        </div>
                        <div class="price">
                            <span class="value">R$ 1.250,00</span> por noite
                        </div>
                    </div>
                    <div class="hotel-option-actions">
                        <button class="btn btn-primary" onclick="bookHotel('ALVEAR123')">
                            <i class="fas fa-check"></i> Selecionar este hotel
                        </button>
                    </div>
                </div>
            </div>
        `;

        return message + opcoesHTML;
    }

    return message;
}

// Função para executar ações com base na resposta do backend
function executeAction(action) {
    if (!action) return;

    switch(action.type) {
        case 'search_flights':
            searchFlights(action.data);
            break;
        case 'generate_travel_plan':
            generateTravelPlan(action.data);
            break;
        default:
            console.log('Unknown action type:', action.type);
    }
}

// Funções para carregar dados do backend
function loadConversations() {
    fetch('/api/conversations')
        .then(response => response.json())
        .then(data => {
            const conversationsList = document.getElementById('conversations-list');
            conversationsList.innerHTML = '';

            if (data.conversations && data.conversations.length > 0) {
                data.conversations.forEach(conversation => {
                    const template = document.getElementById('conversation-item-template');
                    const clone = document.importNode(template.content, true);

                    const item = clone.querySelector('.sidebar-item');
                    item.setAttribute('data-id', conversation.id);

                    const title = clone.querySelector('.sidebar-item-title');
                    title.textContent = conversation.title;

                    const subtitle = clone.querySelector('.sidebar-item-subtitle');
                    // Formatar data para exibição
                    const date = new Date(conversation.created_at);
                    subtitle.textContent = date.toLocaleDateString('pt-BR');

                    // Adicionar event listener para carregar conversa
                    item.addEventListener('click', function() {
                        loadConversation(conversation.id);
                    });

                    conversationsList.appendChild(clone);
                });
            } else {
                conversationsList.innerHTML = '<div class="empty-list">Nenhuma conversa encontrada</div>';
            }
        })
        .catch(error => {
            console.log('Error loading conversations:', error);
        });
}

function loadConversation(conversationId) {
    if (currentConversationId === conversationId) {
        return;
    }

    fetch(`/api/conversations/${conversationId}`)
        .then(response => response.json())
        .then(data => {
            currentConversationId = conversationId;

            // Limpar chat
            document.getElementById('chat-messages').innerHTML = '';

            // Adicionar mensagens ao chat
            data.messages.forEach(message => {
                if (message.is_user) {
                    addUserMessage(message.content);
                } else {
                    addAssistantMessage(message.content);
                }
            });

            // Ativar seção de chat
            document.querySelectorAll('.sidebar-nav-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector('.sidebar-nav-item[data-section="chat"]').classList.add('active');

            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById('chat-section').classList.add('active');

            // Destacar conversa ativa na lista
            document.querySelectorAll('#conversations-list .sidebar-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`#conversations-list .sidebar-item[data-id="${conversationId}"]`).classList.add('active');
        })
        .catch(error => {
            console.log('Error loading conversation:', error);
            alert('Erro ao carregar conversa. Tente novamente.');
        });
}

function loadPlans() {
    fetch('/api/plans')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const plansList = document.getElementById('plans-list');
            plansList.innerHTML = '';

            if (data && data.length > 0) {
                data.forEach(plan => {
                    const template = document.getElementById('plan-item-template');
                    const clone = document.importNode(template.content, true);

                    const item = clone.querySelector('.sidebar-item');
                    item.setAttribute('data-id', plan.id);

                    const title = clone.querySelector('.sidebar-item-title');
                    title.textContent = plan.title;

                    const subtitle = clone.querySelector('.sidebar-item-subtitle');
                    subtitle.textContent = plan.destination;

                    // Adicionar event listener para carregar plano
                    item.addEventListener('click', function() {
                        loadPlan(plan.id);
                    });

                    plansList.appendChild(clone);
                });
            } else {
                plansList.innerHTML = '<div class="empty-list">Nenhum plano de viagem encontrado</div>';
            }
        })
        .catch(error => {
            console.log('Error loading plans:', error);
        });
}

function loadPlan(planId) {
    fetch(`/api/plan/${planId}`)
        .then(response => response.json())
        .then(plan => {
            const planDetails = document.getElementById('plan-details');

            // Formatar datas
            const startDate = plan.start_date ? new Date(plan.start_date).toLocaleDateString('pt-BR') : 'Não definida';
            const endDate = plan.end_date ? new Date(plan.end_date).toLocaleDateString('pt-BR') : 'Não definida';

            // Criar HTML para o plano
            planDetails.innerHTML = `
                <div class="plan-header">
                    <h3>${plan.title}</h3>
                    <div class="plan-meta">
                        <div class="plan-meta-item">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${plan.destination}</span>
                        </div>
                        <div class="plan-meta-item">
                            <i class="fas fa-calendar"></i>
                            <span>${startDate} - ${endDate}</span>
                        </div>
                    </div>
                </div>

                <div class="plan-details-content">
                    <div class="plan-section">
                        <h4><i class="fas fa-info-circle"></i> Detalhes</h4>
                        <div class="plan-details-text">
                            ${plan.details || 'Nenhum detalhe disponível.'}
                        </div>
                    </div>

                    <div class="plan-section">
                        <h4><i class="fas fa-plane"></i> Voos</h4>
                        <div class="plan-flights">
                            ${renderFlights(plan.flights)}
                        </div>
                    </div>

                    <div class="plan-section">
                        <h4><i class="fas fa-hotel"></i> Hospedagem</h4>
                        <div class="plan-accommodations">
                            ${renderAccommodations(plan.accommodations)}
                        </div>
                    </div>

                    <div class="plan-actions">
                        <button class="btn btn-primary" onclick="downloadPlanPDF(${plan.id})">
                            <i class="fas fa-file-pdf"></i> Baixar PDF
                        </button>
                        <button class="btn btn-outline" onclick="sharePlan(${plan.id})">
                            <i class="fas fa-share-alt"></i> Compartilhar
                        </button>
                    </div>
                </div>
            `;

            // Ativar seção de detalhes do plano
            document.querySelectorAll('.sidebar-nav-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector('.sidebar-nav-item[data-section="plans"]').classList.add('active');

            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById('plans-detail-section').classList.add('active');
        })
        .catch(error => {
            console.log('Error loading plan:', error);
            alert('Erro ao carregar plano. Tente novamente.');
        });
}

function renderFlights(flights) {
    if (!flights || flights.length === 0) {
        return '<div class="empty-section">Nenhum voo adicionado a este plano.</div>';
    }

    let html = '';

    flights.forEach(flight => {
        // Formatar datas
        const departureTime = flight.departure_time ? new Date(flight.departure_time).toLocaleString('pt-BR') : '';
        const arrivalTime = flight.arrival_time ? new Date(flight.arrival_time).toLocaleString('pt-BR') : '';

        html += `
            <div class="flight-card">
                <div class="flight-card-header">
                    <div class="flight-airline">${flight.airline || 'Companhia não especificada'} ${flight.flight_number || ''}</div>
                    <div class="flight-price">${flight.price ? `${flight.currency} ${flight.price}` : 'Preço não disponível'}</div>
                </div>
                <div class="flight-card-content">
                    <div class="flight-route">
                        <div class="flight-origin">
                            <div class="flight-code">${flight.departure_location || ''}</div>
                            <div class="flight-time">${departureTime}</div>
                        </div>
                        <div class="flight-divider">
                            <i class="fas fa-plane"></i>
                        </div>
                        <div class="flight-destination">
                            <div class="flight-code">${flight.arrival_location || ''}</div>
                            <div class="flight-time">${arrivalTime}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    return html;
}

function renderAccommodations(accommodations) {
    if (!accommodations || accommodations.length === 0) {
        return '<div class="empty-section">Nenhuma hospedagem adicionada a este plano.</div>';
    }

    let html = '';

    accommodations.forEach(acc => {
        // Formatar datas
        const checkIn = acc.check_in ? new Date(acc.check_in).toLocaleDateString('pt-BR') : 'Não definido';
        const checkOut = acc.check_out ? new Date(acc.check_out).toLocaleDateString('pt-BR') : 'Não definido';

        // Criar estrelas para classificação
        let stars = '';
        if (acc.stars) {
            for (let i = 0; i < acc.stars; i++) {
                stars += '<i class="fas fa-star"></i>';
            }
        }

        html += `
            <div class="accommodation-card">
                <div class="accommodation-card-header">
                    <div class="accommodation-name">${acc.name || 'Hospedagem não especificada'}</div>
                    <div class="accommodation-rating">${stars}</div>
                </div>
                <div class="accommodation-card-content">
                    <div class="accommodation-location">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${acc.location || 'Localização não disponível'}</span>
                    </div>
                    <div class="accommodation-dates">
                        <div class="checkin">
                            <i class="fas fa-calendar-check"></i>
                            <span>Check-in: ${checkIn}</span>
                        </div>
                        <div class="checkout">
                            <i class="fas fa-calendar-times"></i>
                            <span>Check-out: ${checkOut}</span>
                        </div>
                    </div>
                    <div class="accommodation-price">
                        <i class="fas fa-tag"></i>
                        <span>${acc.price_per_night ? `${acc.currency} ${acc.price_per_night}/noite` : 'Preço não disponível'}</span>
                    </div>
                </div>
            </div>
        `;
    });

    return html;
}

function loadProfile() {
    fetch('/api/profile')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(profile => {
            // Preencher formulário de perfil
            document.getElementById('profile-name').value = profile.name || '';
            document.getElementById('profile-email').value = profile.email || '';
            document.getElementById('profile-phone').value = profile.phone || '';

            // Preencher preferências
            if (profile.preferences) {
                document.getElementById('profile-preferred-destinations').value = profile.preferences.preferred_destinations || '';

                const accommodationType = document.getElementById('profile-accommodation-type');
                if (profile.preferences.accommodation_type) {
                    for (let i = 0; i < accommodationType.options.length; i++) {
                        if (accommodationType.options[i].value === profile.preferences.accommodation_type) {
                            accommodationType.selectedIndex = i;
                            break;
                        }
                    }
                }

                const budget = document.getElementById('profile-budget');
                if (profile.preferences.budget) {
                    for (let i = 0; i < budget.options.length; i++) {
                        if (budget.options[i].value === profile.preferences.budget) {
                            budget.selectedIndex = i;
                            break;
                        }
                    }
                }
            }
        })
        .catch(error => {
            console.log('Error loading profile:', error);
        });
}

// Funções de ação
function searchFlights(data) {
    // Mostrar indicador de busca
    addAssistantMessage('Buscando as melhores opções de voos para você...');

    fetch('/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: 'flights',
            params: data
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            addAssistantMessage(`Desculpe, encontrei um problema ao buscar voos: ${result.error}`);
            return;
        }

        if (!result.flights || result.flights.length === 0) {
            addAssistantMessage('Desculpe, não encontrei voos disponíveis com os critérios informados. Poderia ajustar as datas ou destinos?');
            return;
        }

        // Criar mensagem com resultados
        let message = '<p>Encontrei estas opções de voo para você:</p>';
        message += '<div class="flights-results">';

        result.flights.forEach((flight, index) => {
            if (index >= 3) return; // Mostrar apenas os 3 primeiros resultados

            // Extrair informações do voo
            const departureTime = new Date(flight.departure.time).toLocaleString('pt-BR');
            const arrivalTime = new Date(flight.arrival.time).toLocaleString('pt-BR');

            message += `
                <div class="flight-result-card">
                    <div class="flight-result-header">
                        <div class="flight-route">${flight.departure.airport} → ${flight.arrival.airport}</div>
                        <div class="flight-price">${flight.price}</div>
                    </div>
                    <div class="flight-result-details">
                        <div class="flight-times">
                            <span>Saída: ${departureTime}</span>
                            <span>Chegada: ${arrivalTime}</span>
                        </div>
                        <div class="flight-duration">Duração: ${flight.duration.replace('PT', '').replace('H', 'h ').replace('M', 'm')}</div>
                        <div class="flight-segments">Escalas: ${flight.segments > 1 ? (flight.segments - 1) : 'Voo direto'}</div>
                    </div>
                    <div class="flight-result-actions">
                        <button class="btn btn-primary book-flight-btn" onclick="bookFlight('${flight.id}')">
                            <i class="fas fa-shopping-cart"></i> Comprar
                        </button>
                        <button class="btn btn-outline add-to-monitor-btn" onclick="addToMonitor('flight', ${JSON.stringify(flight).replace(/"/g, '&quot;')})">
                            <i class="fas fa-bell"></i> Monitorar Preço
                        </button>
                    </div>
                </div>
            `;
        });

        if (result.flights.length > 3) {
            message += `<div class="more-results">E mais ${result.flights.length - 3} opções disponíveis...</div>`;
        }

        message += '</div>';

        addAssistantMessage(message);
    })
    .catch(error => {
        console.log('Error searching flights:', error);
        addAssistantMessage('Desculpe, ocorreu um erro ao buscar os voos. Por favor, tente novamente mais tarde.');
    });
}

function generateTravelPlan(data) {
    // Implementação real a ser feita com base nos dados coletados
    addAssistantMessage("Gerando seu plano de viagem completo...");

    // Exemplo de geração de plano
    setTimeout(() => {
        const planMessage = `
            <div class="travel-plan">
                <h4>Seu Plano de Viagem para ${data.destinations}</h4>

                <div class="travel-plan-section">
                    <h5>Resumo</h5>
                    <p><strong>Destinos:</strong> ${data.destinations}</p>
                    <p><strong>Período:</strong> ${data.dateAndDuration}</p>
                    <p><strong>Viajantes:</strong> ${data.peopleAndPreferences}</p>
                    <p><strong>Orçamento:</strong> ${data.budget}</p>
                </div>

                <div class="travel-plan-section">
                    <h5>Voos Recomendados</h5>
                    <div class="flight-option">
                        <div class="flight-header">
                            <span class="flight-company">LATAM</span>
                            <span class="flight-price">R$ 1.880,00</span>
                        </div>
                        <div class="flight-details">
                            <p><strong>Ida:</strong> São Paulo (GRU) → Buenos Aires (EZE), 15 Jun, 08:30 - 11:45</p>
                            <p><strong>Volta:</strong> Buenos Aires (EZE) → São Paulo (GRU), 22 Jun, 14:20 - 17:35</p>
                        </div>
                        <button class="btn btn-primary" onclick="bookFlight('mock-flight-1')">Reservar</button>
                    </div>
                </div>

                <div class="travel-plan-section">
                    <h5>Hospedagens Recomendadas</h5>
                    <div class="hotel-option">
                        <div class="hotel-header">
                            <span class="hotel-name">Hotel Faena Buenos Aires</span>
                            <span class="hotel-price">R$ 780,00/noite</span>
                        </div>
                        <div class="hotel-details">
                            <p><strong>Localização:</strong> Puerto Madero, Buenos Aires</p>
                            <p><strong>Avaliação:</strong> 4.8/5 (320 avaliações)</p>
                        </div>
                        <button class="btn btn-primary" onclick="bookHotel('mock-hotel-1')">Reservar</button>
                    </div>
                </div>

                <div class="travel-plan-section">
                    <h5>Roteiro Sugerido</h5>
                    <div class="itinerary">
                        <div class="itinerary-day">
                            <h6>Dia 1: Chegada</h6>
                            <p>Chegada em Buenos Aires, check-in no hotel e passeio pelo Puerto Madero.</p>
                        </div>
                        <div class="itinerary-day">
                            <h6>Dia 2: Centro Histórico</h6>
                            <p>Visita à Plaza de Mayo, Casa Rosada e Catedral Metropolitana.</p>
                        </div>
                        <div class="itinerary-day">
                            <h6>Dia 3: San Telmo e La Boca</h6>
                            <p>Explore os bairros históricos e visite o estádio La Bombonera.</p>
                        </div>
                    </div>
                </div>

                <div class="travel-plan-actions">
                    <button class="btn btn-primary" onclick="saveTravelPlan()">Salvar Plano</button>
                    <button class="btn btn-outline" onclick="downloadPlan()">Baixar PDF</button>
                </div>
            </div>
        `;

        addAssistantMessage(planMessage);
    }, 2000);
}

// Funções de utilidade
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function logout() {
    fetch('/logout')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Restaurar UI para usuário não logado
                document.querySelector('.header-actions').innerHTML = `
                    <button id="login-button" class="btn btn-outline"><i class="fas fa-sign-in-alt"></i> Entrar</button>
                    <button id="signup-button" class="btn btn-primary"><i class="fas fa-user-plus"></i> Cadastrar</button>
                `;

                // Adicionar event listeners novamente
                document.getElementById('login-button').addEventListener('click', function() {
                    document.getElementById('login-modal').style.display = 'flex';
                });

                document.getElementById('signup-button').addEventListener('click', function() {
                    document.getElementById('signup-modal').style.display = 'flex';
                });

                // Limpar dados
                document.getElementById('conversations-list').innerHTML = '';
                document.getElementById('plans-list').innerHTML = '';

                // Redefinir variáveis
                currentConversationId = null;

                // Limpar chat
                document.getElementById('chat-messages').innerHTML = '';
                addAssistantMessage("Olá! Eu sou Flai, seu assistente de viagens virtual. Como posso ajudar você hoje?");
            } else {
                alert('Erro ao fazer logout');
            }
        })
        .catch(error => {
            console.error('Erro no logout:', error);
            alert('Erro ao fazer logout. Tente novamente.');
        });
}

// Monitoramento de preços
function initPriceMonitoring() {
    // Carregar ofertas monitoradas e alertas de preço ao iniciar a aplicação
    loadMonitoredOffers();

    // Verificar preços periodicamente (a cada 60 segundos)
    setInterval(checkPrices, 60000);
}

function loadMonitoredOffers() {
    fetch('/api/price-monitor')
        .then(response => {
            if (response.status === 401) {
                console.log('Usuário não está logado.');
                return { flights: [], hotels: [], alerts: [] };
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`Carregados: ${data.flights.length + data.hotels.length} ofertas e ${data.alerts.length} alertas`);

            // Aqui poderia atualizar uma UI para monitoramento de preços
            // Por exemplo, mostrar um contador de alertas no header

            // Verificar se há alertas não lidos
            const unreadAlerts = data.alerts.filter(alert => !alert.read);
            if (unreadAlerts.length > 0) {
                // Mostrar indicador de alertas
                const headerActions = document.querySelector('.header-actions');
                if (headerActions) {
                    const alertIndicator = document.createElement('div');
                    alertIndicator.className = 'alert-indicator';
                    alertIndicator.innerHTML = `
                        <i class="fas fa-bell"></i>
                        <span class="alert-count">${unreadAlerts.length}</span>
                    `;
                    alertIndicator.addEventListener('click', showPriceAlerts);

                    // Adicionar ao header se ainda não existir
                    if (!document.querySelector('.alert-indicator')) {
                        headerActions.prepend(alertIndicator);
                    } else {
                        document.querySelector('.alert-count').textContent = unreadAlerts.length;
                    }
                }
            }
        })
        .catch(error => {
            console.log('Usuário não está logado:', error);
        });
}

function checkPrices() {
    console.log('Verificando preços para ofertas monitoradas');
    fetch('/api/price-monitor/check', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.status === 401) {
            return { flights: { checked: 0 }, hotels: { checked: 0 }, alerts: [] };
        }
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Se novos alertas foram gerados, atualizar o indicador
        if (data.alerts && data.alerts.length > 0) {
            // Recarregar ofertas monitoradas para atualizar a UI
            loadMonitoredOffers();

            // Opcional: Mostrar notificação para o usuário
            const alertsText = data.alerts.length === 1 ? 
                'Um alerta de preço foi gerado!' :
                `${data.alerts.length} alertas de preço foram gerados!`;

            // Adicionar como mensagem do assistente se estiver em uma conversa ativa
            if (currentConversationId) {
                addAssistantMessage(`
                    <div class="price-alert-notification">
                        <i class="fas fa-bell"></i>
                        <p>${alertsText}</p>
                        <button class="btn btn-sm" onclick="showPriceAlerts()">Ver Alertas</button>
                    </div>
                `);
            }
        }
    })
    .catch(error => {
        // Ignorar erros de autenticação
        if (!error.message.includes('401')) {
            console.error('Erro ao verificar preços:', error);
        }
    });
}

function addToMonitor(type, offerData) {
    fetch('/api/price-monitor', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: type,
            data: offerData
        })
    })
    .then(response => {
        if (response.status === 401) {
            alert('Você precisa estar logado para monitorar preços. Por favor, faça login.');
            document.getElementById('login-modal').style.display = 'flex';
            return null;
        }
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            // Mostrar confirmação
            alert('Oferta adicionada ao monitoramento de preços com sucesso!');

            // Adicionar como mensagem do assistente
            const typeText = type === 'flight' ? 'voo' : 'hotel';
            addAssistantMessage(`
                <div class="monitor-confirmation">
                    <i class="fas fa-check-circle"></i>
                    <p>Este ${typeText} foi adicionado ao monitoramento de preços. Você será notificado se o preço diminuir!</p>
                </div>
            `);
        }
    })
    .catch(error => {
        console.error('Erro ao adicionar ao monitoramento:', error);
        alert('Não foi possível adicionar ao monitoramento. Tente novamente mais tarde.');
    });
}

function showPriceAlerts() {
    // Implementação para mostrar um modal ou página com alertas de preço
    alert('Funcionalidade de alertas de preço em desenvolvimento!');
}

// Funções para reserva e compra
function bookFlight(flightId) {
    // Aqui você implementaria a compra direta, sem redirecionar
    // Adicionando feedback de confirmação na interface

    // Adicionar mensagem de confirmação
    addAssistantMessage(`
        <div class="booking-confirmation">
            <i class="fas fa-check-circle"></i>
            <h4>Passagem Comprada com Sucesso!</h4>
            <p>Sua compra foi processada e confirmada. Os detalhes foram enviados para seu email.</p>
            <p>Localizador: <strong>FL${Math.floor(Math.random() * 100000)}</strong></p>

            <div class="booking-details">
                <div class="booking-detail-item">
                    <i class="fas fa-plane-departure"></i>
                    <span>Embarque: Aeroporto Internacional de Guarulhos (GRU), Terminal 3</span>
                </div>
                <div class="booking-detail-item">
                    <i class="fas fa-calendar-alt"></i>
                    <span>Data/Hora: 01/06/2024 às 08:20</span>
                </div>
                <div class="booking-detail-item">
                    <i class="fas fa-user"></i>
                    <span>Passageiro: ${document.getElementById('profile-name').value || 'Usuário'}</span>
                </div>
                <div class="booking-detail-item">
                    <i class="fas fa-money-bill-wave"></i>
                    <span>Valor pago: R$ 2.450,00 (10x de R$ 245,00 sem juros)</span>
                </div>
            </div>

            <div class="booking-actions">
                <button class="btn btn-primary" onclick="downloadTicket('${flightId}')">
                    <i class="fas fa-file-pdf"></i> Baixar bilhete
                </button>
                <button class="btn btn-outline" onclick="addToCalendar('${flightId}')">
                    <i class="fas fa-calendar-plus"></i> Adicionar ao calendário
                </button>
            </div>
        </div>
    `);
}

function bookHotel(hotelId) {
    // Implementação similar para reservas de hotel
    addAssistantMessage(`
        <div class="booking-confirmation">
            <i class="fas fa-check-circle"></i>
            <h4>Reserva de Hotel Confirmada!</h4>
            <p>Sua reserva foi processada com sucesso. A confirmação foi enviada para seu email.</p>
            <p>Número da reserva: <strong>HT${Math.floor(Math.random() * 100000)}</strong></p>

            <div class="booking-details">
                <div class="booking-detail-item">
                    <i class="fas fa-hotel"></i>
                    <span>Hotel: Alvear Palace</span>
                </div>
                <div class="booking-detail-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>Endereço: Av. Alvear 1891, Recoleta, Buenos Aires</span>
                </div>
                <div class="booking-detail-item">
                    <i class="fas fa-calendar-check"></i>
                    <span>Check-in: 01/06/2024 a partir das 14:00</span>
                </div>
                <div class="booking-detail-item">
                    <i class="fas fa-calendar-times"></i>
                    <span>Check-out: 08/06/2024 até às 12:00</span>
                </div>
                <div class="booking-detail-item">
                    <i class="fas fa-money-bill-wave"></i>
                    <span>Valor total: R$ 8.750,00 (7 noites)</span>
                </div>
            </div>

            <div class="booking-actions">
                <button class="btn btn-primary" onclick="downloadReservation('${hotelId}')">
                    <i class="fas fa-file-pdf"></i> Baixar voucher
                </button>
                <button class="btn btn-outline" onclick="viewOnMap('${hotelId}')">
                    <i class="fas fa-map-marked-alt"></i> Ver no mapa
                </button>
            </div>
        </div>
    `);
}

function downloadTicket(flightId) {
    // Simulação de download do bilhete
    alert(`Baixando bilhete para o voo ${flightId}. Em um sistema real, um PDF seria gerado.`);
}

function addToCalendar(flightId) {
    // Simulação de adição ao calendário
    alert(`Adicionando voo ${flightId} ao calendário. Em um sistema real, um arquivo .ics seria gerado.`);
}

function downloadReservation(hotelId) {
    // Simulação de download do voucher
    alert(`Baixando voucher para o hotel ${hotelId}. Em um sistema real, um PDF seria gerado.`);
}

function viewOnMap(hotelId) {
    // Simulação de visualização no mapa
    alert(`Abrindo localização do hotel ${hotelId} no mapa. Em um sistema real, um mapa seria exibido.`);
}

function downloadPlanPDF(planId) {
    window.open(`/api/plan/${planId}/pdf`, '_blank');
}

function sharePlan(planId) {
    // Implementar compartilhamento de plano
    alert(`Compartilhamento do plano ${planId} em desenvolvimento.`);
}

// Iniciar monitoramento de preços quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    initPriceMonitoring();
});
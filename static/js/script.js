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

    // State variables
    let isSidebarCollapsed = false;
    let currentConversationId = null;
    let activeSection = 'chat';
    let userLoggedIn = false;
    let userProfile = {};
    let conversations = [];
    let plans = [];
    let activePriceMonitorTab = 'flights';
    let monitoredOffers = [];

    // Toggle sidebar
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            isSidebarCollapsed = !isSidebarCollapsed;

            // Atualiza o ícone
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

    // Mostrar/esconder modais
    function showModal(modal) {
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    function hideModal(modal) {
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Listener para botões de login e signup
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

    // Fechar modal ao clicar fora
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            hideModal(event.target);
        }
    });

    // Navegação entre seções
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        item.addEventListener('click', function() {
            // Remover classe active de todos os itens
            document.querySelectorAll('.sidebar-nav-item').forEach(el => {
                el.classList.remove('active');
            });

            // Adicionar classe active ao item clicado
            this.classList.add('active');

            // Mostrar a seção correspondente
            const section = this.getAttribute('data-section');
            showSection(section);
        });
    });

    function showSection(sectionName) {
        // Esconder todas as seções
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Mostrar seção específica
        const sectionToShow = document.getElementById(`${sectionName}-section`);
        if (sectionToShow) {
            sectionToShow.classList.add('active');
            activeSection = sectionName;
        }

        // Para seções específicas, carregar dados
        if (sectionName === 'chat' && currentConversationId) {
            loadConversationMessages(currentConversationId);
        } else if (sectionName === 'plans') {
            loadPlans();
        } else if (sectionName === 'profile') {
            loadProfile();
        } else if (sectionName === 'price-monitor') {
            loadMonitoredOffers();
        }
    }

    // Funções para a funcionalidade de chat
    if (chatForm) {
        chatForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const message = messageInput.value.trim();

            if (message) {
                // Adicionar mensagem do usuário à interface
                addMessageToChat(message, true);

                // Limpar input
                messageInput.value = '';

                // Enviar mensagem para o servidor
                sendChatMessage(message);
            }
        });
    }

    function addMessageToChat(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');

        if (isUser) {
            messageDiv.classList.add('user');
        } else {
            messageDiv.classList.add('assistant');
        }

        const avatarDiv = document.createElement('div');
        avatarDiv.classList.add('message-avatar');

        // Ícone diferente para usuário e assistente
        const icon = document.createElement('i');
        if (isUser) {
            icon.classList.add('fas', 'fa-user');
        } else {
            icon.classList.add('fas', 'fa-robot');
        }

        avatarDiv.appendChild(icon);

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');

        const paragraph = document.createElement('p');
        paragraph.textContent = message;

        contentDiv.appendChild(paragraph);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        chatMessages.appendChild(messageDiv);

        // Scroll para a última mensagem
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function sendChatMessage(message) {
        // Preparar dados da requisição
        const data = {
            message: message
        };

        // Se já existe uma conversa, incluir o ID
        if (currentConversationId) {
            data.conversation_id = currentConversationId;
        }

        // Enviar requisição para o servidor
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Erro ao enviar mensagem:', data.error);
                addMessageToChat('Desculpe, ocorreu um erro ao processar sua mensagem.', false);
            } else {
                // Adicionar resposta do assistente
                addMessageToChat(data.response, false);

                // Atualizar ID da conversa atual
                if (data.conversation_id) {
                    currentConversationId = data.conversation_id;

                    // Recarregar lista de conversas
                    loadConversations();
                }
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
        .then(response => response.json())
        .then(data => {
            conversations = data;
            renderConversationsList();
        })
        .catch(error => {
            console.log('Error loading conversations:', error);
        });
    }

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
            const item = template.content.cloneNode(true);

            const itemDiv = item.querySelector('.sidebar-item');
            itemDiv.dataset.id = conversation.id;

            const title = itemDiv.querySelector('.sidebar-item-title');
            title.textContent = conversation.title;

            const subtitle = itemDiv.querySelector('.sidebar-item-subtitle');
            subtitle.textContent = `Atualizada em ${conversation.last_updated}`;

            // Marcar conversa ativa
            if (conversation.id === currentConversationId) {
                itemDiv.classList.add('active');
            }

            // Event listener para carregar conversa ao clicar
            itemDiv.addEventListener('click', function() {
                currentConversationId = conversation.id;
                loadConversationMessages(conversation.id);

                // Atualizar UI
                document.querySelectorAll('#conversations-list .sidebar-item').forEach(item => {
                    item.classList.remove('active');
                });
                this.classList.add('active');

                // Mostrar seção de chat
                showSection('chat');
            });

            conversationsList.appendChild(item);
        });
    }

    function loadConversationMessages(conversationId) {
        fetch(`/api/conversation/${conversationId}/messages`)
        .then(response => response.json())
        .then(data => {
            // Limpar mensagens atuais
            chatMessages.innerHTML = '';

            // Adicionar mensagens à interface
            data.forEach(msg => {
                addMessageToChat(msg.content, msg.is_user);
            });
        })
        .catch(error => {
            console.error('Erro ao carregar mensagens:', error);
        });
    }

    // Nova conversa
    if (newConversationButton) {
        newConversationButton.addEventListener('click', function() {
            // Limpar conversa atual
            currentConversationId = null;
            chatMessages.innerHTML = '';

            // Adicionar mensagem inicial do assistente
            addMessageToChat('Olá! Eu sou Flai, seu assistente de viagens virtual. Como posso ajudar você hoje?', false);

            // Mostrar seção de chat
            showSection('chat');
        });
    }

    // Funções para a página de perfil
    function loadProfile() {
        fetch('/api/profile')
        .then(response => response.json())
        .then(data => {
            userProfile = data;

            // Preencher o formulário
            if (profileForm) {
                profileForm.querySelector('#profile-name').value = data.name || '';
                profileForm.querySelector('#profile-email').value = data.email || '';
                profileForm.querySelector('#profile-phone').value = data.phone || '';

                if (data.preferences) {
                    profileForm.querySelector('#profile-preferred-destinations').value = data.preferences.preferred_destinations || '';

                    const accommodationType = profileForm.querySelector('#profile-accommodation-type');
                    if (accommodationType && data.preferences.accommodation_type) {
                        for (let i = 0; i < accommodationType.options.length; i++) {
                            if (accommodationType.options[i].value === data.preferences.accommodation_type) {
                                accommodationType.selectedIndex = i;
                                break;
                            }
                        }
                    }

                    const budget = profileForm.querySelector('#profile-budget');
                    if (budget && data.preferences.budget) {
                        for (let i = 0; i < budget.options.length; i++) {
                            if (budget.options[i].value === data.preferences.budget) {
                                budget.selectedIndex = i;
                                break;
                            }
                        }
                    }
                }
            }
        })
        .catch(error => {
            console.log('Error loading profile:', error);
        });
    }

    if (profileForm) {
        profileForm.addEventListener('submit', function(event) {
            event.preventDefault();

            // Coletar dados do formulário
            const formData = {
                name: profileForm.querySelector('#profile-name').value,
                email: profileForm.querySelector('#profile-email').value,
                phone: profileForm.querySelector('#profile-phone').value,
                preferences: {
                    preferred_destinations: profileForm.querySelector('#profile-preferred-destinations').value,
                    accommodation_type: profileForm.querySelector('#profile-accommodation-type').value,
                    budget: profileForm.querySelector('#profile-budget').value
                }
            };

            // Enviar para o servidor
            fetch('/api/profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Perfil atualizado com sucesso!');
                    userProfile = data.profile;
                } else {
                    alert('Erro ao atualizar perfil.');
                }
            })
            .catch(error => {
                console.error('Erro ao salvar perfil:', error);
                alert('Erro ao atualizar perfil.');
            });
        });
    }

    // Funções para planos de viagem
    function loadPlans() {
        fetch('/api/plans')
        .then(response => response.json())
        .then(data => {
            plans = data;
            renderPlansList();
        })
        .catch(error => {
            console.log('Error loading plans:', error);
        });
    }

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
            const item = template.content.cloneNode(true);

            const itemDiv = item.querySelector('.sidebar-item');
            itemDiv.dataset.id = plan.id;

            const title = itemDiv.querySelector('.sidebar-item-title');
            title.textContent = plan.title;

            const subtitle = itemDiv.querySelector('.sidebar-item-subtitle');
            subtitle.textContent = plan.destination;

            // Event listener para carregar plano ao clicar
            itemDiv.addEventListener('click', function() {
                loadPlanDetails(plan.id);

                // Atualizar UI
                document.querySelectorAll('#plans-list .sidebar-item').forEach(item => {
                    item.classList.remove('active');
                });
                this.classList.add('active');

                // Mostrar seção de planos
                showSection('plans');
            });

            plansList.appendChild(item);
        });
    }

    function loadPlanDetails(planId) {
        fetch(`/api/plan/${planId}`)
        .then(response => response.json())
        .then(plan => {
            const planDetails = document.getElementById('plan-details');
            if (!planDetails) return;

            // Construir a interface para o plano
            planDetails.innerHTML = `
                <div class="plan-header">
                    <h3>${plan.title}</h3>
                    <p class="plan-destination"><i class="fas fa-map-marker-alt"></i> ${plan.destination}</p>
                    <p class="plan-dates">
                        <i class="fas fa-calendar-alt"></i> 
                        ${plan.start_date ? plan.start_date : ''} 
                        ${plan.start_date && plan.end_date ? ' - ' : ''} 
                        ${plan.end_date ? plan.end_date : ''}
                    </p>
                </div>

                <div class="plan-content">
                    <div class="plan-details-section">
                        <h4>Detalhes</h4>
                        <p>${plan.details || 'Sem detalhes adicionais'}</p>
                    </div>

                    <div class="plan-flights-section">
                        <h4>Voos</h4>
                        ${renderFlightsList(plan.flights)}
                    </div>

                    <div class="plan-accommodations-section">
                        <h4>Hospedagem</h4>
                        ${renderAccommodationsList(plan.accommodations)}
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Erro ao carregar detalhes do plano:', error);
        });
    }

    function renderFlightsList(flights) {
        if (!flights || flights.length === 0) {
            return '<p class="empty-list-message">Nenhum voo adicionado a este plano</p>';
        }

        let html = '<div class="flights-list">';

        flights.forEach(flight => {
            html += `
                <div class="flight-item">
                    <div class="flight-header">
                        <span class="flight-airline">${flight.airline}</span>
                        <span class="flight-number">${flight.flight_number}</span>
                    </div>
                    <div class="flight-route">
                        <div class="flight-departure">
                            <p class="flight-location">${flight.departure_location}</p>
                            <p class="flight-time">${formatDateTime(flight.departure_time)}</p>
                        </div>
                        <div class="flight-arrow">
                            <i class="fas fa-plane"></i>
                        </div>
                        <div class="flight-arrival">
                            <p class="flight-location">${flight.arrival_location}</p>
                            <p class="flight-time">${formatDateTime(flight.arrival_time)}</p>
                        </div>
                    </div>
                    <div class="flight-price">
                        <p>${flight.price} ${flight.currency}</p>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    function renderAccommodationsList(accommodations) {
        if (!accommodations || accommodations.length === 0) {
            return '<p class="empty-list-message">Nenhuma hospedagem adicionada a este plano</p>';
        }

        let html = '<div class="accommodations-list">';

        accommodations.forEach(acc => {
            html += `
                <div class="accommodation-item">
                    <div class="accommodation-header">
                        <h5>${acc.name}</h5>
                        <div class="accommodation-stars">
                            ${renderStars(acc.stars)}
                        </div>
                    </div>
                    <p class="accommodation-location"><i class="fas fa-map-marker-alt"></i> ${acc.location}</p>
                    <p class="accommodation-dates">
                        <i class="fas fa-calendar-check"></i> Check-in: ${acc.check_in || 'Não definido'}<br>
                        <i class="fas fa-calendar-times"></i> Check-out: ${acc.check_out || 'Não definido'}
                    </p>
                    <p class="accommodation-price">
                        <i class="fas fa-tag"></i> ${acc.price_per_night} ${acc.currency} por noite
                    </p>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    function renderStars(stars) {
        let html = '';
        for (let i = 0; i < 5; i++) {
            if (i < stars) {
                html += '<i class="fas fa-star"></i>';
            } else {
                html += '<i class="far fa-star"></i>';
            }
        }
        return html;
    }

    function formatDateTime(dateTimeStr) {
        if (!dateTimeStr) return 'Não definido';

        const date = new Date(dateTimeStr);
        return date.toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Funções para monitoramento de preços
    function loadMonitoredOffers() {
        fetch('/api/price-monitor')
        .then(response => response.json())
        .then(data => {
            monitoredOffers = data;
            renderMonitoredOffers();
            console.log(`Carregados: ${data.flights.length + data.hotels.length} ofertas e ${data.alerts.length} alertas`);
        })
        .catch(error => {
            console.error('Erro ao carregar ofertas monitoradas:', error);
        });
    }

    function renderMonitoredOffers() {
        // Renderizar voos monitorados
        const flightsList = document.getElementById('flights-list');
        if (flightsList) {
            renderFlightsMonitor(flightsList, monitoredOffers.flights);
        }

        // Renderizar hotéis monitorados
        const hotelsList = document.getElementById('hotels-list');
        if (hotelsList) {
            renderHotelsMonitor(hotelsList, monitoredOffers.hotels);
        }

        // Renderizar alertas
        const alertsList = document.getElementById('alerts-list');
        if (alertsList) {
            renderAlerts(alertsList, monitoredOffers.alerts);
        }

        // Configurar tabs
        configurePriceMonitorTabs();
    }

    function renderFlightsMonitor(container, flights) {
        container.innerHTML = '';

        if (!flights || flights.length === 0) {
            container.innerHTML = '<p class="empty-list-message">Nenhum voo sendo monitorado</p>';
            return;
        }

        flights.forEach(flight => {
            const item = document.createElement('div');
            item.className = 'monitor-item';
            item.dataset.id = flight.id;

            // Calcular diferença de preço
            const priceDiff = flight.current_price - flight.original_price;
            const priceDiffPercentage = (priceDiff / flight.original_price) * 100;

            // Classe para indicar se o preço subiu ou desceu
            let priceChangeClass = 'price-same';
            if (priceDiff < 0) {
                priceChangeClass = 'price-down';
            } else if (priceDiff > 0) {
                priceChangeClass = 'price-up';
            }

            item.innerHTML = `
                <div class="monitor-item-header">
                    <h4 class="monitor-item-title">${flight.name}</h4>
                    <button class="btn btn-icon remove-monitor" data-id="${flight.id}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <p class="monitor-item-description">${flight.description}</p>
                <div class="price-info">
                    <div class="current-price ${priceChangeClass}">
                        <span class="price-label">Preço atual:</span>
                        <span class="price-value">${flight.current_price.toFixed(2)} ${flight.currency}</span>
                    </div>
                    <div class="price-change ${priceChangeClass}">
                        ${priceDiff !== 0 ? 
                            `<span class="price-diff">
                                ${priceDiff > 0 ? '+' : ''}${priceDiff.toFixed(2)} ${flight.currency} 
                                (${priceDiff > 0 ? '+' : ''}${priceDiffPercentage.toFixed(1)}%)
                            </span>` : 
                            '<span class="price-diff">Sem alteração</span>'
                        }
                    </div>
                </div>
                <p class="lowest-price">
                    <span class="price-label">Menor preço registrado:</span>
                    <span class="price-value">${flight.lowest_price.toFixed(2)} ${flight.currency}</span>
                </p>
                <p class="monitor-date">
                    <span>Monitorando desde: ${new Date(flight.date_added).toLocaleDateString('pt-BR')}</span>
                </p>
                <div class="price-chart" data-id="${flight.id}">
                    <!-- Gráfico será renderizado aqui -->
                </div>
            `;

            container.appendChild(item);

            // Adicionar event listener para remover do monitoramento
            item.querySelector('.remove-monitor').addEventListener('click', function(e) {
                e.stopPropagation();
                const id = this.dataset.id;
                if (confirm('Tem certeza que deseja remover este voo do monitoramento?')) {
                    removeFromMonitor(id);
                }
            });

            // Renderizar o gráfico de preços se tiver histórico
            if (flight.price_history && flight.price_history.length > 1) {
                renderPriceChart(item.querySelector('.price-chart'), flight.price_history);
            } else {
                item.querySelector('.price-chart').innerHTML = '<p class="chart-placeholder">Histórico insuficiente para gerar gráfico</p>';
            }
        });
    }

    function renderHotelsMonitor(container, hotels) {
        container.innerHTML = '';

        if (!hotels || hotels.length === 0) {
            container.innerHTML = '<p class="empty-list-message">Nenhum hotel sendo monitorado</p>';
            return;
        }

        hotels.forEach(hotel => {
            const item = document.createElement('div');
            item.className = 'monitor-item';
            item.dataset.id = hotel.id;

            // Calcular diferença de preço
            const priceDiff = hotel.current_price - hotel.original_price;
            const priceDiffPercentage = (priceDiff / hotel.original_price) * 100;

            // Classe para indicar se o preço subiu ou desceu
            let priceChangeClass = 'price-same';
            if (priceDiff < 0) {
                priceChangeClass = 'price-down';
            } else if (priceDiff > 0) {
                priceChangeClass = 'price-up';
            }

            item.innerHTML = `
                <div class="monitor-item-header">
                    <h4 class="monitor-item-title">${hotel.name}</h4>
                    <button class="btn btn-icon remove-monitor" data-id="${hotel.id}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <p class="monitor-item-description">${hotel.description}</p>
                <div class="price-info">
                    <div class="current-price ${priceChangeClass}">
                        <span class="price-label">Preço atual:</span>
                        <span class="price-value">${hotel.current_price.toFixed(2)} ${hotel.currency}</span>
                    </div>
                    <div class="price-change ${priceChangeClass}">
                        ${priceDiff !== 0 ? 
                            `<span class="price-diff">
                                ${priceDiff > 0 ? '+' : ''}${priceDiff.toFixed(2)} ${hotel.currency} 
                                (${priceDiff > 0 ? '+' : ''}${priceDiffPercentage.toFixed(1)}%)
                            </span>` : 
                            '<span class="price-diff">Sem alteração</span>'
                        }
                    </div>
                </div>
                <p class="lowest-price">
                    <span class="price-label">Menor preço registrado:</span>
                    <span class="price-value">${hotel.lowest_price.toFixed(2)} ${hotel.currency}</span>
                </p>
                <p class="monitor-date">
                    <span>Monitorando desde: ${new Date(hotel.date_added).toLocaleDateString('pt-BR')}</span>
                </p>
                <div class="price-chart" data-id="${hotel.id}">
                    <!-- Gráfico será renderizado aqui -->
                </div>
            `;

            container.appendChild(item);

            // Adicionar event listener para remover do monitoramento
            item.querySelector('.remove-monitor').addEventListener('click', function(e) {
                e.stopPropagation();
                const id = this.dataset.id;
                if (confirm('Tem certeza que deseja remover este hotel do monitoramento?')) {
                    removeFromMonitor(id);
                }
            });

            // Renderizar o gráfico de preços se tiver histórico
            if (hotel.price_history && hotel.price_history.length > 1) {
                renderPriceChart(item.querySelector('.price-chart'), hotel.price_history);
            } else {
                item.querySelector('.price-chart').innerHTML = '<p class="chart-placeholder">Histórico insuficiente para gerar gráfico</p>';
            }
        });
    }

    function renderAlerts(container, alerts) {
        container.innerHTML = '';

        if (!alerts || alerts.length === 0) {
            container.innerHTML = '<p class="empty-list-message">Nenhum alerta de preço disponível</p>';
            return;
        }

        // Botão para marcar todos como lidos
        const markAllReadBtn = document.createElement('button');
        markAllReadBtn.className = 'btn btn-primary mark-all-read';
        markAllReadBtn.innerHTML = '<i class="fas fa-check-double"></i> Marcar todos como lidos';
        markAllReadBtn.addEventListener('click', function() {
            markAlertsAsRead();
        });

        container.appendChild(markAllReadBtn);

        // Renderizar cada alerta
        alerts.forEach(alert => {
            const item = document.createElement('div');
            item.className = 'alert-item';
            if (!alert.read) {
                item.classList.add('unread');
            }

            const priceDiff = alert.new_price - alert.old_price;
            const priceDiffPercentage = (priceDiff / alert.old_price) * 100;

            item.innerHTML = `
                <div class="alert-header">
                    <h4 class="alert-title">${alert.name}</h4>
                    <span class="alert-date">${new Date(alert.date).toLocaleDateString('pt-BR')}</span>
                </div>
                <p class="alert-description">${alert.description}</p>
                <div class="alert-price-info">
                    <p class="old-price">
                        <span class="price-label">Preço anterior:</span>
                        <span class="price-value">${alert.old_price.toFixed(2)} ${alert.currency}</span>
                    </p>
                    <p class="new-price price-down">
                        <span class="price-label">Novo preço:</span>
                        <span class="price-value">${alert.new_price.toFixed(2)} ${alert.currency}</span>
                    </p>
                    <p class="price-diff price-down">
                        <span class="diff-value">${priceDiff.toFixed(2)} ${alert.currency} (${priceDiffPercentage.toFixed(1)}%)</span>
                    </p>
                </div>
                <div class="alert-actions">
                    <button class="btn btn-primary view-monitor" data-id="${alert.monitor_id}">
                        <i class="fas fa-eye"></i> Ver detalhes
                    </button>
                    <button class="btn btn-outline mark-read" data-id="${alert.id}" ${alert.read ? 'disabled' : ''}>
                        <i class="fas fa-check"></i> ${alert.read ? 'Lido' : 'Marcar como lido'}
                    </button>
                </div>
            `;

            container.appendChild(item);

            // Event listener para marcar como lido
            item.querySelector('.mark-read').addEventListener('click', function() {
                const alertId = this.dataset.id;
                markAlertsAsRead([alertId]);
                item.classList.remove('unread');
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-check"></i> Lido';
            });

            // Event listener para ver os detalhes do item monitorado
            item.querySelector('.view-monitor').addEventListener('click', function() {
                const monitorId = this.dataset.id;
                // Determinar se é voo ou hotel
                let type = alert.type === 'flight' ? 'flights' : 'hotels';

                // Mudar para a tab correspondente
                document.querySelector(`.tab[data-tab="${type}"]`).click();

                // Destacar o item
                const monitorItem = document.querySelector(`.monitor-item[data-id="${monitorId}"]`);
                if (monitorItem) {
                    monitorItem.scrollIntoView({ behavior: 'smooth' });
                    monitorItem.classList.add('highlight');
                    setTimeout(() => {
                        monitorItem.classList.remove('highlight');
                    }, 2000);
                }
            });
        });
    }

    function configurePriceMonitorTabs() {
        document.querySelectorAll('.price-monitor-tabs .tab').forEach(tab => {
            tab.addEventListener('click', function() {
                // Remover classe active de todas as tabs
                document.querySelectorAll('.price-monitor-tabs .tab').forEach(t => {
                    t.classList.remove('active');
                });

                // Adicionar classe active na tab clicada
                this.classList.add('active');

                // Esconder todos os conteúdos
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });

                // Mostrar o conteúdo correspondente
                const tabId = this.dataset.tab;
                document.getElementById(`${tabId}-tab`).classList.add('active');

                // Atualizar a tab ativa
                activePriceMonitorTab = tabId;
            });
        });
    }

    function renderPriceChart(container, priceHistory) {
        // Implementação básica para simular um gráfico 
        // Em um cenário real, usaríamos uma biblioteca como Chart.js

        container.innerHTML = '<div class="simple-chart"></div>';
        const chart = container.querySelector('.simple-chart');

        const prices = priceHistory.map(entry => entry.price);
        const dates = priceHistory.map(entry => new Date(entry.date).toLocaleDateString('pt-BR')););

        // Encontrar preço mín e máx para a escala
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const range = maxPrice - minPrice;

        // Criar barras para representar preços
        let chartHTML = '';
        prices.forEach((price, index) => {
            // Calcular altura relativa
            const height = range > 0 ? ((price - minPrice) / range) * 100 : 50;

            // Determinar cor com base na variação do preço
            let color = '#999'; // Cinza para neutro

            if (index > 0) {
                if (price < prices[index - 1]) {
                    color = '#4CAF50'; // Verde para queda
                } else if (price > prices[index - 1]) {
                    color = '#F44336'; // Vermelho para aumento
                }
            }

            chartHTML += `
                <div class="chart-bar" style="height: ${height}%" title="${price.toFixed(2)} em ${dates[index]}">
                    <div class="bar" style="background-color: ${color}"></div>
                </div>
            `;
        });

        chart.innerHTML = chartHTML;
    }

    function removeFromMonitor(monitorId) {
        fetch(`/api/price-monitor/${monitorId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Atualizar a interface removendo o item
                const item = document.querySelector(`.monitor-item[data-id="${monitorId}"]`);
                if (item) {
                    item.remove();
                }

                // Recarregar dados
                loadMonitoredOffers();
            } else {
                alert(`Erro ao remover oferta: ${data.error || 'Erro desconhecido'}`);
            }
        })
        .catch(error => {
            console.error('Erro ao remover oferta do monitoramento:', error);
            alert('Erro ao remover oferta do monitoramento.');
        });
    }

    function markAlertsAsRead(alertIds = []) {
        fetch('/api/price-alerts/mark-read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ alert_ids: alertIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Se nenhum ID específico, todos foram marcados como lidos
                if (alertIds.length === 0) {
                    document.querySelectorAll('.alert-item').forEach(item => {
                        item.classList.remove('unread');
                        const btn = item.querySelector('.mark-read');
                        if (btn) {
                            btn.disabled = true;
                            btn.innerHTML = '<i class="fas fa-check"></i> Lido';
                        }
                    });
                }

                // Recarregar dados
                loadMonitoredOffers();
            } else {
                alert(`Erro ao marcar alertas como lidos: ${data.error || 'Erro desconhecido'}`);
            }
        })
        .catch(error => {
            console.error('Erro ao marcar alertas como lidos:', error);
            alert('Erro ao marcar alertas como lidos.');
        });
    }

    // Verificar preços regularmente (a cada 5 minutos)
    function checkPrices() {
        fetch('/api/price-monitor/check', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Verificando preços para', data.flights.checked + data.hotels.checked, 'ofertas monitoradas');

            // Se houver novos alertas, recarregar dados
            if (data.alerts && data.alerts.length > 0) {
                loadMonitoredOffers();

                // Notificar o usuário
                alert(`Atenção: ${data.alerts.length} nova(s) queda(s) de preço detectada(s)!`);
            }
        })
        .catch(error => {
            console.error('Erro ao verificar preços:', error);
        });
    }

    // Inicialização
    function init() {
        // Verificar se o usuário está logado
        fetch('/api/profile')
        .then(response => {
            if (response.ok) {
                userLoggedIn = true;

                // Carregar dados
                loadConversations();
                loadProfile();
                loadPlans();
                loadMonitoredOffers();

                // Verificar preços a cada 5 minutos
                setInterval(checkPrices, 300000);

                // Executar uma verificação inicial após 10 segundos
                setTimeout(checkPrices, 10000);
            }
        })
        .catch(error => {
            console.log('Usuário não está logado:', error);
        });
    }

    // Message input auto-resize
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // Handle Enter key to submit form
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
            // Shift+Enter will add a normal line break
        });
    }

    // Inicializar a aplicação
    init();
});
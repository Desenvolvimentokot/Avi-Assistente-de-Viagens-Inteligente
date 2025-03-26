/**
 * Flai - Travel Planning Assistant
 * Main JavaScript file
 */

// DOM elements
const sidebar = document.getElementById('sidebar');
const content = document.getElementById('content');
const conversationsList = document.getElementById('conversations-list');
const plansList = document.getElementById('plans-list');
const conversationsSection = document.getElementById('conversations-section');
const plansSection = document.getElementById('plans-section');
const profileSection = document.getElementById('profile-section');
const chatInput = document.getElementById('chat-input');
let chatForm = document.getElementById('chat-form');
let chatMessages = document.getElementById('chat-messages');
const profileForm = document.getElementById('profile-form');
const sidebarToggle = document.getElementById('sidebar-toggle');
const fullscreenToggle = document.getElementById('fullscreen-toggle');

// State management
let activeSection = 'conversations';
let conversations = [];
let plans = [];
let userProfile = {};
let activePlanId = null;
let chatHistory = [];
let isSidebarCollapsed = false;
let isFullscreenChat = false;

// Sistema de monitoramento de preços
let monitoredOffers = []; // Armazena as ofertas monitoradas
let priceAlerts = []; // Armazena alertas de queda de preço

// Load initial data
document.addEventListener('DOMContentLoaded', () => {
    loadConversations();
    loadPlans();
    loadProfile();
    
    // Carregar dados do monitoramento de preços (localStorage)
    loadPriceMonitoringData();
    
    // Configurar verificação periódica de preços (a cada 5 minutos)
    // Em uma implementação real, isso poderia ser feito no servidor
    const PRICE_CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutos em milissegundos
    setInterval(checkPrices, PRICE_CHECK_INTERVAL);
    
    // Verificar preços imediatamente para inicializar o sistema
    // Isso é útil para demonstração/teste rápido
    setTimeout(checkPrices, 10000); // Verifica após 10 segundos para dar tempo de visualizar
    
    // Show conversations section by default
    showSection('conversations');
    
    // Add event listeners
    chatForm.addEventListener('submit', handleChatSubmit);
    profileForm.addEventListener('submit', handleProfileSubmit);
    
    // Add event listeners to sidebar links
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const section = e.currentTarget.dataset.section;
            
            // Se for a seção de conversas, apenas mostrar a interface sem reiniciar o chat
            if (section === 'conversations' && activeSection === 'conversations') {
                return; // Não faz nada se já estiver na seção de conversas
            }
            
            showSection(section);
        });
    });
    
    // Add event listeners to header navigation items
    document.querySelectorAll('.header-nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const icon = e.currentTarget.querySelector('i');
            
            if (icon.classList.contains('fa-bell')) {
                toggleNotifications();
            } else if (icon.classList.contains('fa-user-circle')) {
                showSection('profile');
            }
        });
    });
    
    // Add event listener for sidebar toggle
    sidebarToggle.addEventListener('click', toggleSidebar);
    
    // Add event listener for fullscreen toggle (will be re-attached when chat loads)
    if (fullscreenToggle) {
        fullscreenToggle.addEventListener('click', toggleFullscreenChat);
    }
});

// Function to load conversations from API
function loadConversations() {
    fetch('/api/conversations')
        .then(response => response.json())
        .then(data => {
            conversations = data;
            renderConversations();
        })
        .catch(error => {
            console.error('Error loading conversations:', error);
        });
}

// Function to load travel plans from API
function loadPlans() {
    fetch('/api/plans')
        .then(response => response.json())
        .then(data => {
            plans = data;
            renderPlans();
        })
        .catch(error => {
            console.error('Error loading plans:', error);
        });
}

// Function to load user profile from API
function loadProfile() {
    fetch('/api/profile')
        .then(response => response.json())
        .then(data => {
            userProfile = data;
            renderProfile();
        })
        .catch(error => {
            console.error('Error loading profile:', error);
        });
}

// Function to render conversations list
function renderConversations() {
    conversationsList.innerHTML = '';
    
    conversations.forEach(conversation => {
        const item = document.createElement('li');
        item.className = 'sidebar-list-item';
        item.dataset.id = conversation.id;
        item.innerHTML = `
            <div class="sidebar-list-item-title">${conversation.title}</div>
            <div class="sidebar-list-item-info">Atualizado: ${conversation.last_updated}</div>
        `;
        
        item.addEventListener('click', () => {
            // Carrega a conversa existente em vez de começar uma nova
            fetch(`/api/conversation/${conversation.id}/messages`)
                .then(response => response.json())
                .then(data => {
                    chatHistory = data;
                    renderChatMessages();
                    showSection('conversations');
                })
                .catch(error => {
                    console.error('Erro ao carregar mensagens da conversa:', error);
                });
        });
        
        conversationsList.appendChild(item);
    });
}

// Function to render travel plans list
function renderPlans() {
    plansList.innerHTML = '';
    
    plans.forEach(plan => {
        const item = document.createElement('li');
        item.className = 'sidebar-list-item';
        item.dataset.id = plan.id;
        item.innerHTML = `
            <div class="sidebar-list-item-title">${plan.title}</div>
            <div class="sidebar-list-item-info">${plan.destination} (${plan.start_date} - ${plan.end_date})</div>
        `;
        
        item.addEventListener('click', () => {
            activePlanId = plan.id;
            loadPlanDetails(plan.id);
            showSection('plans');
        });
        
        plansList.appendChild(item);
    });
}

// Function to load and display plan details
function loadPlanDetails(planId) {
    fetch(`/api/plan/${planId}`)
        .then(response => response.json())
        .then(plan => {
            renderPlanDetails(plan);
        })
        .catch(error => {
            console.error('Error loading plan details:', error);
        });
}

// Function to render plan details
function renderPlanDetails(plan) {
    // Mock flight and hotel data that would come from Amadeus API
    const mockFlights = [
        {
            airline: "LATAM",
            flight_number: "LA3456",
            departure: "São Paulo (GRU)",
            arrival: plan.destination.split(',')[0],
            departure_time: "08:30",
            arrival_time: "20:15",
            price: "R$2.450"
        },
        {
            airline: "Gol",
            flight_number: "G35678",
            departure: "São Paulo (GRU)",
            arrival: plan.destination.split(',')[0],
            departure_time: "18:00",
            arrival_time: "07:45 (+1)",
            price: "R$2.820"
        }
    ];
    
    const mockHotels = [
        {
            name: `Grande Hotel ${plan.destination.split(',')[0]}`,
            stars: 4,
            location: `${plan.destination.split(',')[0]} Central`,
            price_per_night: "R$980",
            available: true
        },
        {
            name: `${plan.destination.split(',')[0]} Vista Resort`,
            stars: 3,
            location: `Centro de ${plan.destination.split(',')[0]}`,
            price_per_night: "R$740",
            available: true
        }
    ];
    
    // Update main content with plan details
    content.innerHTML = `
        <div class="content-section">
            <h2 class="content-title">Detalhes do Plano de Viagem</h2>
            <div class="plan-details">
                <div class="plan-header">
                    <h3 class="plan-title">${plan.title}</h3>
                    <div class="plan-dates">${plan.start_date} - ${plan.end_date}</div>
                    <div class="plan-destination">${plan.destination}</div>
                </div>
                
                <div class="plan-section">
                    <h4 class="plan-section-title">Detalhes da Viagem</h4>
                    <p>${plan.details}</p>
                </div>
                
                <div class="plan-section">
                    <h4 class="plan-section-title">Voos</h4>
                    <div class="plan-flight-cards">
                        ${mockFlights.map(flight => `
                            <div class="plan-card">
                                <div class="plan-card-title">${flight.airline} - ${flight.flight_number}</div>
                                <div class="plan-card-info">${flight.departure} → ${flight.arrival}</div>
                                <div class="plan-card-info">Partida: ${flight.departure_time} | Chegada: ${flight.arrival_time}</div>
                                <div class="plan-card-price">${flight.price}</div>
                            </div>
                        `).join('')}
                        <p class="plan-section-note">Obs: Dados de voos virão da API Amadeus na versão em produção</p>
                    </div>
                </div>
                
                <div class="plan-section">
                    <h4 class="plan-section-title">Hospedagem</h4>
                    <div class="plan-hotel-cards">
                        ${mockHotels.map(hotel => `
                            <div class="plan-card">
                                <div class="plan-card-title">${hotel.name} (${hotel.stars}★)</div>
                                <div class="plan-card-info">${hotel.location}</div>
                                <div class="plan-card-price">${hotel.price_per_night} por noite</div>
                            </div>
                        `).join('')}
                        <p class="plan-section-note">Obs: Dados de hotéis virão da API Amadeus na versão em produção</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Function to render user profile
function renderProfile() {
    // Populate profile form with user data
    document.getElementById('profile-name').value = userProfile.name || '';
    document.getElementById('profile-email').value = userProfile.email || '';
    document.getElementById('profile-phone').value = userProfile.phone || '';
    document.getElementById('profile-preferred-destinations').value = userProfile.preferences?.preferred_destinations || '';
    document.getElementById('profile-accommodation-type').value = userProfile.preferences?.accommodation_type || '';
    document.getElementById('profile-budget').value = userProfile.preferences?.budget || '';
    
    console.log('Profile rendered:', userProfile);
}

// Function to handle chat form submission
function handleChatSubmit(e) {
    e.preventDefault();
    
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input
    messageInput.value = '';
    
    // Show loading indicator
    const loadingMsg = addMessageToChat('assistant', '<div class="loading"></div>');
    
    // Call API to get response (simulating GPT API call)
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message
        loadingMsg.remove();
        
        // Add assistant response
        addMessageToChat('assistant', data.response);
        
        // Check if response mentions flights or hotels (in Portuguese)
        if (message.toLowerCase().includes('voo') || 
            message.toLowerCase().includes('passagem') || 
            message.toLowerCase().includes('hotel') ||
            message.toLowerCase().includes('hospedagem')) {
            // Simulate Amadeus API call
            const searchType = (message.toLowerCase().includes('voo') || message.toLowerCase().includes('passagem')) ? 'flights' : 'hotels';
            
            fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ type: searchType })
            })
            .then(response => response.json())
            .then(searchData => {
                // Format and display search results
                let resultsHtml = '<div class="search-results">';
                
                if (searchType === 'flights') {
                    resultsHtml += '<h4>Opções de Voos:</h4>';
                    searchData.results.forEach(flight => {
                        // Converter preço para formato numérico para monitoramento (removendo R$ e vírgula)
                        const numericPrice = parseFloat(flight.price.replace('R$', '').replace('.', '').replace(',', '.'));
                        
                        resultsHtml += `
                            <div class="plan-card">
                                <div class="plan-card-title">${flight.airline} - ${flight.flight_number}</div>
                                <div class="plan-card-info">${flight.departure} → ${flight.arrival}</div>
                                <div class="plan-card-info">Partida: ${flight.departure_time} | Chegada: ${flight.arrival_time}</div>
                                <div class="plan-card-price-container">
                                    <div class="plan-card-price">${flight.price}</div>
                                    <button class="monitor-price-btn" data-type="flight" 
                                        data-id="${flight.flight_number}"
                                        data-name="${flight.airline} - ${flight.flight_number}"
                                        data-destination="${flight.arrival}"
                                        data-price="${numericPrice}"
                                        data-formatted-price="${flight.price}"
                                        data-details='${JSON.stringify({
                                            departure: flight.departure,
                                            departure_time: flight.departure_time,
                                            arrival_time: flight.arrival_time
                                        })}'>
                                        <i class="fas fa-bell"></i> Monitorar Preço
                                    </button>
                                </div>
                            </div>
                        `;
                    });
                } else {
                    resultsHtml += '<h4>Opções de Hotéis:</h4>';
                    searchData.results.forEach(hotel => {
                        // Converter preço para formato numérico para monitoramento (removendo R$ e vírgula)
                        const numericPrice = parseFloat(hotel.price_per_night.replace('R$', '').replace('.', '').replace(',', '.'));
                        
                        resultsHtml += `
                            <div class="plan-card">
                                <div class="plan-card-title">${hotel.name} (${hotel.stars}★)</div>
                                <div class="plan-card-info">${hotel.location}</div>
                                <div class="plan-card-price-container">
                                    <div class="plan-card-price">${hotel.price_per_night} por noite</div>
                                    <button class="monitor-price-btn" data-type="hotel" 
                                        data-id="${hotel.name.replace(/\s+/g, '-')}"
                                        data-name="${hotel.name}"
                                        data-destination="${hotel.location}"
                                        data-price="${numericPrice}"
                                        data-formatted-price="${hotel.price_per_night}"
                                        data-details='${JSON.stringify({
                                            stars: hotel.stars,
                                            available: hotel.available
                                        })}'>
                                        <i class="fas fa-bell"></i> Monitorar Preço
                                    </button>
                                </div>
                            </div>
                        `;
                    });
                }
                
                resultsHtml += '</div>';
                const messageElement = addMessageToChat('assistant', resultsHtml);
                
                // Adicionar event listeners aos botões de monitoramento de preço
                setTimeout(() => {
                    const monitorButtons = messageElement.querySelectorAll('.monitor-price-btn');
                    monitorButtons.forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            e.preventDefault();
                            
                            // Extrair dados do botão
                            const type = btn.dataset.type;
                            const id = btn.dataset.id;
                            const name = btn.dataset.name;
                            const destination = btn.dataset.destination;
                            const price = parseFloat(btn.dataset.price);
                            const formattedPrice = btn.dataset.formattedPrice;
                            const details = JSON.parse(btn.dataset.details);
                            
                            // Criar objeto para monitoramento
                            const offer = {
                                type,
                                id,
                                name,
                                destination,
                                price,
                                formattedPrice,
                                details
                            };
                            
                            // Adicionar ao monitoramento
                            addPriceMonitor(offer);
                            
                            // Feedback visual ao usuário
                            btn.innerHTML = '<i class="fas fa-check"></i> Monitorando';
                            btn.classList.add('monitoring');
                            btn.disabled = true;
                            
                            // Adicionar mensagem de confirmação no chat
                            const monitoringMessage = type === 'flight' 
                                ? `Estou monitorando o preço do voo ${name} para ${destination}. Você receberá uma notificação quando o preço cair.`
                                : `Estou monitorando o preço do hotel ${name} em ${destination}. Você receberá uma notificação quando o preço cair.`;
                            
                            addMessageToChat('assistant', monitoringMessage);
                        });
                    });
                }, 100); // Pequeno atraso para garantir que o DOM foi atualizado
            })
            .catch(error => {
                console.error('Error searching:', error);
            });
        }
    })
    .catch(error => {
        console.error('Error getting chat response:', error);
        // Remove loading message
        loadingMsg.remove();
        // Add error message
        addMessageToChat('assistant', 'Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.');
    });
}

// Function to add a message to the chat
function addMessageToChat(sender, content) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? 'U' : 'F';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = content;
    
    messageElement.appendChild(avatar);
    messageElement.appendChild(messageContent);
    
    chatMessages.appendChild(messageElement);
    
    // Auto scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Save to chat history
    chatHistory.push({
        sender,
        content
    });
    
    return messageElement;
}

// Function to render chat messages from history
function renderChatMessages() {
    chatMessages.innerHTML = '';
    
    if (chatHistory.length === 0) {
        // Add welcome message
        addMessageToChat('assistant', 'Olá! Eu sou o Flai, seu assistente de planejamento de viagens. Conte-me sobre seus planos de viagem e eu vou ajudar a organizar a viagem perfeita. Para onde você gostaria de ir?');
    } else {
        // Add all messages from history
        chatHistory.forEach(msg => {
            addMessageToChat(msg.sender, msg.content);
        });
    }
}

// Function to handle profile form submission
function handleProfileSubmit(e) {
    e.preventDefault();
    
    const name = document.getElementById('profile-name').value.trim();
    const email = document.getElementById('profile-email').value.trim();
    const phone = document.getElementById('profile-phone').value.trim();
    const preferredDestinations = document.getElementById('profile-preferred-destinations').value.trim();
    const accommodationType = document.getElementById('profile-accommodation-type').value.trim();
    const budget = document.getElementById('profile-budget').value.trim();
    
    // Create updated profile object
    const updatedProfile = {
        name,
        email,
        phone,
        preferences: {
            preferred_destinations: preferredDestinations,
            accommodation_type: accommodationType,
            budget
        }
    };
    
    // Call API to update profile
    fetch('/api/profile', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updatedProfile)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update local profile data
            userProfile = data.profile;
            
            // Show success message
            const successMsg = document.createElement('div');
            successMsg.className = 'profile-success-message';
            successMsg.textContent = 'Perfil atualizado com sucesso!';
            
            // Add success message after form
            profileForm.after(successMsg);
            
            // Remove success message after 3 seconds
            setTimeout(() => {
                successMsg.remove();
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Error updating profile:', error);
    });
}

// Function to show a specific section
function showSection(section) {
    // Hide all sections
    conversationsSection.style.display = 'none';
    plansSection.style.display = 'none';
    profileSection.style.display = 'none';
    
    // Remove active class from all sidebar items
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section and mark sidebar item as active
    if (section === 'conversations') {
        conversationsSection.style.display = 'block';
        document.querySelector('.sidebar-nav-item[data-section="conversations"]').classList.add('active');
        renderConversationUI();
    } else if (section === 'plans') {
        plansSection.style.display = 'block';
        document.querySelector('.sidebar-nav-item[data-section="plans"]').classList.add('active');
        
        // If no plan is selected, show empty state
        if (!activePlanId && plans.length > 0) {
            activePlanId = plans[0].id;
            loadPlanDetails(activePlanId);
        } else if (plans.length === 0) {
            content.innerHTML = `
                <div class="content-section">
                    <h2 class="content-title">Planos de Viagem</h2>
                    <div class="empty-state">
                        <p>Você ainda não tem planos de viagem. Inicie uma conversa para criar um!</p>
                    </div>
                </div>
            `;
        }
    } else if (section === 'profile') {
        // Exibir o perfil no conteúdo principal em vez de usar a seção oculta
        document.querySelector('.sidebar-nav-item[data-section="profile"]').classList.add('active');
        
        // Renderizar o perfil diretamente no conteúdo principal
        content.innerHTML = `
            <div class="content-section">
                <h2 class="content-title">Seu Perfil</h2>
                <div class="profile-container">
                    <form id="profile-form" class="profile-form">
                        <div class="profile-form-group">
                            <label class="profile-form-label" for="profile-name">Nome</label>
                            <input type="text" id="profile-name" class="profile-form-input" placeholder="Seu nome" value="${userProfile.name || ''}">
                        </div>
                        
                        <div class="profile-form-group">
                            <label class="profile-form-label" for="profile-email">Email</label>
                            <input type="email" id="profile-email" class="profile-form-input" placeholder="Seu endereço de email" value="${userProfile.email || ''}">
                        </div>
                        
                        <div class="profile-form-group">
                            <label class="profile-form-label" for="profile-phone">Telefone</label>
                            <input type="tel" id="profile-phone" class="profile-form-input" placeholder="Seu número de telefone" value="${userProfile.phone || ''}">
                        </div>
                        
                        <h3 class="profile-section-title">Preferências de Viagem</h3>
                        
                        <div class="profile-form-group">
                            <label class="profile-form-label" for="profile-preferred-destinations">Destinos Preferidos</label>
                            <input type="text" id="profile-preferred-destinations" class="profile-form-input" placeholder="Praia, Montanhas, Cidades, etc." value="${userProfile.preferences?.preferred_destinations || ''}">
                        </div>
                        
                        <div class="profile-form-group">
                            <label class="profile-form-label" for="profile-accommodation-type">Tipo de Acomodação</label>
                            <input type="text" id="profile-accommodation-type" class="profile-form-input" placeholder="Hotel, Hostel, Resort, etc." value="${userProfile.preferences?.accommodation_type || ''}">
                        </div>
                        
                        <div class="profile-form-group">
                            <label class="profile-form-label" for="profile-budget">Faixa de Orçamento</label>
                            <input type="text" id="profile-budget" class="profile-form-input" placeholder="Econômico, Médio, Luxo" value="${userProfile.preferences?.budget || ''}">
                        </div>
                        
                        <button type="submit" class="profile-form-button">Salvar Perfil</button>
                    </form>
                </div>
                
                <div class="content-section" style="margin-top: 30px;">
                    <h2 class="content-title">Monitoramento de Preços</h2>
                    <div class="price-monitoring-container">
                        <div class="price-monitoring-header">
                            <h3>Ofertas Monitoradas</h3>
                            <p>Você receberá notificações quando houver queda nos preços destas ofertas.</p>
                        </div>
                        
                        <div id="monitored-offers-list" class="monitored-offers-list">
                            ${monitoredOffers.length === 0 ? `
                                <div class="empty-state">
                                    <p>Você ainda não está monitorando nenhuma oferta.</p>
                                    <p>Busque voos ou hotéis no chat e clique em "Monitorar Preço" para receber notificações quando os preços caírem.</p>
                                </div>
                            ` : monitoredOffers.map(offer => `
                                <div class="monitored-offer-item" data-id="${offer.id}" data-type="${offer.type}">
                                    <div class="monitored-offer-icon">
                                        <i class="fas fa-${offer.type === 'flight' ? 'plane' : 'hotel'}"></i>
                                    </div>
                                    <div class="monitored-offer-content">
                                        <div class="monitored-offer-title">${offer.name}</div>
                                        <div class="monitored-offer-info">${offer.destination}</div>
                                        <div class="monitored-offer-price">
                                            <span class="current-price">${offer.formattedPrice}</span>
                                            ${offer.price < offer.lowestPrice ? '' : `
                                                <span class="lowest-price">Menor preço encontrado: ${formatPrice(offer.lowestPrice)}</span>
                                            `}
                                        </div>
                                        <div class="monitored-offer-date">Monitorando desde ${new Date(offer.added).toLocaleDateString('pt-BR')}</div>
                                    </div>
                                    <button class="remove-monitor-btn" data-id="${offer.id}" data-type="${offer.type}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Função auxiliar para formatar preço
        function formatPrice(price) {
            return `R$${price.toFixed(2).replace('.', ',')}`;
        }
        
        // Recapturar a referência ao formulário de perfil
        const newProfileForm = document.getElementById('profile-form');
        if (newProfileForm) {
            newProfileForm.addEventListener('submit', handleProfileSubmit);
        }
        
        // Adicionar event listeners aos botões de remoção de monitoramento
        const removeButtons = document.querySelectorAll('.remove-monitor-btn');
        removeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                
                const type = btn.dataset.type;
                const id = btn.dataset.id;
                
                // Confirmar com o usuário
                if (confirm('Tem certeza que deseja parar de monitorar esta oferta?')) {
                    // Remover do monitoramento
                    const removed = removePriceMonitor(type, id);
                    
                    if (removed) {
                        // Remover o elemento da interface
                        const offerItem = btn.closest('.monitored-offer-item');
                        offerItem.classList.add('removing');
                        
                        // Animação de remoção
                        setTimeout(() => {
                            offerItem.remove();
                            
                            // Se não houver mais ofertas, mostrar estado vazio
                            if (monitoredOffers.length === 0) {
                                document.getElementById('monitored-offers-list').innerHTML = `
                                    <div class="empty-state">
                                        <p>Você ainda não está monitorando nenhuma oferta.</p>
                                        <p>Busque voos ou hotéis no chat e clique em "Monitorar Preço" para receber notificações quando os preços caírem.</p>
                                    </div>
                                `;
                            }
                        }, 300);
                    }
                }
            });
        });
    }
    
    activeSection = section;
}

// Function to render the conversation UI
function renderConversationUI() {
    content.innerHTML = `
        <div class="content-section">
            <h2 class="content-title">Converse com Flai</h2>
            <div class="chat-container">
                <div id="chat-messages" class="chat-messages"></div>
                
                <form id="chat-form" class="chat-input">
                    <textarea id="message-input" placeholder="Digite sua mensagem..." autocomplete="off" rows="1" maxlength="500"></textarea>
                    <button type="submit">
                        <i class="fas fa-paper-plane"></i> Enviar
                    </button>
                </form>
                
                <!-- Fullscreen Toggle Button -->
                <div id="fullscreen-toggle" class="fullscreen-toggle">
                    <i class="fas fa-expand"></i>
                </div>
            </div>
        </div>
    `;
    
    // Re-attach event listeners
    chatForm = document.getElementById('chat-form');
    chatMessages = document.getElementById('chat-messages');
    
    // Re-attach fullscreen toggle listener
    const fullscreenBtn = document.getElementById('fullscreen-toggle');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', toggleFullscreenChat);
    }
    
    // Apply fullscreen mode if it was active
    if (isFullscreenChat) {
        document.body.classList.add('fullscreen-chat');
        if (fullscreenBtn) {
            fullscreenBtn.querySelector('i').classList.remove('fa-expand');
            fullscreenBtn.querySelector('i').classList.add('fa-compress');
        }
    }
    chatForm.addEventListener('submit', handleChatSubmit);
    
    // Render messages
    renderChatMessages();
}

// Mock functions for Amadeus API (these would be replaced with actual API calls)
/**
 * Search for flights using Amadeus API
 * @param {Object} params - Search parameters
 */
function searchFlights(params) {
    console.log('Searching flights with params:', params);
    // This would be an actual API call in production
    // return fetch('https://api.amadeus.com/v2/shopping/flight-offers', {...})
    
    // For now, return mock data
    return Promise.resolve({
        results: [
            {
                airline: "LATAM",
                flight_number: "LA3456",
                departure: params.origin,
                arrival: params.destination,
                departure_time: "08:30",
                arrival_time: "20:15",
                price: "R$2.450"
            },
            {
                airline: "Gol",
                flight_number: "G35678",
                departure: params.origin,
                arrival: params.destination,
                departure_time: "18:00",
                arrival_time: "07:45 (+1)",
                price: "R$2.820"
            }
        ]
    });
}

/**
 * Search for hotels using Amadeus API
 * @param {Object} params - Search parameters
 */
function searchHotels(params) {
    console.log('Searching hotels with params:', params);
    // This would be an actual API call in production
    // return fetch('https://api.amadeus.com/v2/shopping/hotel-offers', {...})
    
    // For now, return mock data
    return Promise.resolve({
        results: [
            {
                name: `Grande Hotel ${params.city}`,
                stars: 4,
                location: `${params.city} Central`,
                price_per_night: "R$980",
                available: true
            },
            {
                name: `${params.city} Vista Resort`,
                stars: 3,
                location: `Centro de ${params.city}`,
                price_per_night: "R$740",
                available: true
            }
        ]
    });
}

/**
 * Toggle sidebar expand/collapse state
 */
function toggleSidebar() {
    isSidebarCollapsed = !isSidebarCollapsed;
    
    sidebar.classList.toggle('collapsed', isSidebarCollapsed);
    content.classList.toggle('expanded', isSidebarCollapsed);
    
    const icon = sidebarToggle.querySelector('i');
    if (isSidebarCollapsed) {
        icon.classList.remove('fa-chevron-left');
        icon.classList.add('fa-chevron-right');
    } else {
        icon.classList.remove('fa-chevron-right');
        icon.classList.add('fa-chevron-left');
    }
}

/**
 * Toggle fullscreen chat mode
 */
function toggleFullscreenChat() {
    isFullscreenChat = !isFullscreenChat;
    
    document.body.classList.toggle('fullscreen-chat', isFullscreenChat);
    
    const fullscreenBtn = document.getElementById('fullscreen-toggle');
    if (fullscreenBtn) {
        const icon = fullscreenBtn.querySelector('i');
        if (isFullscreenChat) {
            icon.classList.remove('fa-expand');
            icon.classList.add('fa-compress');
        } else {
            icon.classList.remove('fa-compress');
            icon.classList.add('fa-expand');
        }
    }
    
    // Auto-collapse sidebar when entering fullscreen mode
    if (isFullscreenChat && !isSidebarCollapsed) {
        toggleSidebar();
    }
}

// Toggle notifications panel
// Sistema de monitoramento de preços

/**
 * Adiciona uma nova oferta para monitoramento
 * @param {Object} offer - Objeto contendo detalhes da oferta
 * @param {string} offer.type - Tipo da oferta ('flight' ou 'hotel')
 * @param {string} offer.id - Identificador único da oferta
 * @param {string} offer.name - Nome da oferta (companhia aérea + número do voo, ou nome do hotel)
 * @param {string} offer.destination - Destino 
 * @param {number} offer.price - Preço atual em formato numérico (ex: 2450.00)
 * @param {string} offer.formattedPrice - Preço formatado para exibição (ex: "R$2.450")
 * @param {Object} offer.details - Detalhes específicos da oferta (datas, localização, etc)
 */
function addPriceMonitor(offer) {
    // Verifica se a oferta já está sendo monitorada
    const existingOffer = monitoredOffers.find(o => o.id === offer.id && o.type === offer.type);
    
    if (existingOffer) {
        console.log(`Oferta já está sendo monitorada: ${offer.name} para ${offer.destination}`);
        return existingOffer;
    }
    
    // Adiciona timestamp e histórico de preços
    const newOffer = {
        ...offer,
        added: new Date(),
        lastChecked: new Date(),
        priceHistory: [
            {
                price: offer.price,
                date: new Date()
            }
        ],
        lowestPrice: offer.price
    };
    
    // Adiciona à lista de ofertas monitoradas
    monitoredOffers.push(newOffer);
    console.log(`Nova oferta adicionada ao monitoramento: ${offer.name} para ${offer.destination}`);
    
    // Armazena no localStorage
    saveMonitoredOffers();
    
    return newOffer;
}

/**
 * Remove uma oferta do monitoramento
 * @param {string} type - Tipo da oferta ('flight' ou 'hotel')
 * @param {string} id - ID da oferta a ser removida
 */
function removePriceMonitor(type, id) {
    const index = monitoredOffers.findIndex(o => o.id === id && o.type === type);
    
    if (index !== -1) {
        const offer = monitoredOffers[index];
        monitoredOffers.splice(index, 1);
        console.log(`Oferta removida do monitoramento: ${offer.name} para ${offer.destination}`);
        
        // Armazena no localStorage
        saveMonitoredOffers();
        return true;
    }
    
    return false;
}

/**
 * Verifica preços atuais das ofertas monitoradas
 * Normalmente seria chamada periodicamente por um setInterval
 */
function checkPrices() {
    console.log(`Verificando preços para ${monitoredOffers.length} ofertas monitoradas`);
    
    // Para cada oferta monitorada, simulamos uma consulta à API
    monitoredOffers.forEach(offer => {
        // Em uma implementação real, faríamos uma chamada às APIs Amadeus
        // Para esta demonstração, vamos simular mudanças aleatórias de preço
        simulateCheckPrice(offer);
    });
    
    // Atualiza o painel de notificações se estiver aberto
    const notificationsPanel = document.getElementById('notifications-panel');
    if (notificationsPanel && notificationsPanel.classList.contains('active')) {
        renderNotifications();
    }
}

/**
 * Função para simular uma verificação de preço
 * Atualiza o histórico de preços e cria alertas quando necessário
 * Em produção, isso seria substituído por chamadas reais à API Amadeus
 * @param {Object} offer - Oferta a ser verificada
 */
function simulateCheckPrice(offer) {
    // Chance de 30% de ter uma alteração de preço
    if (Math.random() < 0.3) {
        // Simula uma variação de preço entre -15% e +5%
        const variation = (Math.random() * 0.2) - 0.15;
        const newPrice = Math.max(offer.price * (1 + variation), offer.price * 0.5);
        const roundedPrice = Math.round(newPrice * 100) / 100;
        
        // Formata o novo preço
        const formattedPrice = `R$${roundedPrice.toFixed(2).replace('.', ',')}`;
        
        // Se o preço caiu, adiciona um alerta
        if (roundedPrice < offer.price) {
            createPriceAlert(offer, roundedPrice, formattedPrice);
        }
        
        // Atualiza o histórico de preços
        offer.priceHistory.push({
            price: roundedPrice,
            date: new Date()
        });
        
        // Atualiza o preço atual
        offer.price = roundedPrice;
        offer.formattedPrice = formattedPrice;
        
        // Atualiza o menor preço se necessário
        if (roundedPrice < offer.lowestPrice) {
            offer.lowestPrice = roundedPrice;
        }
    }
    
    // Atualiza o timestamp da última verificação
    offer.lastChecked = new Date();
    
    // Salva as alterações
    saveMonitoredOffers();
}

/**
 * Cria um alerta de queda de preço
 * @param {Object} offer - Oferta que teve queda de preço
 * @param {number} newPrice - Novo preço
 * @param {string} formattedPrice - Preço formatado para exibição
 */
function createPriceAlert(offer, newPrice, formattedPrice) {
    const percentDrop = ((offer.price - newPrice) / offer.price * 100).toFixed(1);
    
    const alert = {
        id: `alert-${Date.now()}`,
        offerId: offer.id,
        offerType: offer.type,
        title: offer.type === 'flight'
            ? `Queda de preço: ${offer.name} para ${offer.destination}`
            : `Queda de preço: ${offer.name} em ${offer.destination}`,
        message: `O preço caiu ${percentDrop}% para ${formattedPrice}`,
        icon: offer.type === 'flight' ? 'plane' : 'hotel',
        date: new Date(),
        read: false
    };
    
    // Adiciona o alerta ao início da lista
    priceAlerts.unshift(alert);
    
    // Limita a 50 alertas para não sobrecarregar o armazenamento
    if (priceAlerts.length > 50) {
        priceAlerts.pop();
    }
    
    // Armazena no localStorage
    savePriceAlerts();
    
    // Atualiza o contador de notificações não lidas
    updateUnreadNotificationsCount();
    
    return alert;
}

/**
 * Atualiza o contador de notificações não lidas
 */
function updateUnreadNotificationsCount() {
    const unreadCount = priceAlerts.filter(alert => !alert.read).length;
    
    // Atualiza o badge no ícone de notificações
    const notificationBadge = document.querySelector('.notification-badge');
    if (notificationBadge) {
        if (unreadCount > 0) {
            notificationBadge.textContent = unreadCount;
            notificationBadge.style.display = 'flex';
        } else {
            notificationBadge.style.display = 'none';
        }
    }
}

/**
 * Marca todos os alertas como lidos
 */
function markAllAlertsAsRead() {
    priceAlerts.forEach(alert => {
        alert.read = true;
    });
    
    // Armazena no localStorage
    savePriceAlerts();
    
    // Atualiza o contador
    updateUnreadNotificationsCount();
}

/**
 * Salva as ofertas monitoradas no localStorage
 */
function saveMonitoredOffers() {
    localStorage.setItem('monitoredOffers', JSON.stringify(monitoredOffers));
}

/**
 * Salva os alertas de preço no localStorage
 */
function savePriceAlerts() {
    localStorage.setItem('priceAlerts', JSON.stringify(priceAlerts));
}

/**
 * Carrega as ofertas monitoradas e alertas do localStorage
 */
function loadPriceMonitoringData() {
    try {
        const savedOffers = localStorage.getItem('monitoredOffers');
        if (savedOffers) {
            monitoredOffers = JSON.parse(savedOffers);
            
            // Converte as strings de data para objetos Date
            monitoredOffers.forEach(offer => {
                offer.added = new Date(offer.added);
                offer.lastChecked = new Date(offer.lastChecked);
                offer.priceHistory.forEach(record => {
                    record.date = new Date(record.date);
                });
            });
        }
        
        const savedAlerts = localStorage.getItem('priceAlerts');
        if (savedAlerts) {
            priceAlerts = JSON.parse(savedAlerts);
            
            // Converte as strings de data para objetos Date
            priceAlerts.forEach(alert => {
                alert.date = new Date(alert.date);
            });
        }
        
        // Atualiza o contador de notificações não lidas
        updateUnreadNotificationsCount();
        
        console.log(`Carregados: ${monitoredOffers.length} ofertas e ${priceAlerts.length} alertas`);
    } catch (error) {
        console.error('Erro ao carregar dados do monitoramento de preços:', error);
    }
}

// Função para renderizar as notificações
function renderNotifications() {
    // Verifica se o painel existe
    let notificationsPanel = document.getElementById('notifications-panel');
    
    // Conteúdo HTML para o painel
    const notificationsHtml = `
        <div class="notifications-header">
            <h3>Notificações</h3>
            <div class="notifications-actions">
                <button id="mark-all-read" class="notifications-action-btn">
                    <i class="fas fa-check-double"></i> Marcar todas como lidas
                </button>
                <button id="close-notifications" class="notifications-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
        <div class="notifications-list">
            ${priceAlerts.length > 0 ? priceAlerts.map(alert => `
                <div class="notification-item ${alert.read ? 'read' : 'unread'}" data-id="${alert.id}">
                    <div class="notification-icon">
                        <i class="fas fa-${alert.icon}"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">${alert.title}</div>
                        <div class="notification-message">${alert.message}</div>
                        <div class="notification-time">${formatAlertDate(alert.date)}</div>
                    </div>
                </div>
            `).join('') : `
                <div class="empty-notifications">
                    <p>Você não tem notificações de preço no momento.</p>
                    <p>Adicione uma oferta ao monitoramento para receber alertas quando os preços caírem!</p>
                </div>
            `}
        </div>
    `;
    
    // Se o painel não existe, cria-o
    if (!notificationsPanel) {
        notificationsPanel = document.createElement('div');
        notificationsPanel.id = 'notifications-panel';
        notificationsPanel.className = 'notifications-panel';
        document.body.appendChild(notificationsPanel);
    }
    
    // Atualiza o conteúdo
    notificationsPanel.innerHTML = notificationsHtml;
    
    // Adiciona event listeners
    document.getElementById('close-notifications').addEventListener('click', () => {
        notificationsPanel.classList.remove('active');
    });
    
    const markAllReadBtn = document.getElementById('mark-all-read');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', () => {
            markAllAlertsAsRead();
            renderNotifications();
        });
    }
    
    // Adiciona event listeners para cada notificação
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', () => {
            const alertId = item.dataset.id;
            const alert = priceAlerts.find(a => a.id === alertId);
            
            if (alert) {
                // Marca como lida
                alert.read = true;
                savePriceAlerts();
                updateUnreadNotificationsCount();
                
                // Atualiza a classe visualmente
                item.classList.add('read');
                item.classList.remove('unread');
            }
        });
    });
}

/**
 * Formata a data do alerta para exibição
 * @param {Date} date - Data do alerta
 * @returns {string} - Data formatada
 */
function formatAlertDate(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMinutes < 1) {
        return 'Agora mesmo';
    } else if (diffMinutes < 60) {
        return `${diffMinutes} ${diffMinutes === 1 ? 'minuto' : 'minutos'} atrás`;
    } else if (diffHours < 24) {
        return `${diffHours} ${diffHours === 1 ? 'hora' : 'horas'} atrás`;
    } else if (diffDays < 7) {
        return `${diffDays} ${diffDays === 1 ? 'dia' : 'dias'} atrás`;
    } else {
        return date.toLocaleDateString('pt-BR');
    }
}

// Toggle do painel de notificações
function toggleNotifications() {
    // Marca alertas como lidos quando o painel for aberto
    let notificationsPanel = document.getElementById('notifications-panel');
    
    // Renderiza as notificações (cria ou atualiza o painel)
    renderNotifications();
    
    // Se o painel existe, alterna a classe .active
    if (notificationsPanel) {
        notificationsPanel.classList.toggle('active');
    }
    
    // Se o painel acabou de ser criado, adiciona a classe .active após um breve delay
    if (!notificationsPanel.classList.contains('active')) {
        setTimeout(() => {
            notificationsPanel.classList.add('active');
        }, 10);
    }
}

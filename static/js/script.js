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

// Load initial data
document.addEventListener('DOMContentLoaded', () => {
    loadConversations();
    loadPlans();
    loadProfile();
    
    // Show conversations section by default
    showSection('conversations');
    
    // Add event listeners
    chatForm.addEventListener('submit', handleChatSubmit);
    profileForm.addEventListener('submit', handleProfileSubmit);
    
    // Add event listeners to sidebar links
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const section = e.currentTarget.dataset.section;
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
            // Clear existing chat and load new conversation
            chatHistory = [];
            renderChatMessages();
            showSection('conversations');
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
                        resultsHtml += `
                            <div class="plan-card">
                                <div class="plan-card-title">${flight.airline} - ${flight.flight_number}</div>
                                <div class="plan-card-info">${flight.departure} → ${flight.arrival}</div>
                                <div class="plan-card-info">Partida: ${flight.departure_time} | Chegada: ${flight.arrival_time}</div>
                                <div class="plan-card-price">${flight.price}</div>
                            </div>
                        `;
                    });
                } else {
                    resultsHtml += '<h4>Opções de Hotéis:</h4>';
                    searchData.results.forEach(hotel => {
                        resultsHtml += `
                            <div class="plan-card">
                                <div class="plan-card-title">${hotel.name} (${hotel.stars}★)</div>
                                <div class="plan-card-info">${hotel.location}</div>
                                <div class="plan-card-price">${hotel.price_per_night} por noite</div>
                            </div>
                        `;
                    });
                }
                
                resultsHtml += '</div>';
                addMessageToChat('assistant', resultsHtml);
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
        profileSection.style.display = 'block';
        document.querySelector('.sidebar-nav-item[data-section="profile"]').classList.add('active');
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
                    <input id="message-input" type="text" placeholder="Digite sua mensagem..." autocomplete="off">
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
function toggleNotifications() {
    // Check if notifications panel exists
    let notificationsPanel = document.getElementById('notifications-panel');
    
    // If panel doesn't exist, create it
    if (!notificationsPanel) {
        notificationsPanel = document.createElement('div');
        notificationsPanel.id = 'notifications-panel';
        notificationsPanel.className = 'notifications-panel';
        
        // Add some mock notifications
        notificationsPanel.innerHTML = `
            <div class="notifications-header">
                <h3>Notificações</h3>
                <button id="close-notifications" class="notifications-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notifications-list">
                <div class="notification-item">
                    <div class="notification-icon">
                        <i class="fas fa-plane"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">Sua viagem para Barcelona começa em 5 dias!</div>
                        <div class="notification-time">Hoje, 10:30</div>
                    </div>
                </div>
                <div class="notification-item">
                    <div class="notification-icon">
                        <i class="fas fa-hotel"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">Confirmação de reserva recebida do Hotel Barcelona Central</div>
                        <div class="notification-time">Ontem, 14:15</div>
                    </div>
                </div>
                <div class="notification-item">
                    <div class="notification-icon">
                        <i class="fas fa-percent"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">Promoção de última hora: 15% de desconto em voos para Lisboa</div>
                        <div class="notification-time">2 dias atrás</div>
                    </div>
                </div>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(notificationsPanel);
        
        // Add close button event listener
        document.getElementById('close-notifications').addEventListener('click', () => {
            notificationsPanel.classList.remove('active');
        });
    } else {
        // Toggle active class
        notificationsPanel.classList.toggle('active');
    }
    
    // If panel was just created, add active class after a brief delay
    if (!notificationsPanel.classList.contains('active')) {
        setTimeout(() => {
            notificationsPanel.classList.add('active');
        }, 10);
    }
}

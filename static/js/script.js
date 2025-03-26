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
const chatForm = document.getElementById('chat-form');
const chatMessages = document.getElementById('chat-messages');
const profileForm = document.getElementById('profile-form');

// State management
let activeSection = 'conversations';
let conversations = [];
let plans = [];
let userProfile = {};
let activePlanId = null;
let chatHistory = [];

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
            <div class="sidebar-list-item-info">Updated: ${conversation.last_updated}</div>
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
            airline: "Air France",
            flight_number: "AF1234",
            departure: "New York (JFK)",
            arrival: plan.destination.split(',')[0],
            departure_time: "08:30",
            arrival_time: "20:15",
            price: "€450"
        },
        {
            airline: "Delta",
            flight_number: "DL5678",
            departure: "New York (JFK)",
            arrival: plan.destination.split(',')[0],
            departure_time: "18:00",
            arrival_time: "07:45 (+1)",
            price: "€520"
        }
    ];
    
    const mockHotels = [
        {
            name: `Grand Hotel ${plan.destination.split(',')[0]}`,
            stars: 4,
            location: `Central ${plan.destination.split(',')[0]}`,
            price_per_night: "€180",
            available: true
        },
        {
            name: `${plan.destination.split(',')[0]} View Resort`,
            stars: 3,
            location: `Downtown ${plan.destination.split(',')[0]}`,
            price_per_night: "€135",
            available: true
        }
    ];
    
    // Update main content with plan details
    content.innerHTML = `
        <div class="content-section">
            <h2 class="content-title">Travel Plan Details</h2>
            <div class="plan-details">
                <div class="plan-header">
                    <h3 class="plan-title">${plan.title}</h3>
                    <div class="plan-dates">${plan.start_date} - ${plan.end_date}</div>
                    <div class="plan-destination">${plan.destination}</div>
                </div>
                
                <div class="plan-section">
                    <h4 class="plan-section-title">Trip Details</h4>
                    <p>${plan.details}</p>
                </div>
                
                <div class="plan-section">
                    <h4 class="plan-section-title">Flights</h4>
                    <div class="plan-flight-cards">
                        ${mockFlights.map(flight => `
                            <div class="plan-card">
                                <div class="plan-card-title">${flight.airline} - ${flight.flight_number}</div>
                                <div class="plan-card-info">${flight.departure} → ${flight.arrival}</div>
                                <div class="plan-card-info">Departure: ${flight.departure_time} | Arrival: ${flight.arrival_time}</div>
                                <div class="plan-card-price">${flight.price}</div>
                            </div>
                        `).join('')}
                        <p class="plan-section-note">Note: Flight data would come from Amadeus API in production</p>
                    </div>
                </div>
                
                <div class="plan-section">
                    <h4 class="plan-section-title">Accommodations</h4>
                    <div class="plan-hotel-cards">
                        ${mockHotels.map(hotel => `
                            <div class="plan-card">
                                <div class="plan-card-title">${hotel.name} (${hotel.stars}★)</div>
                                <div class="plan-card-info">${hotel.location}</div>
                                <div class="plan-card-price">${hotel.price_per_night} per night</div>
                            </div>
                        `).join('')}
                        <p class="plan-section-note">Note: Hotel data would come from Amadeus API in production</p>
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
        
        // Check if response mentions flights or hotels
        if (message.toLowerCase().includes('flight') || message.toLowerCase().includes('hotel')) {
            // Simulate Amadeus API call
            const searchType = message.toLowerCase().includes('flight') ? 'flights' : 'hotels';
            
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
                    resultsHtml += '<h4>Flight Options:</h4>';
                    searchData.results.forEach(flight => {
                        resultsHtml += `
                            <div class="plan-card">
                                <div class="plan-card-title">${flight.airline} - ${flight.flight_number}</div>
                                <div class="plan-card-info">${flight.departure} → ${flight.arrival}</div>
                                <div class="plan-card-info">Departure: ${flight.departure_time} | Arrival: ${flight.arrival_time}</div>
                                <div class="plan-card-price">${flight.price}</div>
                            </div>
                        `;
                    });
                } else {
                    resultsHtml += '<h4>Hotel Options:</h4>';
                    searchData.results.forEach(hotel => {
                        resultsHtml += `
                            <div class="plan-card">
                                <div class="plan-card-title">${hotel.name} (${hotel.stars}★)</div>
                                <div class="plan-card-info">${hotel.location}</div>
                                <div class="plan-card-price">${hotel.price_per_night} per night</div>
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
        addMessageToChat('assistant', 'Sorry, there was an error processing your request. Please try again.');
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
            </div>
        </div>
    `;
    
    // Re-attach event listeners
    chatForm = document.getElementById('chat-form');
    chatMessages = document.getElementById('chat-messages');
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

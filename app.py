import os
import logging
from flask import Flask, render_template, jsonify, request

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Mock data for conversations
conversations = [
    {"id": 1, "title": "Trip to Paris", "last_updated": "2023-10-15"},
    {"id": 2, "title": "Weekend in Barcelona", "last_updated": "2023-09-28"},
    {"id": 3, "title": "Summer vacation planning", "last_updated": "2023-08-10"}
]

# Mock data for travel plans
plans = [
    {
        "id": 1,
        "title": "Weekend in Barcelona",
        "destination": "Barcelona, Spain",
        "start_date": "2023-12-15",
        "end_date": "2023-12-17",
        "details": "A weekend getaway to explore the architecture and cuisine of Barcelona."
    },
    {
        "id": 2,
        "title": "Summer in Greece",
        "destination": "Athens and Santorini, Greece",
        "start_date": "2024-06-10",
        "end_date": "2024-06-20",
        "details": "A 10-day vacation exploring Athens and relaxing in Santorini."
    }
]

# Mock user profile
user_profile = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1 123-456-7890",
    "preferences": {
        "preferred_destinations": "Beach, Mountains",
        "accommodation_type": "Hotel",
        "budget": "Medium"
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/conversations')
def get_conversations():
    return jsonify(conversations)

@app.route('/api/plans')
def get_plans():
    return jsonify(plans)

@app.route('/api/plan/<int:plan_id>')
def get_plan(plan_id):
    plan = next((p for p in plans if p["id"] == plan_id), None)
    if plan:
        return jsonify(plan)
    return jsonify({"error": "Plan not found"}), 404

@app.route('/api/profile')
def get_profile():
    return jsonify(user_profile)

@app.route('/api/profile', methods=['POST'])
def update_profile():
    global user_profile
    data = request.json
    
    # Update only the provided fields
    if 'name' in data:
        user_profile['name'] = data['name']
    if 'email' in data:
        user_profile['email'] = data['email']
    if 'phone' in data:
        user_profile['phone'] = data['phone']
    if 'preferences' in data:
        user_profile['preferences'] = data['preferences']
    
    return jsonify({"success": True, "profile": user_profile})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    # Mock GPT response
    if 'paris' in user_message.lower():
        response = "Paris is a beautiful destination! The best time to visit is spring (April to June) or fall (September to November). Would you like me to suggest some accommodations or activities?"
    elif 'flight' in user_message.lower():
        response = "I can help you find flights. Could you provide your departure city, destination, and travel dates?"
    elif 'hotel' in user_message.lower() or 'accommodation' in user_message.lower():
        response = "For accommodations, I recommend checking options in the city center for the best experience. What's your budget range per night?"
    else:
        response = "I'm your Flai travel assistant. Tell me about your travel plans, and I'll help you organize the perfect trip. Where would you like to go?"
    
    return jsonify({
        "response": response,
        "note": "This is a mock response. In production, this would connect to the GPT API."
    })

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    search_type = data.get('type', '')
    
    # Mock Amadeus API response
    if search_type == 'flights':
        return jsonify({
            "results": [
                {
                    "airline": "Air France",
                    "flight_number": "AF1234",
                    "departure": "New York (JFK)",
                    "arrival": "Paris (CDG)",
                    "departure_time": "08:30",
                    "arrival_time": "20:15",
                    "price": "€450"
                },
                {
                    "airline": "Delta",
                    "flight_number": "DL5678",
                    "departure": "New York (JFK)",
                    "arrival": "Paris (CDG)",
                    "departure_time": "18:00",
                    "arrival_time": "07:45 (+1)",
                    "price": "€520"
                }
            ],
            "note": "This is a mock response. In production, this would connect to the Amadeus API."
        })
    elif search_type == 'hotels':
        return jsonify({
            "results": [
                {
                    "name": "Grand Hotel Paris",
                    "stars": 4,
                    "location": "Central Paris",
                    "price_per_night": "€180",
                    "available": True
                },
                {
                    "name": "Seine River View",
                    "stars": 3,
                    "location": "Left Bank, Paris",
                    "price_per_night": "€135",
                    "available": True
                }
            ],
            "note": "This is a mock response. In production, this would connect to the Amadeus API."
        })
    else:
        return jsonify({
            "error": "Invalid search type. Use 'flights' or 'hotels'."
        }), 400

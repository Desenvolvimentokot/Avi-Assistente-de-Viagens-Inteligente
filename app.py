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
    {"id": 1, "title": "Viagem para Paris", "last_updated": "15/10/2023"},
    {"id": 2, "title": "Final de semana em Barcelona", "last_updated": "28/09/2023"},
    {"id": 3, "title": "Planejamento de férias de verão", "last_updated": "10/08/2023"}
]

# Mock data for travel plans
plans = [
    {
        "id": 1,
        "title": "Final de semana em Barcelona",
        "destination": "Barcelona, Espanha",
        "start_date": "15/12/2023",
        "end_date": "17/12/2023",
        "details": "Um fim de semana para explorar a arquitetura e a culinária de Barcelona."
    },
    {
        "id": 2,
        "title": "Verão na Grécia",
        "destination": "Atenas e Santorini, Grécia",
        "start_date": "10/06/2024",
        "end_date": "20/06/2024",
        "details": "Férias de 10 dias explorando Atenas e relaxando em Santorini."
    }
]

# Mock user profile
user_profile = {
    "name": "João Silva",
    "email": "joao.silva@exemplo.com",
    "phone": "+55 11 98765-4321",
    "preferences": {
        "preferred_destinations": "Praia, Montanha",
        "accommodation_type": "Hotel",
        "budget": "Médio"
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
    return jsonify({"error": "Plano não encontrado"}), 404

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
        response = "Paris é um destino maravilhoso! A melhor época para visitar é na primavera (abril a junho) ou no outono (setembro a novembro). Gostaria que eu sugerisse algumas acomodações ou atividades?"
    elif 'voo' in user_message.lower() or 'passagem' in user_message.lower():
        response = "Posso ajudar você a encontrar voos. Poderia me informar sua cidade de partida, destino e datas de viagem?"
    elif 'hotel' in user_message.lower() or 'hospedagem' in user_message.lower():
        response = "Para hospedagem, recomendo verificar opções no centro da cidade para a melhor experiência. Qual é a sua faixa de orçamento por noite?"
    else:
        response = "Sou o Flai, seu assistente de viagens. Conte-me sobre seus planos de viagem, e vou ajudar a organizar a viagem perfeita. Para onde você gostaria de ir?"
    
    return jsonify({
        "response": response,
        "note": "Esta é uma resposta simulada. Em produção, seria conectado à API GPT."
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
                    "airline": "LATAM",
                    "flight_number": "LA3456",
                    "departure": "São Paulo (GRU)",
                    "arrival": "Paris (CDG)",
                    "departure_time": "08:30",
                    "arrival_time": "20:15",
                    "price": "R$2.450"
                },
                {
                    "airline": "Gol",
                    "flight_number": "G35678",
                    "departure": "São Paulo (GRU)",
                    "arrival": "Paris (CDG)",
                    "departure_time": "18:00",
                    "arrival_time": "07:45 (+1)",
                    "price": "R$2.820"
                }
            ],
            "note": "Esta é uma resposta simulada. Em produção, seria conectado à API Amadeus."
        })
    elif search_type == 'hotels':
        return jsonify({
            "results": [
                {
                    "name": "Grande Hotel Paris",
                    "stars": 4,
                    "location": "Paris Central",
                    "price_per_night": "R$980",
                    "available": True
                },
                {
                    "name": "Vista Rio Sena",
                    "stars": 3,
                    "location": "Margem Esquerda, Paris",
                    "price_per_night": "R$740",
                    "available": True
                }
            ],
            "note": "Esta é uma resposta simulada. Em produção, seria conectado à API Amadeus."
        })
    else:
        return jsonify({
            "error": "Tipo de pesquisa inválido. Use 'flights' ou 'hotels'."
        }), 400

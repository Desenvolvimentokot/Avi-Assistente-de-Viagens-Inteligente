import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request

# Importação dos serviços
from services.amadeus_service import AmadeusService
from services.openai_service import OpenAIService

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Inicializa os serviços
amadeus_service = AmadeusService()
openai_service = OpenAIService()

# Dados temporários (serão substituídos por banco de dados)
conversations = [
    {"id": 1, "title": "Viagem para Paris", "last_updated": "15/10/2023"},
    {"id": 2, "title": "Final de semana em Barcelona", "last_updated": "28/09/2023"},
    {"id": 3, "title": "Planejamento de férias de verão", "last_updated": "10/08/2023"}
]

# Armazena mensagens das conversas
conversation_messages = {
    1: [
        {"is_user": True, "content": "Olá, estou planejando uma viagem para Paris.", "timestamp": "2023-10-15T10:30:00"},
        {"is_user": False, "content": "Paris é um destino maravilhoso! A melhor época para visitar é na primavera (abril a junho) ou no outono (setembro a novembro). Gostaria que eu sugerisse algumas acomodações ou atividades?", "timestamp": "2023-10-15T10:30:15"}
    ]
}

# Dados de viagens
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

# Dados do perfil do usuário
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
    conversation_id = data.get('conversation_id')
    
    # Obter histórico da conversa, se existir
    messages_history = []
    if conversation_id and conversation_id in conversation_messages:
        messages_history = conversation_messages[conversation_id]
    
    try:
        # Chamar a API da OpenAI através do nosso serviço
        result = openai_service.travel_assistant(user_message, messages_history)
        
        if 'error' in result:
            logging.error(f"Erro na API do OpenAI: {result['error']}")
            return jsonify({
                "response": "Desculpe, estou enfrentando problemas para processar sua solicitação no momento. Por favor, tente novamente mais tarde.",
                "error": result['error']
            }), 500
        
        # Adicionar a mensagem do usuário e a resposta ao histórico
        now = datetime.now().isoformat()
        
        # Adicionar mensagem do usuário ao histórico
        new_user_message = {
            "is_user": True,
            "content": user_message,
            "timestamp": now
        }
        
        # Adicionar resposta do assistente ao histórico
        assistant_response = result['response']
        new_assistant_message = {
            "is_user": False,
            "content": assistant_response,
            "timestamp": now
        }
        
        # Se for uma nova conversa, criar um ID e título
        if not conversation_id:
            new_id = max([c['id'] for c in conversations], default=0) + 1
            title = user_message[:30] + "..." if len(user_message) > 30 else user_message
            conversations.append({
                "id": new_id,
                "title": title,
                "last_updated": datetime.now().strftime("%d/%m/%Y")
            })
            conversation_id = new_id
            conversation_messages[conversation_id] = []
        
        # Adicionar as novas mensagens ao histórico
        conversation_messages[conversation_id].append(new_user_message)
        conversation_messages[conversation_id].append(new_assistant_message)
        
        # Atualizar o timestamp da última atualização da conversa
        for conv in conversations:
            if conv['id'] == conversation_id:
                conv['last_updated'] = datetime.now().strftime("%d/%m/%Y")
                break
        
        return jsonify({
            "response": assistant_response,
            "conversation_id": conversation_id
        })
    
    except Exception as e:
        logging.error(f"Erro ao processar mensagem do chat: {str(e)}")
        return jsonify({
            "response": "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde.",
            "error": str(e)
        }), 500

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

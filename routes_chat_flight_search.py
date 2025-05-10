"""
Módulo para integrar a busca oculta de voos com o chat da AVI
Este módulo processa as mensagens do chat e inicia buscas de voos
quando necessário, usando o iframe invisível.
"""

import json
import logging
import uuid
from flask import Blueprint, request, jsonify, make_response, current_app
from services.chat_flight_extractor import ChatFlightExtractor

# Configurar logger
logger = logging.getLogger(__name__)

# Criar instância do extrator
flight_extractor = ChatFlightExtractor()

# Criar Blueprint
chat_flight_search_bp = Blueprint('chat_flight_search', __name__)

@chat_flight_search_bp.route('/api/chat-extract-flight', methods=['POST'])
def extract_flight_info():
    """
    Endpoint para extrair informações de voo de uma mensagem do usuário.
    
    Request JSON:
    {
        "message": "Quero viajar de São Paulo para o Rio de Janeiro no dia 10/06",
        "context": {
            "travel_info": { ... informações anteriores ... }
        }
    }
    
    Response:
    {
        "success": true,
        "flight_info": {
            "origin": "GRU",
            "destination": "GIG",
            "departure_date": "2025-06-10",
            "return_date": null,
            "adults": 1,
            "ready_for_search": true
        },
        "has_flight_intent": true
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Dados ausentes no corpo da requisição"
            }), 400
        
        # Extrair parâmetros
        message = data.get('message', '')
        context = data.get('context', {})
        
        if not message:
            return jsonify({
                "success": False,
                "message": "Mensagem ausente"
            }), 400
        
        # Verificar se a mensagem contém intenção de busca de voos
        has_flight_intent = flight_extractor.is_flight_search_intent(message)
        
        # Se tiver intenção, extrair informações
        flight_info = None
        if has_flight_intent:
            flight_info = flight_extractor.extract_flight_info(message, context)
        
        # Resposta para o frontend
        return jsonify({
            "success": True,
            "flight_info": flight_info,
            "has_flight_intent": has_flight_intent
        })
        
    except Exception as e:
        logger.error(f"Erro ao extrair informações de voo: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao processar: {str(e)}"
        }), 500

@chat_flight_search_bp.route('/api/initiate-hidden-search', methods=['POST'])
def initiate_hidden_search():
    """
    Endpoint para iniciar uma busca oculta de voos.
    
    Request JSON:
    {
        "flight_info": {
            "origin": "GRU",
            "destination": "GIG",
            "departure_date": "2025-06-10",
            "return_date": null,
            "adults": 1
        },
        "session_id": "uuid-string"
    }
    
    Response:
    {
        "success": true,
        "message": "Busca iniciada com sucesso",
        "search_initiated": true,
        "flight_info": { ... informações do voo ... },
        "session_id": "uuid-string",
        "trigger_hidden_search": true
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Dados ausentes no corpo da requisição"
            }), 400
        
        # Extrair parâmetros
        flight_info = data.get('flight_info', {})
        session_id = data.get('session_id')
        
        # Validar parâmetros obrigatórios
        required_fields = ['origin', 'destination', 'departure_date']
        for field in required_fields:
            if field not in flight_info or not flight_info[field]:
                return jsonify({
                    "success": False,
                    "message": f"Campo obrigatório ausente: {field}"
                }), 400
        
        # Obter ou gerar ID de sessão
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Registrar informações de voo para esta sessão
        if 'chat_sessions' not in current_app.config:
            current_app.config['chat_sessions'] = {}
        
        if session_id not in current_app.config['chat_sessions']:
            current_app.config['chat_sessions'][session_id] = {}
        
        current_app.config['chat_sessions'][session_id]['flight_info'] = flight_info
        current_app.config['chat_sessions'][session_id]['search_requested'] = True
        
        logger.info(f"Busca oculta registrada para sessão {session_id}: {flight_info}")
        
        # Resposta para o frontend
        response = jsonify({
            "success": True,
            "message": "Busca iniciada com sucesso",
            "search_initiated": True,
            "flight_info": flight_info,
            "session_id": session_id,
            "trigger_hidden_search": True
        })
        
        # Definir cookies para manter a sessão
        response.set_cookie('flai_session_id', session_id, max_age=86400*30, httponly=True)
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao iniciar busca oculta: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao iniciar busca: {str(e)}"
        }), 500
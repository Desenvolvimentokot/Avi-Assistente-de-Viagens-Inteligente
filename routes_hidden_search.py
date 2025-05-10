"""
Módulo para implementação da busca oculta de voos usando iframe invisível
Esta abordagem permite obter dados reais de voos sem usar um navegador headless no servidor.
"""

import json
import uuid
import logging
from flask import Blueprint, request, jsonify, render_template, session, current_app, make_response

# Configurar logger
logger = logging.getLogger(__name__)

# Criar Blueprint
hidden_search_bp = Blueprint('hidden_search', __name__)

@hidden_search_bp.route('/hidden-search')
def hidden_search():
    """
    Renderiza a página com o widget oculto de busca de voos.
    Esta página usa um iframe invisível para carregar o widget Trip.com
    e capturar os resultados.
    """
    logger.info("Acessando página de busca oculta")
    return render_template('hidden_flight_search.html')

@hidden_search_bp.route('/api/hidden-flight-search', methods=['POST'])
def start_hidden_flight_search():
    """
    Inicia uma busca oculta de voos.
    
    Request JSON:
    {
        "origin": "GRU",
        "destination": "JFK",
        "departure_date": "2025-06-01",
        "return_date": "2025-06-15",  // opcional
        "adults": 1  // opcional, padrão é 1
    }
    
    Response:
    {
        "success": true,
        "message": "Buscando voos...",
        "action": "open_hidden_frame",
        "url": "/hidden-search?origin=GRU&destination=JFK...",
        "session_id": "uuid-string"
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
        origin = data.get('origin')
        destination = data.get('destination')
        departure_date = data.get('departure_date')
        return_date = data.get('return_date', '')
        adults = data.get('adults', 1)
        
        # Validar parâmetros obrigatórios
        if not origin or not destination or not departure_date:
            return jsonify({
                "success": False,
                "message": "Parâmetros obrigatórios ausentes (origin, destination, departure_date)"
            }), 400
        
        # Obter ou gerar ID de sessão
        session_id = request.cookies.get('flai_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Gerar URL para a página oculta
        search_url = f"/hidden-search?origin={origin}&destination={destination}&departure_date={departure_date}"
        
        if return_date:
            search_url += f"&return_date={return_date}"
            
        search_url += f"&adults={adults}&session_id={session_id}"
        
        logger.info(f"Iniciando busca oculta: {search_url}")
        
        # Resposta para o frontend
        return jsonify({
            "success": True,
            "message": "Buscando voos...",
            "action": "open_hidden_frame",
            "url": search_url,
            "session_id": session_id
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar busca oculta: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao iniciar busca: {str(e)}"
        }), 500

@hidden_search_bp.route('/api/save-flight-results', methods=['POST'])
def save_flight_results():
    """
    Salva os resultados de voos encontrados pelo widget.
    
    Request JSON:
    {
        "flights": [...],  // array de objetos de voos
        "session_id": "uuid-string"
    }
    
    Response:
    {
        "success": true,
        "message": "Resultados salvos com sucesso",
        "redirect_url": "/chat"
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
        flights = data.get('flights', [])
        session_id = data.get('session_id')
        
        if not flights or not session_id:
            return jsonify({
                "success": False,
                "message": "Parâmetros inválidos (flights, session_id)"
            }), 400
        
        logger.info(f"Recebidos {len(flights)} resultados para sessão {session_id}")
        
        # Formatar os resultados
        formatted_flights = []
        for flight in flights:
            try:
                # A estrutura exata pode variar dependendo do retorno do widget
                formatted_flight = {
                    "airline": flight.get('airline', 'Desconhecida'),
                    "flight_number": flight.get('flight_number', ''),
                    "origin": flight.get('origin', ''),
                    "destination": flight.get('destination', ''),
                    "departure_at": flight.get('departure_at', ''),
                    "arrival_at": flight.get('arrival_at', ''),
                    "price": flight.get('price', 0)
                }
                formatted_flights.append(formatted_flight)
            except Exception as e:
                logger.error(f"Erro ao formatar voo: {str(e)}")
        
        # Aqui precisaríamos de um mecanismo para armazenar os resultados
        # Para testes, vamos apenas guardar no app.config
        if 'flight_results' not in current_app.config:
            current_app.config['flight_results'] = {}
        
        current_app.config['flight_results'][session_id] = formatted_flights
        
        logger.info(f"Resultados salvos para sessão {session_id}")
        
        # Resposta para o frontend
        return jsonify({
            "success": True,
            "message": "Resultados salvos com sucesso",
            "redirect_url": "/chat"
        })
        
    except Exception as e:
        logger.error(f"Erro ao salvar resultados: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao salvar resultados: {str(e)}"
        }), 500
        
@hidden_search_bp.route('/api/chat-flight-results', methods=['GET'])
def get_chat_flight_results():
    """
    Verifica se há resultados de voos disponíveis para o chat.
    
    Response:
    {
        "success": true,
        "message": "Resultados disponíveis",
        "results": [...],  // array de objetos de voos ou vazio
        "has_results": true/false
    }
    """
    try:
        # Obter ID de sessão
        session_id = request.cookies.get('flai_session_id')
        
        if not session_id:
            return jsonify({
                "success": False,
                "message": "Sessão não encontrada",
                "results": [],
                "has_results": False
            })
        
        logger.info(f"Verificando resultados para sessão {session_id}")
        
        # Verificar se há resultados para esta sessão
        results = []
        if 'flight_results' in current_app.config and session_id in current_app.config['flight_results']:
            results = current_app.config['flight_results'][session_id]
            
            # Limpar resultados após retorná-los
            del current_app.config['flight_results'][session_id]
            
            logger.info(f"Encontrados {len(results)} resultados para sessão {session_id}")
        
        # Criar resposta
        response = jsonify({
            "success": True,
            "message": "Resultados verificados com sucesso",
            "results": results,
            "has_results": len(results) > 0
        })
        
        # Garantir que a sessão seja mantida
        if session_id:
            response.set_cookie('flai_session_id', session_id, max_age=86400*30, httponly=True)
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao verificar resultados: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao verificar resultados: {str(e)}",
            "results": [],
            "has_results": False
        }), 500
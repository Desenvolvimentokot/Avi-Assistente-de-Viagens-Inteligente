"""
API para integração do widget Trip.com/TravelPayouts com o chat AVI
Este módulo fornece endpoints para carregamento do widget em modo headless
e obtenção de resultados para exibição na interface de chat.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, current_app
from services.flight_widget_loader import FlightWidgetLoader

# Configurar logging
logger = logging.getLogger(__name__)

# Criar Blueprint
widget_api = Blueprint('widget_api', __name__)

# Instanciar o carregador de widget
flight_widget_loader = FlightWidgetLoader()

# Armazenamento em memória para buscas em andamento
# Na implementação final, utilizar Redis ou outro cache distribuído
active_searches = {}

@widget_api.route('/search', methods=['POST'])
def start_search():
    """
    Inicia uma busca de voos usando o widget headless.
    
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
        "search_id": "uuid-string",
        "message": "Busca iniciada com sucesso"
    }
    """
    try:
        # Obter dados da requisição
        data = request.json
        
        # Validar dados obrigatórios
        if not data or not all(k in data for k in ['origin', 'destination', 'departure_date']):
            return jsonify({
                'error': 'Parâmetros incompletos. Obrigatório: origin, destination, departure_date'
            }), 400
        
        # Gerar ID para a busca
        search_id = str(uuid.uuid4())
        
        # Armazenar dados da busca
        search_data = {
            'id': search_id,
            'params': data,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'results': None
        }
        active_searches[search_id] = search_data
        
        # Iniciar busca em background
        # Aqui apenas agendamos, o processamento real aconteceria em um worker separado
        try:
            # Iniciar busca headless
            flight_widget_loader.start_search(
                search_id=search_id,
                origin=data.get('origin'),
                destination=data.get('destination'),
                departure_date=data.get('departure_date'),
                return_date=data.get('return_date'),
                adults=data.get('adults', 1)
            )
            active_searches[search_id]['status'] = 'processing'
            logger.info(f"Busca iniciada: {search_id} - {data.get('origin')} → {data.get('destination')}")
        except Exception as e:
            logger.error(f"Erro ao iniciar busca: {str(e)}")
            active_searches[search_id]['status'] = 'error'
            active_searches[search_id]['error'] = str(e)
        
        # Retornar ID da busca
        return jsonify({
            'search_id': search_id,
            'message': 'Busca iniciada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar requisição de busca: {str(e)}")
        return jsonify({
            'error': f'Erro ao iniciar busca: {str(e)}'
        }), 500

@widget_api.route('/status/<search_id>', methods=['GET'])
def check_status(search_id):
    """
    Verifica o status de uma busca em andamento.
    
    Retorna:
    {
        "status": "pending|processing|complete|error",
        "message": "Mensagem de status",
        "progress": 50  // porcentagem de progresso (opcional)
    }
    """
    # Verificar se a busca existe
    if search_id not in active_searches:
        return jsonify({
            'error': 'Busca não encontrada'
        }), 404
    
    # Obter dados da busca
    search_data = active_searches[search_id]
    
    # Verificar status real com o widget loader
    try:
        status_info = flight_widget_loader.check_status(search_id)
        
        # Atualizar status no armazenamento
        if status_info:
            search_data['status'] = status_info.get('status', search_data['status'])
            search_data['progress'] = status_info.get('progress', 0)
            search_data['message'] = status_info.get('message', '')
            
            # Se a busca foi concluída, armazenar resultados
            if status_info.get('status') == 'complete' and status_info.get('results'):
                search_data['results'] = status_info['results']
    except Exception as e:
        logger.error(f"Erro ao verificar status: {str(e)}")
        # Não alteramos o status aqui para não interromper o fluxo
    
    # Retornar status atual
    return jsonify({
        'status': search_data['status'],
        'message': search_data.get('message', 'Processando busca...'),
        'progress': search_data.get('progress', 0)
    })

@widget_api.route('/results/<search_id>', methods=['GET'])
def get_results(search_id):
    """
    Obtém os resultados de uma busca concluída.
    
    Retorna:
    {
        "flights": [
            {
                "airline": "LATAM",
                "price": 2500.00,
                "currency": "BRL",
                "departure": "10:00",
                "arrival": "15:30",
                "duration": "5h 30m",
                "stops": 1,
                "bookingUrl": "https://..."
            },
            ...
        ]
    }
    """
    # Verificar se a busca existe
    if search_id not in active_searches:
        return jsonify({
            'error': 'Busca não encontrada'
        }), 404
    
    # Obter dados da busca
    search_data = active_searches[search_id]
    
    # Verificar se a busca foi concluída
    if search_data['status'] != 'complete':
        return jsonify({
            'error': f'Busca ainda não concluída. Status atual: {search_data["status"]}'
        }), 400
    
    # Verificar se temos resultados
    if not search_data.get('results'):
        # Tentar buscar resultados novamente
        try:
            results = flight_widget_loader.get_results(search_id)
            search_data['results'] = results
        except Exception as e:
            logger.error(f"Erro ao buscar resultados: {str(e)}")
            return jsonify({
                'error': f'Erro ao buscar resultados: {str(e)}'
            }), 500
    
    # Retornar resultados
    return jsonify({
        'flights': search_data.get('results', [])
    })

@widget_api.route('/search_page', methods=['GET'])
def search_page():
    """
    Renderiza a página de busca headless (não visível para o usuário).
    Esta página será carregada pelo FlightWidgetLoader em um browser headless.
    """
    return render_template('widget_search.html')

@widget_api.route('/demo_search', methods=['GET'])
def demo_search():
    """
    Renderiza uma interface de demonstração para testar a API de busca.
    """
    return render_template('widget_api_demo.html')

@widget_api.route('/chat_search', methods=['GET'])
def chat_search():
    """
    Renderiza a interface de chat com integração de busca de voos.
    """
    return render_template('chat_flight_search.html')
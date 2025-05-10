"""
API de busca headless de voos usando o widget Trip.com

Este módulo implementa as rotas necessárias para:
1. Iniciar uma busca de voos headless
2. Verificar o status de uma busca em andamento
3. Obter os resultados de uma busca

Os dados são obtidos diretamente do widget Trip.com usando um navegador headless.
"""

import logging
import uuid
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, url_for, render_template, current_app, session

from services.flight_widget_loader import FlightWidgetLoader

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar blueprint para as rotas da API
widget_api = Blueprint('widget_api', __name__)

# Cache temporário para armazenar resultados de buscas
# Em produção isso poderia ser um banco de dados
search_cache = {}

# Inicializar o carregador de widget
widget_loader = FlightWidgetLoader()

@widget_api.route('/widget_search')
def widget_search_page():
    """
    Página que contém o widget Trip.com, usada pelo navegador headless
    """
    session_id = request.args.get('session_id', 'default')
    return render_template('widget_search.html', session_id=session_id)

@widget_api.route('/api/widget/search', methods=['POST'])
def start_widget_search():
    """
    Inicia uma busca de voos usando o widget headless
    
    Parâmetros esperados no JSON:
    - origin: código IATA da origem (ex: 'GRU')
    - destination: código IATA do destino (ex: 'JFK') 
    - departure_date: data de ida (formato: 'YYYY-MM-DD')
    - return_date: data de volta (opcional, formato: 'YYYY-MM-DD')
    - adults: número de adultos (opcional, padrão: 1)
    """
    try:
        # Gerar ID único para esta busca
        search_id = str(uuid.uuid4())
        
        # Obter parâmetros de busca
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Nenhum dado fornecido'
            }), 400
        
        # Validar campos obrigatórios
        required_fields = ['origin', 'destination', 'departure_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Campo obrigatório ausente: {field}'
                }), 400
        
        # Formatar parâmetros para o widget
        travel_params = {
            'origin': data['origin'],
            'destination': data['destination'],
            'departure_date': data['departure_date'],
            'return_date': data.get('return_date', ''),
            'adults': data.get('adults', 1),
            'children': data.get('children', 0),
            'infants': data.get('infants', 0)
        }
        
        # Registrar no cache
        search_cache[search_id] = {
            'status': 'pending',
            'params': travel_params,
            'created_at': datetime.now().isoformat(),
            'results': None
        }
        
        # Iniciar busca em background (em produção, isso seria uma tarefa assíncrona)
        # Para este exemplo, executamos diretamente para simplicidade
        try:
            results = widget_loader.fetch_flights(search_id, travel_params)
            
            # Atualizar o cache com os resultados
            search_cache[search_id]['status'] = 'complete'
            search_cache[search_id]['results'] = results
            search_cache[search_id]['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Busca {search_id} concluída com sucesso")
        except Exception as e:
            search_cache[search_id]['status'] = 'error'
            search_cache[search_id]['error'] = str(e)
            logger.error(f"Erro na busca {search_id}: {str(e)}")
        
        # Responder com o ID da busca para o cliente consultar o status
        return jsonify({
            'status': 'accepted',
            'message': 'Busca iniciada',
            'search_id': search_id
        }), 202
        
    except Exception as e:
        logger.error(f"Erro ao iniciar busca: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@widget_api.route('/api/widget/status/<search_id>', methods=['GET'])
def check_search_status(search_id):
    """
    Verifica o status de uma busca em andamento
    """
    if search_id not in search_cache:
        return jsonify({
            'status': 'error',
            'message': 'Busca não encontrada'
        }), 404
    
    search_data = search_cache[search_id]
    status = search_data['status']
    
    response = {
        'search_id': search_id,
        'status': status
    }
    
    # Se a busca já foi concluída, incluir os resultados
    if status == 'complete':
        response['results'] = search_data['results']
        response['completed_at'] = search_data['completed_at']
    
    # Se houve erro, incluir a mensagem de erro
    if status == 'error':
        response['error'] = search_data.get('error', 'Erro desconhecido')
    
    return jsonify(response)

@widget_api.route('/api/widget/results/<search_id>', methods=['GET'])
def get_search_results(search_id):
    """
    Obtém os resultados de uma busca
    """
    if search_id not in search_cache:
        return jsonify({
            'status': 'error',
            'message': 'Busca não encontrada'
        }), 404
    
    search_data = search_cache[search_id]
    
    if search_data['status'] != 'complete':
        return jsonify({
            'status': search_data['status'],
            'message': 'Busca ainda não foi concluída' if search_data['status'] == 'pending' else 'Busca falhou'
        }), 202 if search_data['status'] == 'pending' else 500
    
    return jsonify({
        'status': 'success',
        'results': search_data['results'],
        'params': search_data['params'],
        'completed_at': search_data['completed_at']
    })
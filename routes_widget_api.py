"""
API para integração direta com TravelPayouts via REST API para o chat AVI
Este módulo fornece endpoints para busca de voos usando a API REST do TravelPayouts
e obtenção de resultados para exibição na interface de chat.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, current_app
from services.travelpayouts_rest_api import travelpayouts_api
from services.travelpayouts_connector import travelpayouts_connector

# Configurar logging
logger = logging.getLogger(__name__)

# Criar Blueprint
widget_api = Blueprint('widget_api', __name__)

# Armazenamento em memória para buscas em andamento
# Na implementação final, utilizar Redis ou outro cache distribuído
active_searches = {}

@widget_api.route('/search', methods=['POST'])
def start_search():
    """
    Inicia uma busca de voos usando a API REST do TravelPayouts.
    
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
        "message": "Busca iniciada com sucesso",
        "results": [...] // resultados já disponíveis imediatamente
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
        
        # Iniciar busca de voos diretamente via API REST (sem browser!)
        logger.info(f"Iniciando busca via API REST: {data.get('origin')} → {data.get('destination')}")
        
        # Executar busca imediatamente (API REST é síncrona)
        try:
            # Buscar voos diretamente via API REST
            flight_results = travelpayouts_api.search_flights(
                origin=data.get('origin'),
                destination=data.get('destination'),
                departure_date=data.get('departure_date'),
                return_date=data.get('return_date'),
                adults=data.get('adults', 1)
            )
            
            # Armazenar resultados
            search_data = {
                'id': search_id,
                'params': data,
                'status': 'complete',  # Já está completo, não precisamos esperar
                'created_at': datetime.utcnow().isoformat(),
                'completed_at': datetime.utcnow().isoformat(),
                'results': flight_results
            }
            active_searches[search_id] = search_data
            
            logger.info(f"Busca concluída: {search_id} - {len(flight_results)} resultados encontrados")
            
            # Retornar ID da busca e resultados imediatamente
            return jsonify({
                'search_id': search_id,
                'message': 'Busca concluída com sucesso',
                'status': 'complete',
                'results_count': len(flight_results),
                'results': flight_results  # Já retornamos os resultados direto!
            })
            
        except Exception as e:
            logger.error(f"Erro na API REST: {str(e)}")
            # Armazenar dados da busca com erro
            search_data = {
                'id': search_id,
                'params': data,
                'status': 'error',
                'created_at': datetime.utcnow().isoformat(),
                'error': str(e),
                'results': []
            }
            active_searches[search_id] = search_data
            
            return jsonify({
                'search_id': search_id,
                'message': f'Erro na busca: {str(e)}',
                'status': 'error'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao processar requisição de busca: {str(e)}")
        return jsonify({
            'error': f'Erro ao iniciar busca: {str(e)}'
        }), 500

@widget_api.route('/status/<search_id>', methods=['GET'])
def check_status(search_id):
    """
    Verifica o status de uma busca.
    Com a API REST, as buscas são sempre síncronas e já retornam resultados imediatos,
    então este endpoint serve apenas para compatibilidade com o código anterior.
    
    Retorna:
    {
        "status": "complete|error",
        "message": "Mensagem de status",
        "progress": 100  // sempre 100% porque a API REST é síncrona
    }
    """
    # Verificar se a busca existe
    if search_id not in active_searches:
        return jsonify({
            'error': 'Busca não encontrada'
        }), 404
    
    # Obter dados da busca (com API REST, já está concluído)
    search_data = active_searches[search_id]
    
    # Com a API REST, o status é sempre "complete" ou "error"
    # Não há estado intermediário, pois a busca é síncrona
    
    # Retornar status atual
    return jsonify({
        'status': search_data['status'],
        'message': search_data.get('message', 'Busca concluída'),
        'progress': 100  # Sempre 100% porque já foi processado
    })

@widget_api.route('/results/<search_id>', methods=['GET'])
def get_results(search_id):
    """
    Obtém os resultados de uma busca concluída.
    Com a API REST, os resultados já foram retornados na chamada /search,
    este endpoint serve apenas para compatibilidade com o código anterior.
    
    Retorna:
    {
        "flights": [
            {
                "id": "TP123456",
                "itineraries": [...],
                "price": {
                    "total": "1234.56",
                    "currency": "BRL"
                },
                "validatingAirlineCodes": ["LA"],
                "source": "TravelPayouts",
                "booking_url": "https://..."
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
    
    # Retornar resultados (que já foram obtidos na chamada /search)
    return jsonify({
        'flights': search_data.get('results', [])
    })

@widget_api.route('/direct_search', methods=['POST'])
def direct_search():
    """
    Endpoint para busca direta de voos usando o conector TravelPayouts.
    Este endpoint é chamado diretamente pelo frontend, sem precisar do
    fluxo de verificação de status.
    
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
        "data": [...],  // array de objetos de voo
        "meta": {
            "origin": "GRU",
            "destination": "JFK",
            "departure_date": "2025-06-01",
            "return_date": "2025-06-15",
            "currency": "BRL",
            "source": "TravelPayouts"
        }
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
        
        # Usar o conector TravelPayouts para buscar voos
        travel_info = {
            'origin': data.get('origin'),
            'destination': data.get('destination'),
            'departure_date': data.get('departure_date'),
            'return_date': data.get('return_date'),
            'adults': data.get('adults', 1)
        }
        
        # Gerar ID para sessão
        session_id = str(uuid.uuid4())
        
        # Buscar voos diretamente
        results = travelpayouts_connector.search_flights_from_chat(travel_info, session_id)
        
        # Retornar resultados
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Erro na busca direta: {str(e)}")
        return jsonify({
            'error': f'Erro na busca: {str(e)}',
            'data': []
        }), 500

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
    
@widget_api.route('/rest-demo', methods=['GET'])
def rest_demo_search():
    """
    Renderiza uma interface de demonstração para testar a API REST do TravelPayouts.
    Esta é uma versão que usa chamadas diretas à API REST sem Playwright.
    """
    return render_template('search_rest_api.html')

@widget_api.route('/travelpayouts-results', methods=['GET'])
def travelpayouts_results_page():
    """
    Renderiza a página de resultados de voos com base nos parâmetros fornecidos.
    Esta página é o destino do botão "Clique aqui para ver suas melhores opções"
    """
    # Parâmetros da URL: origem, destino, data de ida, data de volta (opcional)
    origin = request.args.get('origin', '')
    destination = request.args.get('destination', '')
    departure_date = request.args.get('departure_date', '')
    return_date = request.args.get('return_date', '')
    
    # Validar parâmetros mínimos
    if not origin or not destination or not departure_date:
        return render_template('error.html', 
                              error="Parâmetros insuficientes para busca de voos. Verifique os valores informados.")
    
    # Renderizar a página com widget TravelPayouts
    return render_template('travelpayouts_results.html',
                          origin=origin,
                          destination=destination,
                          departure_date=departure_date,
                          return_date=return_date)

@widget_api.route('/travelpayouts-test', methods=['GET'])
def travelpayouts_test():
    """
    Endpoint de teste para a API REST do TravelPayouts
    """
    try:
        # Definir parâmetros fixos de teste
        origin = request.args.get('origin', 'GRU')
        destination = request.args.get('destination', 'JFK')
        departure_date = request.args.get('departure_date', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
        
        # Buscar resultados via API REST
        results = travelpayouts_api.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date
        )
        
        # Retornar resultados como JSON
        return jsonify({
            "success": True,
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "results_count": len(results),
            "results": results[:5]  # Limitar a 5 para não sobrecarregar a resposta
        })
        
    except Exception as e:
        logger.error(f"Erro no teste TravelPayouts: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
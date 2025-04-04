"""
Rotas para o Roteiro Personalizado
Este módulo contém as rotas necessárias para o recurso de Roteiro Personalizado,
que permite aos usuários criar roteiros de viagem detalhados com voos, hospedagens
e atividades.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, make_response, redirect, url_for
from models import db, TravelPlan, FlightBooking, Accommodation

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar blueprint
roteiro_bp = Blueprint('roteiro', __name__)

# Rotas do Roteiro Personalizado

@roteiro_bp.route('/roteiro-personalizado')
def roteiro_personalizado():
    """Renderiza a página do Roteiro Personalizado"""
    return render_template('roteiro_personalizado.html')

@roteiro_bp.route('/amadeus-results-roteiro')
def amadeus_results_roteiro():
    """
    Renderiza a página de resultados para o Roteiro Personalizado.
    Esta página é uma versão adaptada da página amadeus_results.html,
    com a adição de funcionalidades para adicionar itens ao roteiro.
    """
    # Parâmetros da busca
    origin = request.args.get('origin', '')
    destination = request.args.get('destination', '')
    departure_date = request.args.get('departure_date', '')
    return_date = request.args.get('return_date', '')
    adults = request.args.get('adults', 1)

    return render_template(
        'amadeus_results_roteiro.html',
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=adults
    )

# API para o Roteiro Personalizado

@roteiro_bp.route('/api/roteiro/iniciar', methods=['POST'])
def iniciar_roteiro():
    """
    Inicia um novo roteiro personalizado.
    Retorna um ID único para o roteiro e define um cookie.
    """
    try:
        data = request.json

        # Criar novo roteiro no banco de dados
        roteiro = TravelPlan(
            title=f"Viagem para {data.get('destination', 'Destino')}",
            user_id=data.get('user_id'),  # Se não tiver user_id, será None (usuário não logado)
            destination=data.get('destination'),
            start_date=datetime.strptime(data.get('startDate'), '%Y-%m-%d') if data.get('startDate') else None,
            end_date=datetime.strptime(data.get('endDate'), '%Y-%m-%d') if data.get('endDate') else None,
            budget=data.get('budget'),
            details=json.dumps(data.get('days', [])),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.session.add(roteiro)
        db.session.commit()

        # Configurar resposta com cookie
        response = jsonify({
            'success': True,
            'roteiro_id': roteiro.id,
            'message': 'Roteiro iniciado com sucesso'
        })

        # Definir cookie com ID do roteiro
        response.set_cookie('roteiro_atual_id', str(roteiro.id), max_age=7*24*60*60)  # 7 dias

        return response

    except Exception as e:
        logger.error(f"Erro ao iniciar roteiro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao iniciar roteiro',
            'details': str(e)
        }), 500

@roteiro_bp.route('/api/roteiro/obter', methods=['GET'])
def obter_roteiro():
    """
    Obtém os dados de um roteiro pelo ID.
    O ID pode vir do parâmetro da URL ou do cookie.
    """
    try:
        # Obter ID do roteiro
        roteiro_id = request.args.get('id')
        
        # Se não foi fornecido na URL, tentar obter do cookie
        if not roteiro_id:
            roteiro_id = request.cookies.get('roteiro_atual_id')
        
        # Se ainda não temos ID, retornar erro
        if not roteiro_id:
            return jsonify({
                'success': False,
                'error': 'ID do roteiro não fornecido'
            }), 400
        
        # Buscar roteiro no banco de dados
        roteiro = TravelPlan.query.get(roteiro_id)
        
        # Se roteiro não existe, retornar erro
        if not roteiro:
            return jsonify({
                'success': False,
                'error': 'Roteiro não encontrado'
            }), 404
        
        # Converter para o formato esperado pelo frontend
        roteiro_data = {
            'id': roteiro.id,
            'destination': roteiro.destination,
            'startDate': roteiro.start_date.isoformat() if roteiro.start_date else None,
            'endDate': roteiro.end_date.isoformat() if roteiro.end_date else None,
            'travelers': 1,  # Valor padrão
            'days': json.loads(roteiro.details) if roteiro.details else []
        }
        
        # Buscar voos associados
        flights = FlightBooking.query.filter_by(travel_plan_id=roteiro.id).all()
        if flights:
            # Adicionar voos aos dias apropriados
            for flight in flights:
                # Determinar em qual dia adicionar o voo
                day_index = 0
                if flight.departure_time and roteiro.start_date:
                    flight_date = flight.departure_time.date()
                    start_date = roteiro.start_date.date()
                    day_diff = (flight_date - start_date).days
                    if day_diff >= 0 and day_diff < len(roteiro_data['days']):
                        day_index = day_diff
                
                # Criar bloco de voo
                flight_block = {
                    'id': f'flight_{flight.id}',
                    'type': 'flight',
                    'airline': flight.airline,
                    'flightNumber': flight.flight_number,
                    'departureAirport': flight.departure_location,
                    'arrivalAirport': flight.arrival_location,
                    'departureTime': flight.departure_time.isoformat() if flight.departure_time else None,
                    'arrivalTime': flight.arrival_time.isoformat() if flight.arrival_time else None,
                    'price': flight.price,
                    'currency': flight.currency
                }
                
                # Adicionar ao dia correspondente
                if len(roteiro_data['days']) > day_index:
                    if 'blocks' not in roteiro_data['days'][day_index]:
                        roteiro_data['days'][day_index]['blocks'] = []
                    roteiro_data['days'][day_index]['blocks'].append(flight_block)
        
        # Buscar hospedagens associadas
        accommodations = Accommodation.query.filter_by(travel_plan_id=roteiro.id).all()
        if accommodations:
            for accommodation in accommodations:
                # Determinar em qual dia adicionar a hospedagem
                day_index = 0
                if accommodation.check_in and roteiro.start_date:
                    checkin_date = accommodation.check_in
                    start_date = roteiro.start_date.date()
                    day_diff = (checkin_date - start_date).days
                    if day_diff >= 0 and day_diff < len(roteiro_data['days']):
                        day_index = day_diff
                
                # Criar bloco de hospedagem
                hotel_block = {
                    'id': f'hotel_{accommodation.id}',
                    'type': 'hotel',
                    'name': accommodation.name,
                    'location': accommodation.location,
                    'checkIn': accommodation.check_in.isoformat() if accommodation.check_in else None,
                    'checkOut': accommodation.check_out.isoformat() if accommodation.check_out else None,
                    'pricePerNight': accommodation.price_per_night,
                    'currency': accommodation.currency,
                    'stars': accommodation.stars
                }
                
                # Adicionar ao dia correspondente
                if len(roteiro_data['days']) > day_index:
                    if 'blocks' not in roteiro_data['days'][day_index]:
                        roteiro_data['days'][day_index]['blocks'] = []
                    roteiro_data['days'][day_index]['blocks'].append(hotel_block)
        
        return jsonify({
            'success': True,
            'roteiro': roteiro_data
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter roteiro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter roteiro',
            'details': str(e)
        }), 500

@roteiro_bp.route('/api/roteiro/adicionar-item', methods=['POST'])
def adicionar_item():
    """
    Adiciona um item (voo, hotel, atividade) ao roteiro.
    """
    try:
        data = request.json
        
        # Verificar dados obrigatórios
        if not data.get('roteiro_id'):
            return jsonify({
                'success': False,
                'error': 'ID do roteiro não fornecido'
            }), 400
        
        if not data.get('tipo_item'):
            return jsonify({
                'success': False,
                'error': 'Tipo de item não fornecido'
            }), 400
        
        # Verificar se o roteiro existe
        roteiro = TravelPlan.query.get(data.get('roteiro_id'))
        if not roteiro:
            return jsonify({
                'success': False,
                'error': 'Roteiro não encontrado'
            }), 404
        
        # Adicionar item de acordo com o tipo
        tipo_item = data.get('tipo_item')
        
        if tipo_item == 'voo':
            # Adicionar voo
            voo = FlightBooking(
                travel_plan_id=roteiro.id,
                airline=data.get('airline'),
                flight_number=data.get('flight_number'),
                departure_location=data.get('departure_location'),
                arrival_location=data.get('arrival_location'),
                departure_time=datetime.fromisoformat(data.get('departure_time')) if data.get('departure_time') else None,
                arrival_time=datetime.fromisoformat(data.get('arrival_time')) if data.get('arrival_time') else None,
                price=data.get('price'),
                currency=data.get('currency', 'BRL'),
                booking_status='planned'
            )
            db.session.add(voo)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Voo adicionado com sucesso',
                'item_id': voo.id
            })
            
        elif tipo_item == 'hotel':
            # Adicionar hospedagem
            hotel = Accommodation(
                travel_plan_id=roteiro.id,
                name=data.get('name'),
                location=data.get('location'),
                check_in=datetime.strptime(data.get('check_in'), '%Y-%m-%d').date() if data.get('check_in') else None,
                check_out=datetime.strptime(data.get('check_out'), '%Y-%m-%d').date() if data.get('check_out') else None,
                price_per_night=data.get('price_per_night'),
                currency=data.get('currency', 'BRL'),
                stars=data.get('stars'),
                booking_status='planned'
            )
            db.session.add(hotel)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Hotel adicionado com sucesso',
                'item_id': hotel.id
            })
            
        else:
            return jsonify({
                'success': False,
                'error': f'Tipo de item não suportado: {tipo_item}'
            }), 400
        
    except Exception as e:
        logger.error(f"Erro ao adicionar item ao roteiro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao adicionar item ao roteiro',
            'details': str(e)
        }), 500

@roteiro_bp.route('/api/roteiro/remover-item', methods=['POST'])
def remover_item():
    """
    Remove um item do roteiro.
    """
    try:
        data = request.json
        
        # Verificar dados obrigatórios
        if not data.get('item_id') or not data.get('tipo_item'):
            return jsonify({
                'success': False,
                'error': 'ID do item e tipo não fornecidos'
            }), 400
        
        # Remover item de acordo com o tipo
        tipo_item = data.get('tipo_item')
        item_id = data.get('item_id')
        
        if tipo_item == 'voo':
            # Remover voo
            voo = FlightBooking.query.get(item_id)
            if voo:
                db.session.delete(voo)
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Voo removido com sucesso'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Voo não encontrado'
                }), 404
                
        elif tipo_item == 'hotel':
            # Remover hospedagem
            hotel = Accommodation.query.get(item_id)
            if hotel:
                db.session.delete(hotel)
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Hotel removido com sucesso'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Hotel não encontrado'
                }), 404
                
        else:
            return jsonify({
                'success': False,
                'error': f'Tipo de item não suportado: {tipo_item}'
            }), 400
        
    except Exception as e:
        logger.error(f"Erro ao remover item do roteiro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao remover item do roteiro',
            'details': str(e)
        }), 500

@roteiro_bp.route('/api/roteiro/salvar', methods=['POST'])
def salvar_roteiro():
    """
    Salva ou atualiza um roteiro completo.
    """
    try:
        data = request.json
        
        # Verificar se é um roteiro existente ou novo
        roteiro_id = data.get('id')
        
        if roteiro_id:
            # Atualizar roteiro existente
            roteiro = TravelPlan.query.get(roteiro_id)
            if not roteiro:
                return jsonify({
                    'success': False,
                    'error': 'Roteiro não encontrado'
                }), 404
        else:
            # Criar novo roteiro
            roteiro = TravelPlan(
                user_id=data.get('user_id')  # Pode ser None para usuários não logados
            )
            db.session.add(roteiro)
        
        # Atualizar dados do roteiro
        roteiro.title = f"Viagem para {data.get('destination', 'Destino')}"
        roteiro.destination = data.get('destination')
        roteiro.start_date = datetime.fromisoformat(data.get('startDate')) if data.get('startDate') else None
        roteiro.end_date = datetime.fromisoformat(data.get('endDate')) if data.get('endDate') else None
        roteiro.details = json.dumps(data.get('days', []))
        roteiro.updated_at = datetime.now()
        
        db.session.commit()
        
        # Configurar resposta com cookie
        response = jsonify({
            'success': True,
            'roteiro_id': roteiro.id,
            'message': 'Roteiro salvo com sucesso'
        })
        
        # Definir cookie com ID do roteiro
        response.set_cookie('roteiro_atual_id', str(roteiro.id), max_age=7*24*60*60)  # 7 dias
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao salvar roteiro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao salvar roteiro',
            'details': str(e)
        }), 500

@roteiro_bp.route('/api/roteiro/atualizar', methods=['POST'])
def atualizar_roteiro():
    """
    Atualiza dados de um roteiro existente.
    """
    try:
        data = request.json
        
        # Verificar se o ID do roteiro foi fornecido
        if not data.get('id'):
            return jsonify({
                'success': False,
                'error': 'ID do roteiro não fornecido'
            }), 400
        
        # Buscar roteiro
        roteiro = TravelPlan.query.get(data.get('id'))
        if not roteiro:
            return jsonify({
                'success': False,
                'error': 'Roteiro não encontrado'
            }), 404
        
        # Atualizar campos fornecidos
        if 'destination' in data:
            roteiro.destination = data.get('destination')
            roteiro.title = f"Viagem para {data.get('destination')}"
            
        if 'startDate' in data:
            roteiro.start_date = datetime.fromisoformat(data.get('startDate')) if data.get('startDate') else None
            
        if 'endDate' in data:
            roteiro.end_date = datetime.fromisoformat(data.get('endDate')) if data.get('endDate') else None
            
        if 'days' in data:
            roteiro.details = json.dumps(data.get('days'))
            
        roteiro.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Roteiro atualizado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar roteiro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao atualizar roteiro',
            'details': str(e)
        }), 500
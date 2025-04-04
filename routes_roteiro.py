"""
Rotas para o Roteiro Personalizado
Este módulo contém as rotas necessárias para o recurso de Roteiro Personalizado,
que permite aos usuários criar roteiros de viagem detalhados com voos, hospedagens
e atividades.

O módulo também inclui funções para processamento inteligente do chat da AVI,
permitindo extração de informações e preenchimento automático do roteiro.
"""

import json
import logging
import uuid
import re
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
        
@roteiro_bp.route('/api/roteiro/chat', methods=['POST'])
def roteiro_chat():
    """
    Processa mensagens do chat da AVI e retorna resposta com possíveis atualizações para o roteiro.
    """
    try:
        data = request.json
        message = data.get('message', '').strip()
        roteiro_id = data.get('roteiro_id')
        roteiro_data = data.get('roteiro_data', {})
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Mensagem vazia'
            }), 400
        
        # Processar a mensagem e obter resposta da AVI + atualizações
        response, updates = process_avi_message(message, roteiro_data)
        
        # Se temos um roteiro_id válido e atualizações, salvar no banco de dados
        if roteiro_id and updates:
            try:
                save_updates_to_database(roteiro_id, updates)
            except Exception as e:
                logger.error(f"Erro ao salvar atualizações: {str(e)}")
                # Não falhar a requisição por erro no DB, apenas registrar
        
        return jsonify({
            'success': True,
            'avi_response': response,
            'roteiro_updates': updates
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem do chat: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao processar mensagem',
            'details': str(e)
        }), 500

def process_avi_message(message, roteiro_data):
    """
    Processa a mensagem do usuário e retorna uma resposta da AVI com possíveis atualizações para o roteiro.
    
    Args:
        message: Mensagem do usuário
        roteiro_data: Dados atuais do roteiro
        
    Returns:
        tuple: (resposta da AVI, atualizações para o roteiro)
    """
    from services.amadeus_service import AmadeusService
    
    # Inicializar serviço Amadeus (para buscar voos se necessário)
    amadeus_service = AmadeusService()
    
    # Extrair informações do roteiro atual
    destination = roteiro_data.get('destination', '')
    start_date = roteiro_data.get('startDate')
    end_date = roteiro_data.get('endDate')
    travelers = roteiro_data.get('travelers', 1)
    
    # Inicializar objeto de atualizações
    updates = {}
    
    # Analisar a mensagem para identificar entidades e intenções
    message_lower = message.lower()
    
    # Padrões para extração de informações
    # Destino
    destination_patterns = [
        r'(?:quero|gostaria de|planejo|pretendo|vou|para) (?:ir|viajar|visitar|conhecer) (?:para|a|o|à|ao|em) (.+?)(?:\.|,|\s|$)',
        r'(?:viagem|viajar|visitar|ir|conhecer|férias|turismo) (?:para|a|o|à|ao|em) (.+?)(?:\.|,|\s|$)',
        r'planejo (?:ir|viajar|visitar|conhecer) (.+?)(?:\.|,|\s|$)'
    ]
    
    # Datas
    date_patterns = [
        r'(?:de|dia|data) (\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)',
        r'(\d{1,2}) (?:de|do mês) (\w+)',
        r'(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?',
        r'entre (\d{1,2}\/\d{1,2}) e (\d{1,2}\/\d{1,2})',
        r'entre dia (\d{1,2}) e (\d{1,2})'
    ]
    
    # Número de viajantes
    travelers_patterns = [
        r'(\d+) (?:pessoa|pessoas|viajante|viajantes|adulto|adultos|passageiro|passageiros)',
        r'(?:somos|seremos|vamos) (\d+)',
        r'(?:eu|sozinho|só uma pessoa)',
        r'(?:eu|eu e|com) (?:minha|meu|mais) (\d+)'
    ]
    
    # Verificar se é uma solicitação de busca de destino
    for pattern in destination_patterns:
        matches = re.search(pattern, message_lower)
        if matches:
            potential_destination = matches.group(1).strip()
            if potential_destination and len(potential_destination) > 2:
                updates['destination'] = potential_destination.title()
                break
    
    # Neste ponto, poderíamos utilizar a API GPT para extrair informações de forma mais inteligente,
    # identificar intenções, e até mesmo ter um prompt específico para isso.
    # Por fins de demonstração, vamos implementar uma versão simplificada.
    
    # Determinar o tipo de mensagem/intenção do usuário
    intent = "geral"  # Padrão
    
    if any(word in message_lower for word in ['passag', 'voo', 'avião', 'companhia']):
        intent = "voos"
    elif any(word in message_lower for word in ['hotel', 'hosped', 'acomodaç', 'pousada', 'onde ficar']):
        intent = "hospedagem"
    elif any(word in message_lower for word in ['o que fazer', 'atração', 'atividade', 'passeio', 'visitar']):
        intent = "atrações"
    elif any(word in message_lower for word in ['roteiro', 'itinerário', 'planejar', 'organizar', 'programação']):
        intent = "roteiro"
    elif any(word in message_lower for word in ['busque tudo', 'buscar tudo', 'encontre tudo', 'mostre tudo']):
        intent = "buscar_tudo"
    elif any(word in message_lower for word in ['ajuda', 'ajudar', 'funciona', 'utilizar', 'como', 'não entendi']):
        intent = "ajuda"
    elif any(word in message_lower for word in ['olá', 'oi', 'ei', 'hey', 'boa', 'bom']):
        intent = "saudacao"
    elif any(word in message_lower for word in ['obrigad', 'agradeç', 'valeu', 'perfeito']):
        intent = "agradecimento"
    
    # Gerar resposta da AVI com base na intenção e contexto do roteiro
    response = generate_avi_response(intent, message, updates, roteiro_data)
    
    # Se o usuário está perguntando sobre voos ou busca_tudo, e temos origem e destino, buscar voos
    if (intent in ["voos", "buscar_tudo"]) and destination:
        # Aqui podemos assumir um aeroporto de origem padrão ou extraí-lo da mensagem
        # Por exemplo, usar GRU para São Paulo como padrão
        origin = extract_origin_from_message(message) or "GRU"
        
        # Verificar se temos datas para a busca
        if start_date:
            # Buscar voos na API Amadeus
            try:
                logger.info(f"Buscando voos: {origin} -> {destination}, data: {start_date}")
                flight_results = amadeus_service.search_flights(params={
                    'originLocationCode': origin, 
                    'destinationLocationCode': destination,
                    'departureDate': start_date.split('T')[0] if 'T' in start_date else start_date,
                    'adults': travelers
                })
                
                # Se temos resultados, adicionar às atualizações
                if flight_results and len(flight_results) > 0:
                    # Mapear resultados para o formato de bloco do roteiro
                    flight_blocks = []
                    for flight in flight_results[:3]:  # Mostrar até 3 opções
                        flight_block = map_flight_to_block(flight)
                        if flight_block:
                            flight_blocks.append(flight_block)
                    
                    if flight_blocks:
                        # Adicionar voos às atualizações
                        if 'items' not in updates:
                            updates['items'] = []
                        updates['items'].extend(flight_blocks)
                        
                        # Adicionar mensagem sobre os voos encontrados apenas para intenção voos
                        # Para buscar_tudo já está mencionado na resposta principal
                        if intent == "voos":
                            response += f"\n\nEncontrei {len(flight_blocks)} opções de voos para você e já adicionei ao seu roteiro. Você pode ver os detalhes no painel à direita."
            except Exception as e:
                logger.error(f"Erro ao buscar voos: {str(e)}")
                if intent == "voos":
                    response += "\n\nDesculpe, tive um problema ao buscar voos. Por favor, verifique se o código de aeroporto está correto ou tente novamente mais tarde."
    
    return response, updates

def generate_avi_response(intent, message, updates, roteiro_data):
    """
    Gera resposta da AVI baseada na intenção da mensagem e contexto do roteiro.
    
    Args:
        intent: Intenção identificada na mensagem
        message: Mensagem original do usuário
        updates: Atualizações feitas ou a serem feitas no roteiro
        roteiro_data: Dados atuais do roteiro
        
    Returns:
        string: Resposta da AVI
    """
    # Recuperar informações do roteiro para contextualizar a resposta
    destination = updates.get('destination') or roteiro_data.get('destination')
    start_date = updates.get('startDate') or roteiro_data.get('startDate')
    end_date = updates.get('endDate') or roteiro_data.get('endDate')
    travelers = updates.get('travelers') or roteiro_data.get('travelers', 1)
    
    # Formatar datas para exibição, se disponíveis
    formatted_start_date = None
    formatted_end_date = None
    
    if start_date:
        try:
            if 'T' in start_date:
                start_date = start_date.split('T')[0]
            date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            formatted_start_date = date_obj.strftime('%d/%m/%Y')
        except:
            formatted_start_date = start_date
            
    if end_date:
        try:
            if 'T' in end_date:
                end_date = end_date.split('T')[0]
            date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            formatted_end_date = date_obj.strftime('%d/%m/%Y')
        except:
            formatted_end_date = end_date
    
    # Lista de possíveis respostas para cada intenção
    respostas = {
        "saudacao": [
            f"Olá! Sou a AVI, sua assistente de viagens inteligente. Como posso ajudar com sua viagem{'para ' + destination if destination else ''}?",
            f"Oi! Que bom te ver por aqui. Estou aqui para ajudar com o planejamento da sua viagem{'para ' + destination if destination else ''}.",
            f"Olá! Vamos planejar sua viagem{'para ' + destination if destination else ''}? Conte-me o que você precisa."
        ],
        "voos": [
            f"Vou buscar os melhores voos para {destination}. Você gostaria de partir de qual cidade?",
            f"Para encontrar voos ideais para {destination}, preciso saber: de onde você quer partir e em quais datas?",
            f"Estou pesquisando voos para {destination}. Já definiu a data da viagem?"
        ],
        "hospedagem": [
            f"Posso ajudar a encontrar ótimas hospedagens em {destination}. Tem preferência por hotéis, pousadas ou apartamentos?",
            f"Para sua estadia em {destination}, o que é mais importante: localização, conforto ou economia?",
            f"Que tipo de acomodação você prefere em {destination}? Posso recomendar desde hotéis de luxo até opções mais econômicas."
        ],
        "atrações": [
            f"{destination} tem atrações incríveis! Você prefere atividades culturais, natureza, gastronomia ou vida noturna?",
            f"Em {destination} você encontra muitas opções de lazer. O que mais te interessa conhecer por lá?",
            f"Posso sugerir os melhores pontos turísticos de {destination} baseados nos seus interesses. O que você mais gosta de fazer em viagens?"
        ],
        "roteiro": [
            f"Estou montando seu roteiro para {destination}. Com quantos dias você planeja ficar?",
            f"Para seu roteiro em {destination}, já tem alguma atividade ou lugar específico que não quer deixar de visitar?",
            f"Vamos planejar cada dia em {destination}. Você prefere um roteiro mais intenso ou com tempo livre para relaxar?"
        ],
        "buscar_tudo": [
            f"Perfeito! Vou buscar todas as informações disponíveis para sua viagem para {destination}{' de ' + formatted_start_date + ' a ' + formatted_end_date if formatted_start_date and formatted_end_date else ''}. Estou procurando voos, hospedagens e principais atrações para você!",
            f"Buscando tudo sobre {destination} para você! Encontrarei as melhores opções de voos{' para ' + formatted_start_date if formatted_start_date else ''}, hospedagens e atrações para aproveitar ao máximo sua viagem.",
            f"Estou procurando todas as informações para tornar sua viagem para {destination} perfeita! Já separei algumas opções de voos e estou analisando as melhores hospedagens e atividades."
        ],
        "ajuda": [
            "Estou aqui para ajudar a planejar sua viagem! Você pode me dizer para onde quer ir, e eu ajudo com voos, hospedagem e atrações. Quanto mais detalhes você me der, mais personalizado será o roteiro!",
            "O Roteiro Personalizado permite que você monte sua viagem enquanto conversamos. Me conte seu destino, datas e preferências, e irei sugerindo opções que aparecerão no painel à direita.",
            "Para planejar sua viagem, comece me dizendo seu destino. Em seguida, podemos definir datas, buscar voos, encontrar hospedagens e sugerir atividades para cada dia do seu roteiro."
        ],
        "agradecimento": [
            "Por nada! Estou sempre aqui para ajudar com suas viagens. Se precisar de mais alguma coisa, é só me dizer!",
            "O prazer é meu! Se surgir qualquer dúvida sobre sua viagem, pode contar comigo.",
            "Fico feliz em ajudar! Lembre-se que você pode atualizar seu roteiro a qualquer momento durante nosso planejamento."
        ]
    }
    
    # Seleciona uma resposta aleatória para a intenção detectada
    if intent and intent in respostas:
        import random
        return random.choice(respostas[intent])
    
    # Se não há intenção específica, verificar o contexto para dar uma resposta apropriada
    if 'destination' in updates:  # Se acabamos de descobrir o destino
        return f"Perfeito! Vamos planejar sua viagem para {destination}. Quando você pretende ir? Se já souber, me informe as datas de ida e volta, assim posso buscar as melhores opções para você."
    
    elif destination:  # Se já sabemos o destino, mas é uma conversa geral
        dates_info = ""
        if formatted_start_date and formatted_end_date:
            dates_info = f" de {formatted_start_date} a {formatted_end_date}"
        return f"Estamos planejando sua viagem para {destination}{dates_info}. Em que posso ajudar agora? Posso buscar voos, sugerir hotéis ou recomendar atividades interessantes."
    
    else:  # Conversa bem inicial
        return "Olá! Sou a AVI, sua assistente de viagens inteligente. Para começarmos a planejar sua viagem, me conte: para onde você gostaria de ir?"

def extract_origin_from_message(message):
    """
    Tenta extrair o aeroporto ou cidade de origem da mensagem.
    
    Args:
        message: Mensagem do usuário
        
    Returns:
        string: Código do aeroporto ou None se não identificado
    """
    # Implementação básica com regex - em produção usaria NLP mais avançado
    origin_patterns = [
        r'(?:de|desde|partindo de|saindo de|a partir de) ([A-Z]{3})',  # Busca códigos de aeroporto
        r'(?:de|desde|partindo de|saindo de|a partir de) ([a-zA-ZÀ-ÿ\s]{3,}?)(?:\s|,|\.|\?|$)'  # Busca nomes de cidades
    ]
    
    for pattern in origin_patterns:
        matches = re.search(pattern, message, re.IGNORECASE)
        if matches:
            origin = matches.group(1).strip()
            
            # Se for um código de aeroporto de 3 letras, retornar diretamente
            if len(origin) == 3 and origin.isalpha() and origin.isupper():
                return origin
                
            # Para nomes de cidades, seria necessário um mapeamento cidade -> aeroporto
            # Simplificando para alguns exemplos
            city_to_airport = {
                'são paulo': 'GRU',
                'rio de janeiro': 'GIG',
                'brasília': 'BSB',
                'salvador': 'SSA',
                'recife': 'REC',
                'fortaleza': 'FOR',
                'porto alegre': 'POA',
                'belo horizonte': 'CNF',
                'curitiba': 'CWB',
                'belém': 'BEL',
                'manaus': 'MAO',
                'campinas': 'VCP'
            }
            
            # Verificar se a cidade está no mapeamento
            origin_lower = origin.lower()
            for city, code in city_to_airport.items():
                if city in origin_lower or origin_lower in city:
                    return code
    
    # Se não encontrou nada, retornar None (e usar GRU como default)
    return None

def map_flight_to_block(flight_offer):
    """
    Mapeia uma oferta de voo da API Amadeus para o formato de bloco do roteiro.
    
    Args:
        flight_offer: Oferta de voo da API Amadeus
        
    Returns:
        dict: Bloco de voo formatado para o roteiro
    """
    try:
        # Extrair dados básicos do primeiro segmento de ida
        outbound_segments = flight_offer.get('itineraries', [{}])[0].get('segments', [])
        if not outbound_segments:
            return None
            
        first_segment = outbound_segments[0]
        last_segment = outbound_segments[-1]
        
        # Extrair informações da companhia aérea
        airline_code = first_segment.get('carrierCode', '')
        airline_name = get_airline_name(airline_code) or airline_code
        flight_number = f"{airline_code}{first_segment.get('number', '')}"
        
        # Extrair informações de origem/destino
        departure_iata = first_segment.get('departure', {}).get('iataCode', '')
        arrival_iata = last_segment.get('arrival', {}).get('iataCode', '')
        
        # Extrair datas/horários
        departure_time = first_segment.get('departure', {}).get('at', '')
        arrival_time = last_segment.get('arrival', {}).get('at', '')
        
        # Extrair preço
        price = float(flight_offer.get('price', {}).get('total', 0))
        currency = flight_offer.get('price', {}).get('currency', 'BRL')
        
        # Criar bloco de voo
        return {
            'id': f"flight_{flight_offer.get('id', '')}",
            'type': 'flight',
            'title': f"Voo {airline_name} {flight_number}",
            'airline': airline_name,
            'flightNumber': flight_number,
            'departureAirport': departure_iata,
            'arrivalAirport': arrival_iata,
            'departureTime': departure_time,
            'arrivalTime': arrival_time,
            'price': price,
            'currency': currency,
            'duration': calculate_duration(departure_time, arrival_time),
            'stops': len(outbound_segments) - 1
        }
    except Exception as e:
        logger.error(f"Erro ao mapear voo para bloco: {str(e)}")
        return None

def get_airline_name(airline_code):
    """
    Obtém o nome da companhia aérea a partir do código IATA.
    
    Args:
        airline_code: Código IATA da companhia aérea
        
    Returns:
        string: Nome da companhia aérea ou None se não encontrado
    """
    # Mapeamento simplificado de códigos para nomes de companhias
    airlines = {
        'LA': 'LATAM',
        'G3': 'GOL',
        'AD': 'Azul',
        'AA': 'American Airlines',
        'DL': 'Delta',
        'UA': 'United',
        'BA': 'British Airways',
        'LH': 'Lufthansa',
        'AF': 'Air France',
        'KL': 'KLM',
        'IB': 'Iberia',
        'EK': 'Emirates',
        'QR': 'Qatar Airways',
        'TK': 'Turkish Airlines',
        'AV': 'Avianca'
    }
    
    return airlines.get(airline_code)

def calculate_duration(departure_time, arrival_time):
    """
    Calcula a duração do voo em horas e minutos.
    
    Args:
        departure_time: Data/hora de partida no formato ISO
        arrival_time: Data/hora de chegada no formato ISO
        
    Returns:
        string: Duração no formato "XhYm"
    """
    try:
        from datetime import datetime
        
        # Converter strings para objetos datetime
        departure_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
        arrival_dt = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
        
        # Calcular diferença
        delta = arrival_dt - departure_dt
        total_minutes = delta.total_seconds() / 60
        
        # Formatar como horas e minutos
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        
        return f"{hours}h{minutes:02d}m"
    except Exception:
        return "N/A"  # Em caso de erro

def save_updates_to_database(roteiro_id, updates):
    """
    Salva as atualizações do roteiro no banco de dados.
    
    Args:
        roteiro_id: ID do roteiro
        updates: Dicionário com as atualizações
    """
    try:
        # Verificar se o roteiro existe
        roteiro = TravelPlan.query.get(roteiro_id)
        if not roteiro:
            logger.error(f"Roteiro não encontrado: {roteiro_id}")
            return
        
        # Atualizar campos básicos
        if 'destination' in updates:
            roteiro.destination = updates['destination']
            roteiro.title = f"Viagem para {updates['destination']}"
        
        if 'startDate' in updates and updates['startDate']:
            roteiro.start_date = datetime.fromisoformat(updates['startDate'].replace('Z', '+00:00'))
        
        if 'endDate' in updates and updates['endDate']:
            roteiro.end_date = datetime.fromisoformat(updates['endDate'].replace('Z', '+00:00'))
        
        # Se há items para adicionar (voos, hotéis, etc.)
        if 'items' in updates and updates['items']:
            # Carregar detalhes atuais
            current_details = json.loads(roteiro.details) if roteiro.details else []
            
            # Para cada item, adicionar ao dia apropriado
            for item in updates['items']:
                if item['type'] == 'flight':
                    # Salvar como FlightBooking no banco de dados
                    flight = FlightBooking(
                        travel_plan_id=roteiro.id,
                        airline=item.get('airline', ''),
                        flight_number=item.get('flightNumber', ''),
                        departure_location=item.get('departureAirport', ''),
                        arrival_location=item.get('arrivalAirport', ''),
                        departure_time=datetime.fromisoformat(item['departureTime'].replace('Z', '+00:00')) if item.get('departureTime') else None,
                        arrival_time=datetime.fromisoformat(item['arrivalTime'].replace('Z', '+00:00')) if item.get('arrivalTime') else None,
                        price=item.get('price', 0),
                        currency=item.get('currency', 'BRL'),
                        booking_status='planned'
                    )
                    db.session.add(flight)
                
                elif item['type'] == 'hotel':
                    # Salvar como Accommodation no banco de dados
                    hotel = Accommodation(
                        travel_plan_id=roteiro.id,
                        name=item.get('name', ''),
                        location=item.get('location', ''),
                        check_in=datetime.strptime(item['checkIn'], '%Y-%m-%d').date() if item.get('checkIn') else None,
                        check_out=datetime.strptime(item['checkOut'], '%Y-%m-%d').date() if item.get('checkOut') else None,
                        price_per_night=item.get('pricePerNight', 0),
                        currency=item.get('currency', 'BRL'),
                        stars=item.get('stars', 3),
                        booking_status='planned'
                    )
                    db.session.add(hotel)
        
        # Atualizar data de modificação
        roteiro.updated_at = datetime.now()
        
        # Salvar alterações
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Erro ao salvar atualizações no banco de dados: {str(e)}")
        db.session.rollback()
        raise
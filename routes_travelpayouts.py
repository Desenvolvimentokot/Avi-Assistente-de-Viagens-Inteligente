"""
Rotas para integração com a API TravelPayouts
"""

from flask import Blueprint, jsonify, request, render_template, redirect, url_for, session
from services.travelpayouts_service import TravelPayoutsService
import logging

logger = logging.getLogger(__name__)

# Criar Blueprint para as rotas do TravelPayouts
travelpayouts_bp = Blueprint('travelpayouts', __name__)

# Instanciar o serviço
travelpayouts_service = TravelPayoutsService()

@travelpayouts_bp.route('/search', methods=['GET', 'POST'])
def search_flights():
    """
    Busca voos usando a API do TravelPayouts.
    
    Se for uma requisição GET, exibe o formulário de busca.
    Se for uma requisição POST, realiza a busca e exibe os resultados.
    """
    if request.method == 'POST':
        # Obter parâmetros da requisição
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        departure_date = request.form.get('departure_date')
        return_date = request.form.get('return_date')
        
        # Validar parâmetros
        if not origin or not destination or not departure_date:
            return render_template('travelpayouts_search.html', error='Origem, destino e data de partida são obrigatórios')
        
        # Formatar parâmetros para o serviço
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': 1
        }
        
        if return_date:
            params['returnDate'] = return_date
        
        # Buscar voos
        try:
            results = travelpayouts_service.search_flights(params)
            
            # Salvar resultados na sessão para uso posterior
            session['flight_results'] = results
            
            # Renderizar template com resultados
            return render_template('travelpayouts_results.html', 
                                  flights=results, 
                                  origin=origin, 
                                  destination=destination,
                                  departure_date=departure_date,
                                  return_date=return_date)
        except Exception as e:
            logger.error(f"Erro ao buscar voos: {str(e)}")
            return render_template('travelpayouts_search.html', 
                                  error=f'Erro ao buscar voos: {str(e)}')
    
    # Caso seja uma requisição GET, mostrar formulário de busca
    return render_template('travelpayouts_search.html')

@travelpayouts_bp.route('/api/flights', methods=['POST'])
def api_search_flights():
    """
    Endpoint da API para busca de voos. Retorna os resultados em formato JSON.
    """
    # Obter parâmetros JSON
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    # Extrair parâmetros
    origin = data.get('origin')
    destination = data.get('destination')
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    
    # Validar parâmetros
    if not origin or not destination or not departure_date:
        return jsonify({'error': 'Origem, destino e data de partida são obrigatórios'}), 400
    
    # Formatar parâmetros para o serviço
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': departure_date,
        'adults': 1
    }
    
    if return_date:
        params['returnDate'] = return_date
    
    # Buscar voos
    try:
        results = travelpayouts_service.search_flights(params)
        return jsonify({'flights': results})
    except Exception as e:
        logger.error(f"Erro na API de busca de voos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@travelpayouts_bp.route('/api/best-prices', methods=['GET'])
def api_best_prices():
    """
    Endpoint da API para busca dos melhores preços de voos.
    """
    # Obter parâmetros
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    month = request.args.get('month')  # Formato YYYY-MM
    
    # Validar parâmetros
    if not origin or not destination:
        return jsonify({'error': 'Origem e destino são obrigatórios'}), 400
    
    # Buscar melhores preços
    try:
        results = travelpayouts_service.search_best_prices(origin, destination, month)
        return jsonify({'prices': results})
    except Exception as e:
        logger.error(f"Erro na API de melhores preços: {str(e)}")
        return jsonify({'error': str(e)}), 500

@travelpayouts_bp.route('/redirect', methods=['GET'])
def redirect_to_partner():
    """
    Redireciona para o site de parceiro do TravelPayouts para busca de voos.
    """
    # Obter parâmetros
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    departure_date = request.args.get('departure_date')
    return_date = request.args.get('return_date')
    
    # Validar parâmetros
    if not origin or not destination:
        return render_template('travelpayouts_search.html', error='Origem e destino são obrigatórios')
    
    # Gerar link de redirecionamento
    try:
        redirect_url = travelpayouts_service.get_partner_link(origin, destination, departure_date, return_date)
        return redirect(redirect_url)
    except Exception as e:
        logger.error(f"Erro ao gerar link de redirecionamento: {str(e)}")
        return render_template('travelpayouts_search.html', error=f'Erro ao redirecionar: {str(e)}')

# Rota para o widget de busca (incorporado na página)
@travelpayouts_bp.route('/widget', methods=['GET'])
def widget():
    """
    Renderiza uma página com o widget de busca do TravelPayouts incorporado.
    """
    return render_template('travelpayouts_widget.html')

# Rota de teste para TravelPayouts API
@travelpayouts_bp.route('/api/test', methods=['GET'])
def api_test():
    """
    Endpoint para testar a API do TravelPayouts.
    Retorna dados reais de voos para uso na integração com Trip.com.
    """
    # Obter parâmetros da query
    origin = request.args.get('origin', 'GRU')
    destination = request.args.get('destination', 'JFK')
    
    # Calcular data padrão (30 dias a partir de hoje)
    from datetime import datetime, timedelta
    default_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    departure_date = request.args.get('departure_date', default_date)
    return_date = request.args.get('return_date')
    adults = int(request.args.get('adults', '1'))
    
    logger.info(f"Teste de API TravelPayouts: {origin} → {destination}, {departure_date}")
    
    # Formatar parâmetros para o serviço
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': departure_date,
        'adults': adults
    }
    
    if return_date:
        params['returnDate'] = return_date
    
    # Buscar voos
    try:
        results = travelpayouts_service.search_flights(params)
        
        # Formatar resultados para compatibilidade com a integração Trip.com
        formatted_results = []
        for flight in results:
            formatted_results.append({
                'id': flight.get('id', ''),
                'airline': flight.get('airline', 'Companhia Aérea'),
                'price': float(flight.get('price', 0)),
                'duration': flight.get('duration_to', ''),
                'departure_time': flight.get('departure_at', ''),
                'arrival_time': flight.get('arrival_at', ''),
                'stops': flight.get('transfers', 0),
                'flight_number': flight.get('flight_number', ''),
                'url': flight.get('url', ''),
                'source': 'TravelPayouts API'
            })
        
        return jsonify({
            'success': True,
            'message': 'Dados reais de voos obtidos com sucesso',
            'data': formatted_results
        })
    except Exception as e:
        logger.error(f"Erro no teste da API TravelPayouts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar dados reais de voos'
        }), 500

# Rota para integração com roteiro personalizado
@travelpayouts_bp.route('/roteiro/search', methods=['POST'])
def roteiro_search():
    """
    Endpoint para busca de voos a partir do roteiro personalizado.
    Retorna os resultados em formato JSON para integração com o frontend.
    """
    # Obter parâmetros JSON
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    # Extrair parâmetros
    origin = data.get('origin')
    destination = data.get('destination')
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    
    # Validar parâmetros
    if not origin or not destination or not departure_date:
        return jsonify({'error': 'Origem, destino e data de partida são obrigatórios'}), 400
    
    # Formatar parâmetros para o serviço
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': departure_date,
        'adults': data.get('adults', 1)
    }
    
    if return_date:
        params['returnDate'] = return_date
    
    # Buscar voos
    try:
        results = travelpayouts_service.search_flights(params)
        return jsonify({
            'success': True,
            'flights': results,
            'redirect_url': travelpayouts_service.get_partner_link(origin, destination, departure_date, return_date)
        })
    except Exception as e:
        logger.error(f"Erro na API de busca de voos para roteiro: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'redirect_url': travelpayouts_service.get_partner_link(origin, destination, departure_date, return_date)
        })
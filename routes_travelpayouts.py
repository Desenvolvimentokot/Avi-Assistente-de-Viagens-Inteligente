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
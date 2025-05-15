"""
Rotas diretas para testar a API da Amadeus
Este módulo fornece acesso direto à API da Amadeus sem depender
do fluxo completo de conversação.
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, render_template
from amadeus import Client, ResponseError

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar o blueprint
amadeus_test_bp = Blueprint('amadeus_test', __name__)

# Inicializar cliente Amadeus
amadeus = Client(
    client_id=os.environ.get('AMADEUS_API_KEY'),
    client_secret=os.environ.get('AMADEUS_API_SECRET')
)

# Variáveis globais para cache
token_info = {
    'access_token': None,
    'expires_at': None
}

# Rota da página principal de teste
@amadeus_test_bp.route('/amadeus-test')
def test_page():
    """Renderiza a página de teste da API Amadeus"""
    return render_template('amadeus_test.html')

# Verificar status da API
@amadeus_test_bp.route('/api/amadeus/check', methods=['GET'])
def check_api_status():
    """Verifica se a API Amadeus está acessível e as credenciais são válidas"""
    try:
        # Tentar obter um token de autenticação
        token = get_token()
        if token:
            return jsonify({'status': 'success', 'message': 'API Amadeus está conectada e funcionando'})
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Falha ao obter token de autenticação da API Amadeus'
            })
    except Exception as e:
        logger.error(f"Erro ao verificar status da API: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': f'Erro ao verificar API: {str(e)}'
        })

# Rota para buscar informações de voos
@amadeus_test_bp.route('/api/amadeus/flights', methods=['POST'])
def search_flights():
    """Busca ofertas de voos na API Amadeus"""
    try:
        data = request.json
        
        # Validar parâmetros obrigatórios
        required_params = ['originLocationCode', 'destinationLocationCode', 'departureDate', 'adults']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Parâmetro obrigatório ausente: {param}'})
        
        # Logs detalhados da requisição
        logger.info(f"Buscando voos com os parâmetros: {data}")
        
        # Realizar a busca usando o SDK
        try:
            # Preparar parâmetros
            search_params = {
                'originLocationCode': data['originLocationCode'],
                'destinationLocationCode': data['destinationLocationCode'],
                'departureDate': data['departureDate'],
                'adults': data['adults'],
                'max': 20  # Número máximo de resultados
            }
            
            # Adicionar data de retorno se fornecida
            if 'returnDate' in data and data['returnDate']:
                search_params['returnDate'] = data['returnDate']
            
            # Adicionar moeda se fornecida
            if 'currencyCode' in data and data['currencyCode']:
                search_params['currencyCode'] = data['currencyCode']
            
            # Fazer a requisição ao SDK
            flight_offers = amadeus.shopping.flight_offers_search.get(**search_params)
            
            # Converter resultado para JSON e retornar
            return jsonify({
                'data': flight_offers.data,
                'meta': flight_offers.meta if hasattr(flight_offers, 'meta') else {},
                'success': True
            })
        
        except ResponseError as error:
            logger.error(f"Erro na resposta do SDK Amadeus: {error}")
            return jsonify({
                'error': f'Erro na API Amadeus: {str(error)}',
                'code': getattr(error, 'code', 'unknown'),
                'status': getattr(error, 'status', 500)
            })
        
        except Exception as e:
            logger.error(f"Erro ao usar SDK Amadeus: {str(e)}")
            # Tentar abordagem alternativa com API REST direta
            return search_flights_direct(data)
            
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'})

# Função para buscar voos diretamente via REST API
def search_flights_direct(data):
    """Função alternativa para buscar voos usando a API REST diretamente"""
    try:
        # Obter token
        token = get_token()
        if not token:
            return jsonify({'error': 'Não foi possível obter token de autenticação'})
        
        # Preparar a URL e headers
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Preparar parâmetros
        params = {
            'originLocationCode': data['originLocationCode'],
            'destinationLocationCode': data['destinationLocationCode'],
            'departureDate': data['departureDate'],
            'adults': data['adults'],
            'max': 20
        }
        
        # Adicionar data de retorno se fornecida
        if 'returnDate' in data and data['returnDate']:
            params['returnDate'] = data['returnDate']
        
        # Adicionar moeda se fornecida
        if 'currencyCode' in data and data['currencyCode']:
            params['currencyCode'] = data['currencyCode']
        
        # Fazer a requisição
        response = requests.get(url, headers=headers, params=params)
        
        # Verificar se a requisição foi bem sucedida
        if response.status_code == 200:
            return jsonify({
                'data': response.json().get('data', []),
                'meta': response.json().get('meta', {}),
                'success': True
            })
        else:
            logger.error(f"Erro na API REST: {response.status_code} - {response.text}")
            return jsonify({
                'error': f'Erro na API REST: {response.status_code}',
                'details': response.text
            })
    
    except Exception as e:
        logger.error(f"Erro na abordagem REST: {str(e)}")
        return jsonify({'error': f'Erro ao buscar voos: {str(e)}'})

# Rota para buscar melhores preços
@amadeus_test_bp.route('/api/amadeus/best-prices', methods=['POST'])
def search_best_prices():
    """Busca os melhores preços disponíveis para voos em um período"""
    try:
        data = request.json
        
        # Validar parâmetros obrigatórios
        required_params = ['originLocationCode', 'destinationLocationCode', 'departureDate', 'returnDate']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Parâmetro obrigatório ausente: {param}'})
        
        # Parâmetros opcionais
        max_dates = int(data.get('max_dates_to_check', 3))
        adults = int(data.get('adults', 1))
        currency = data.get('currencyCode', 'BRL')
        
        # Logs da requisição
        logger.info(f"Buscando melhores preços para: {data}")
        
        # Preparar datas para verificação
        start_date = datetime.strptime(data['departureDate'], '%Y-%m-%d')
        end_date = datetime.strptime(data['returnDate'], '%Y-%m-%d')
        date_range = (end_date - start_date).days + 1
        
        # Limitar o número de datas para não sobrecarregar a API
        if date_range > 15:
            date_range = 15
        
        # Verificar se o range é maior que max_dates
        if date_range > max_dates:
            # Selecionar max_dates datas distribuídas no período
            step = date_range // max_dates
            dates_to_check = [start_date + timedelta(days=i*step) for i in range(max_dates)]
        else:
            # Verificar todas as datas no range
            dates_to_check = [start_date + timedelta(days=i) for i in range(date_range)]
        
        # Formatar as datas para o formato correto
        formatted_dates = [d.strftime('%Y-%m-%d') for d in dates_to_check]
        
        # Array para armazenar os resultados
        best_prices = []
        
        # Token para autenticação
        token = get_token()
        if not token:
            return jsonify({'error': 'Não foi possível obter token de autenticação'})
        
        # Para cada data, fazer uma busca
        for departure_date in formatted_dates:
            try:
                # Preparar URL e headers
                url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                # Preparar parâmetros
                params = {
                    'originLocationCode': data['originLocationCode'],
                    'destinationLocationCode': data['destinationLocationCode'],
                    'departureDate': departure_date,
                    'adults': adults,
                    'currencyCode': currency,
                    'max': 5  # Limitamos para não sobrecarregar
                }
                
                # Fazer a requisição
                response = requests.get(url, headers=headers, params=params)
                
                # Verificar se a requisição foi bem sucedida
                if response.status_code == 200:
                    # Extrair os dados relevantes
                    flight_data = response.json()
                    offers = flight_data.get('data', [])
                    
                    if offers:
                        # Pegar o melhor preço para esta data
                        best_offer = min(offers, key=lambda x: float(x.get('price', {}).get('total', '999999')))
                        
                        # Adicionar à lista de melhores preços
                        best_prices.append({
                            'date': departure_date,
                            'price': float(best_offer.get('price', {}).get('total', 0)),
                            'currency': best_offer.get('price', {}).get('currency', currency),
                            'origin': data['originLocationCode'],
                            'destination': data['destinationLocationCode'],
                            'offer_id': best_offer.get('id')
                        })
                
                # Adicionar pequeno delay para não sobrecarregar a API
                import time
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Erro ao buscar preço para data {departure_date}: {str(e)}")
                # Continuar para a próxima data mesmo se houver erro
        
        # Ordenar os preços do menor para o maior
        best_prices.sort(key=lambda x: x['price'])
        
        # Retornar os resultados
        return jsonify({
            'best_prices': best_prices,
            'origin': data['originLocationCode'],
            'destination': data['destinationLocationCode'],
            'dates_checked': formatted_dates,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar melhores preços: {str(e)}")
        return jsonify({'error': f'Erro ao buscar melhores preços: {str(e)}'})

# Rota para obter token da API
@amadeus_test_bp.route('/api/amadeus/token', methods=['POST'])
def api_get_token():
    """Obtém ou atualiza o token de autenticação da API Amadeus"""
    try:
        token = get_token(force_refresh=True)
        if token:
            return jsonify({
                'access_token': token,
                'expires_in': get_token_expiry(),
                'success': True
            })
        else:
            return jsonify({'error': 'Não foi possível obter token de autenticação'})
    except Exception as e:
        logger.error(f"Erro ao obter token: {str(e)}")
        return jsonify({'error': f'Erro ao obter token: {str(e)}'})

# Função para obter token da API Amadeus
def get_token(force_refresh=False):
    """
    Obtém um token de autenticação da API Amadeus
    Se já tiver um token válido, retorna ele, a menos que force_refresh=True
    """
    global token_info
    
    # Verificar se já temos um token válido
    now = datetime.now()
    if not force_refresh and token_info['access_token'] and token_info['expires_at'] and now < token_info['expires_at']:
        logger.info("Usando token em cache")
        return token_info['access_token']
    
    try:
        # Obter novo token
        logger.info("Solicitando novo token")
        api_key = os.environ.get('AMADEUS_API_KEY')
        api_secret = os.environ.get('AMADEUS_API_SECRET')
        
        if not api_key or not api_secret:
            logger.error("API Key ou Secret não configurados")
            return None
        
        # Usar o método tradicional de obter token
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': api_key,
            'client_secret': api_secret
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            token_info['access_token'] = token_data['access_token']
            # Calcular quando o token expira
            expires_in = token_data['expires_in']
            token_info['expires_at'] = now + timedelta(seconds=expires_in - 60)  # Subtrair 1 minuto para segurança
            
            logger.info(f"Novo token obtido, válido por {expires_in} segundos")
            return token_info['access_token']
        else:
            logger.error(f"Erro ao obter token: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Exceção ao obter token: {str(e)}")
        return None

# Função para calcular tempo restante do token
def get_token_expiry():
    """Retorna o tempo restante de validade do token em segundos"""
    global token_info
    
    if token_info['expires_at']:
        now = datetime.now()
        if now < token_info['expires_at']:
            return int((token_info['expires_at'] - now).total_seconds())
    
    return 0
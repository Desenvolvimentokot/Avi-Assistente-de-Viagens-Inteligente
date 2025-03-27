
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from datetime import datetime, timedelta
import json
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar a aplicação Flask
app = Flask(__name__)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///flai.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave_secreta_temporaria')

# Inicializar o SQLAlchemy
db = SQLAlchemy(app)

# Importar os serviços após a inicialização da aplicação
from services.amadeus_service import AmadeusService
try:
    from services.openai_service import OpenAIService
except ImportError:
    logger.warning("OpenAIService não disponível")
    OpenAIService = None

try:
    from services.busca_rapida_service import BuscaRapidaService
except ImportError:
    logger.warning("BuscaRapidaService não disponível")
    BuscaRapidaService = None

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Rota para buscar voos usando a API Amadeus
@app.route('/api/search-flights', methods=['GET'])
def search_flights():
    try:
        # Obter parâmetros da requisição
        origin = request.args.get('origin', 'MAD')  # Código do aeroporto de origem (padrão: Madrid)
        destination = request.args.get('destination', 'BCN')  # Código do aeroporto de destino (padrão: Barcelona)
        departure_date = request.args.get('departure_date', '2025-04-18')  # Data de partida
        return_date = request.args.get('return_date', '2025-04-28')  # Data de retorno
        adults = request.args.get('adults', 1, type=int)  # Número de adultos
        
        # Inicializar o serviço Amadeus
        amadeus_service = AmadeusService()
        
        # Buscar ofertas de voos
        flight_offers = amadeus_service.search_flight_offers(
            origin, 
            destination, 
            departure_date, 
            return_date, 
            adults
        )
        
        return jsonify(flight_offers)
    
    except Exception as e:
        logger.error(f"Erro ao buscar voos: {str(e)}")
        return jsonify({"error": f"Erro ao buscar voos: {str(e)}"}), 500

# Tratamento de erros
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Adicione mais rotas conforme necessário

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

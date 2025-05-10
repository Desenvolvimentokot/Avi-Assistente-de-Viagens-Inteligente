
import logging
from flask import Flask
from app import app
from routes_roteiro import roteiro_bp
from routes_travelpayouts import travelpayouts_bp
from routes_widget_api import widget_api
from routes_hidden_search import hidden_search_bp
from routes_chat_flight_search import chat_flight_search_bp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Registrar blueprints
app.register_blueprint(roteiro_bp)
app.register_blueprint(travelpayouts_bp, url_prefix='/travelpayouts')
app.register_blueprint(widget_api, url_prefix='/widget')
app.register_blueprint(hidden_search_bp)
app.register_blueprint(chat_flight_search_bp)

# Adicionar log de inicialização
logger.info("Aplicação inicializada com TravelPayouts, Roteiro Personalizado, Widget API e Busca Invisível")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

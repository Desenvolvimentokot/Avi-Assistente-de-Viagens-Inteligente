
import logging
from flask import Flask
from app import app
from routes_roteiro import roteiro_bp
from routes_travelpayouts import travelpayouts_bp
from routes_widget_api import widget_api

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Registrar blueprints
app.register_blueprint(roteiro_bp)
app.register_blueprint(travelpayouts_bp, url_prefix='/travelpayouts')
app.register_blueprint(widget_api, url_prefix='/widget')

# Adicionar log de inicialização
logger.info("Aplicação inicializada com TravelPayouts, Roteiro Personalizado e Widget API")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


import logging
from flask import Flask
from app import app
from routes_amadeus_test import amadeus_test_bp
from routes_roteiro import roteiro_bp
from routes_travelpayouts import travelpayouts_bp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Registrar blueprints
app.register_blueprint(amadeus_test_bp)
app.register_blueprint(roteiro_bp)
app.register_blueprint(travelpayouts_bp, url_prefix='/travelpayouts')

# Adicionar log de inicialização
logger.info("Aplicação inicializada com API Amadeus, TravelPayouts e Roteiro Personalizado")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

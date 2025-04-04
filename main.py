
import logging
from flask import Flask
from app import app
from routes_amadeus_test import amadeus_test_bp
from routes_roteiro import roteiro_bp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Registrar blueprints
app.register_blueprint(amadeus_test_bp)
app.register_blueprint(roteiro_bp)

# Adicionar log de inicialização
logger.info("Aplicação inicializada com API Amadeus e Roteiro Personalizado")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

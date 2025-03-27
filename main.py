
# Importar a aplicação Flask do módulo app
from app import app

if __name__ == "__main__":
    # Iniciar o servidor Flask
    app.run(host="0.0.0.0", port=5000, debug=True)

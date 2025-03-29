
#!/usr/bin/env python3
import requests
import json
import logging
import uuid
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_flight_results_api():
    """Testa a API de resultados de voo com dados simulados"""
    # Gerar uma sessão de teste
    session_id = str(uuid.uuid4())
    logger.info(f"Usando session_id de teste: {session_id}")
    
    # URL da API
    base_url = "http://localhost:5000"  # Altere para a URL adequada se necessário
    api_url = f"{base_url}/api/flight_results/{session_id}"
    
    # Dados de teste para a sessão
    test_data = {
        "travel_info": {
            "origin": "GRU",
            "destination": "MIA",
            "departure_date": "2025-05-01",
            "return_date": "2025-05-10",
            "adults": 1
        }
    }
    
    # Primeiro, armazenar os dados na sessão
    logger.info("Criando sessão de teste no servidor...")
    session_url = f"{base_url}/api/test/create_session"
    try:
        response = requests.post(
            session_url, 
            json={"session_id": session_id, "data": test_data}
        )
        response.raise_for_status()
        logger.info(f"Sessão criada: {response.json()}")
    except Exception as e:
        logger.error(f"Erro ao criar sessão: {str(e)}")
        return
    
    # Agora, testar a API de resultados
    logger.info(f"Testando API em: {api_url}")
    try:
        response = requests.get(api_url)
        logger.info(f"Status code: {response.status_code}")
        
        # Verificar se a resposta é válida
        if response.status_code == 200:
            data = response.json()
            logger.info("Resposta recebida com sucesso!")
            
            # Verificar se há erro na resposta
            if "error" in data:
                logger.error(f"Erro na resposta: {data['error']}")
                if "details" in data:
                    logger.error(f"Detalhes: {data['details']}")
            else:
                # Verificar o formato dos dados
                if "data" in data and isinstance(data["data"], list):
                    logger.info(f"Resultados de voos recebidos: {len(data['data'])} itens")
                    if data["data"]:
                        logger.info(f"Primeiro resultado: {json.dumps(data['data'][0], indent=2)}")
                elif "best_prices" in data and isinstance(data["best_prices"], list):
                    logger.info(f"Melhores preços recebidos: {len(data['best_prices'])} itens")
                    if data["best_prices"]:
                        logger.info(f"Melhor preço: {json.dumps(data['best_prices'][0], indent=2)}")
                else:
                    logger.warning("Formato de resposta inesperado")
                    logger.info(f"Resposta completa: {json.dumps(data, indent=2)}")
        else:
            logger.error(f"Erro na requisição: {response.text}")
    
    except Exception as e:
        logger.error(f"Erro ao testar API: {str(e)}")

if __name__ == "__main__":
    test_flight_results_api()

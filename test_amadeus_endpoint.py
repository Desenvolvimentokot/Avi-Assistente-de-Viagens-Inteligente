import logging
import requests
import sys
import os
import json
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_amadeus_endpoint():
    """Teste do endpoint /amadeus-test para verificar a conexão direta com a API Amadeus"""
    logger.info("=== TESTANDO ENDPOINT /AMADEUS-TEST ===")

    try:
        # URL base da aplicação
        base_url = "http://localhost:5000"

        # Endpoint de teste para Amadeus
        endpoint = "/amadeus-test"

        logger.info(f"Testando o endpoint {endpoint}")

        # Fazer requisição ao endpoint
        response = requests.get(f"{base_url}{endpoint}")

        # Verificar resposta
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ TESTE DO ENDPOINT BEM-SUCEDIDO!")
            logger.info(f"Resposta: {json.dumps(data, indent=2)}")

            # Verificar se há dados de voos
            if 'data' in data and len(data['data']) > 0:
                logger.info(f"Encontrados {len(data['data'])} resultados de voo")
                return True
            else:
                logger.warning("Resposta recebida, mas sem dados de voos")
                return False
        else:
            logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Erro na requisição: {str(e)}")
        return False

def test_flight_search_api():
    """
    Testa a busca direta de voos pela API, verificando se a URL está correta
    """
    try:
        # Definir uma URL base para o ambiente local
        base_url = "http://localhost:5000"
        
        # Parâmetros para busca de teste
        search_params = {
            "origin": "GRU",
            "destination": "MIA",
            "departure_date": "2025-06-15",
            "return_date": "2025-06-21",
            "adults": 1
        }
        
        # Fazer a requisição para busca direta
        search_url = f"{base_url}/api/flight_search"
        logger.info(f"Testando busca direta: {search_url}")
        
        response = requests.post(search_url, json=search_params)
        
        # Verificar resposta
        if response.status_code != 200:
            logger.error(f"Falha na busca direta: {response.status_code} - {response.text}")
            return False
            
        # Verificar se contém resultados ou session_id
        result = response.json()
        if "session_id" in result:
            logger.info(f"✅ Busca direta bem-sucedida. Session ID: {result['session_id']}")
            
            # Usar o session_id para buscar resultados
            session_id = result["session_id"]
            results_url = f"{base_url}/api/flight_results/{session_id}"
            
            # Esperar um pouco para garantir que os resultados foram processados
            time.sleep(2)
            
            # Buscar os resultados
            logger.info(f"Buscando resultados para session_id: {session_id}")
            results_response = requests.get(results_url)
            
            if results_response.status_code == 200:
                results = results_response.json()
                if "data" in results and len(results["data"]) > 0:
                    logger.info(f"✅ Resultados encontrados: {len(results['data'])} voos")
                    return True
                else:
                    logger.warning("⚠️ Nenhum resultado encontrado")
            else:
                logger.error(f"❌ Falha ao buscar resultados: {results_response.status_code} - {results_response.text}")
        
        logger.error("❌ Session ID não encontrado na resposta")
        return False
            
    except Exception as e:
        logger.error(f"Erro ao testar busca de voos: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== TESTANDO ENDPOINT AMADEUS ===")
    
    # Testar autenticação
    auth_success = test_amadeus_endpoint()
    
    if auth_success:
        # Testar busca
        logger.info("=== TESTANDO BUSCA DE VOOS ===")
        search_success = test_flight_search_api()
        
        if search_success:
            logger.info("✅ TESTE COMPLETO: Autenticação e busca funcionando corretamente")
        else:
            logger.error("❌ TESTE FALHOU: Busca não está funcionando corretamente")
    else:
        logger.error("❌ TESTE FALHOU: Autenticação não está funcionando")
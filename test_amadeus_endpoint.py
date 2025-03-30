
import requests
import logging
import time
import json
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_amadeus_endpoint():
    """
    Testa o endpoint /amadeus-test para verificar conexão direta com a API Amadeus
    """
    try:
        # Definir uma URL base para o ambiente local
        base_url = "http://localhost:5000"
        
        # Testar conexão ao endpoint de teste do Amadeus
        amadeus_url = f"{base_url}/amadeus-test"
        logger.info(f"Testando endpoint de autenticação Amadeus: {amadeus_url}")
        
        response = requests.get(amadeus_url)
        
        # Verificar resposta
        if response.status_code != 200:
            logger.error(f"Falha ao conectar ao endpoint: {response.status_code} - {response.text}")
            return False
            
        logger.info(f"Resposta do endpoint Amadeus: {response.text[:200]}...")
        
        # Verificar se contém token
        if "token_type" in response.text and "access_token" in response.text:
            logger.info("✅ Autenticação com API Amadeus bem-sucedida")
            return True
        else:
            logger.error("❌ Falha na autenticação com API Amadeus")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao testar endpoint Amadeus: {str(e)}")
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

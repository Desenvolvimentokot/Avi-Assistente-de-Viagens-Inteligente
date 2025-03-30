
import requests
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_amadeus_endpoint():
    """
    Testa o endpoint /amadeus-test para verificar se está usando o FlightServiceConnector
    """
    logger.info("Testando o endpoint /amadeus-test")
    
    # Fazer a requisição direta para o endpoint de teste
    response = requests.get("http://localhost:5000/amadeus-test")
    
    if response.status_code != 200:
        logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
        return False
    
    # Exibir o conteúdo da resposta
    logger.info(f"Resposta do endpoint de teste: {response.text[:200]}...")
    
    # Verificar se a resposta contém indicadores de sucesso
    success_indicators = ["voos encontrados", "FlightServiceConnector", "Amadeus"]
    for indicator in success_indicators:
        if indicator.lower() in response.text.lower():
            logger.info(f"Indicador de sucesso encontrado: '{indicator}'")
        else:
            logger.warning(f"Indicador de sucesso não encontrado: '{indicator}'")
    
    logger.info("Teste do endpoint /amadeus-test concluído")
    return True

if __name__ == "__main__":
    logger.info("=== TESTANDO ENDPOINT /AMADEUS-TEST ===")
    success = test_amadeus_endpoint()
    
    if success:
        logger.info("✅ TESTE DO ENDPOINT PASSOU!")
    else:
        logger.error("❌ TESTE DO ENDPOINT FALHOU!")

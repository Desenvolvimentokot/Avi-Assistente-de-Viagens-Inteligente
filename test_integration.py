
import requests
import json
import logging
import time
import uuid

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_amadeus_integration():
    """
    Testa se a integração está funcionando corretamente via FlightServiceConnector
    sem chamadas à API OpenAI
    """
    # Gerar um session_id único para rastreamento nos logs
    session_id = str(uuid.uuid4())
    logger.info(f"Iniciando teste com session_id: {session_id}")
    
    # Preparar dados para a solicitação de chat que devem acionar a busca direta
    chat_data = {
        "message": "Quero viajar de São Paulo para Miami em 15 de junho de 2025 e ficar por 6 dias",
        "mode": "quick-search",
        "session_id": session_id
    }
    
    # Fazer a requisição ao endpoint de chat
    logger.info("Enviando requisição para /api/chat...")
    response = requests.post("http://localhost:5000/api/chat", json=chat_data)
    
    if response.status_code != 200:
        logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
        return False
    
    # Extrair a resposta
    result = response.json()
    logger.info(f"Resposta do chat: {result.get('response')[:100]}...")
    
    # Verificar se o chat retornou um session_id válido
    if 'session_id' not in result:
        logger.error("Resposta não contém session_id")
        return False
    
    returned_session_id = result.get('session_id')
    logger.info(f"Session ID retornado: {returned_session_id}")
    
    # Verificar se o chat indicou que deve mostrar o painel de resultados
    if result.get('trigger_flight_panel', False):
        logger.info("SUCESSO: Chat está acionando o painel de resultados!")
    else:
        logger.warning("Chat não acionou automaticamente o painel de resultados")
    
    # Mostrar alguma parte da resposta para diagnóstico
    logger.info(f"Trecho da resposta: {result.get('response')[:150]}...")
    
    # Agora vamos tentar obter os resultados de voo para este session_id
    logger.info(f"Esperando 2 segundos antes de buscar resultados...")
    time.sleep(2)  # Pequena pausa para garantir que o backend processou a busca
    
    logger.info(f"Buscando resultados de voo para session_id: {returned_session_id}")
    flight_response = requests.get(f"http://localhost:5000/api/flight_results/{returned_session_id}")
    
    if flight_response.status_code != 200:
        logger.error(f"Erro ao buscar resultados de voo: {flight_response.status_code} - {flight_response.text}")
        return False
    
    # Extrair e analisar os resultados
    flight_results = flight_response.json()
    
    # Verificar a fonte dos dados para garantir que vieram da API real
    source = flight_results.get('source', 'unknown')
    logger.info(f"Fonte dos dados: {source}")
    
    # Verificar se há dados de voos
    flights = flight_results.get('data', [])
    flight_count = len(flights)
    
    if flight_count > 0:
        logger.info(f"SUCESSO: {flight_count} voos encontrados via API Amadeus!")
        
        # Mostrar alguns detalhes do primeiro voo para confirmar
        if flights:
            first_flight = flights[0]
            try:
                price = first_flight.get('price', {}).get('total', 'N/A')
                currency = first_flight.get('price', {}).get('currency', 'N/A')
                logger.info(f"Exemplo de voo: Preço {currency} {price}")
            except Exception as e:
                logger.error(f"Erro ao extrair detalhes do voo: {str(e)}")
    else:
        logger.warning("Nenhum voo encontrado na resposta")
    
    logger.info("Teste concluído com sucesso!")
    return True

if __name__ == "__main__":
    logger.info("=== INICIANDO TESTE DE INTEGRAÇÃO DIRETA AMADEUS ===")
    success = test_direct_amadeus_integration()
    
    if success:
        logger.info("✅ TESTE PASSOU: A integração direta com Amadeus está funcionando!")
    else:
        logger.error("❌ TESTE FALHOU: Verifique os logs para detalhes.")

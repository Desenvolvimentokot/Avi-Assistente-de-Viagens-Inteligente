
import logging
import requests
import sys
import os
import json
import uuid
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_direct_amadeus_integration():
    """Teste de integração direta com a API Amadeus através do chat"""
    logger.info("=== INICIANDO TESTE DE INTEGRAÇÃO DIRETA AMADEUS ===")
    
    try:
        # URL base da aplicação
        base_url = "http://localhost:5000"
        
        # Gerar um session_id para o teste
        session_id = str(uuid.uuid4())
        logger.info(f"Iniciando teste com session_id: {session_id}")
        
        # Preparar mensagem de busca de voo com dados de teste
        chat_message = {
            "message": "Quero viajar de São Paulo para Miami em 10 de abril de 2025",
            "session_id": session_id,
            "mode": "quick-search",
            "history": []
        }
        
        # Passo 1: Enviar mensagem inicial para o chat
        logger.info(f"Enviando requisição para /api/chat...")
        chat_response = requests.post(
            f"{base_url}/api/chat",
            json=chat_message
        )
        
        if chat_response.status_code != 200:
            logger.error(f"Erro na resposta do chat: {chat_response.status_code} - {chat_response.text}")
            return False
        
        # Processar resposta do chat
        chat_data = chat_response.json()
        chat_text = chat_data.get("response", "")
        returned_session_id = chat_data.get("session_id")
        
        logger.info(f"Resposta do chat: {chat_text[:100]}...")
        logger.info(f"Session ID retornado: {returned_session_id}")
        
        # Verificar se o session_id foi retornado corretamente
        if not returned_session_id or returned_session_id != session_id:
            logger.warning(f"Session ID não corresponde: enviado={session_id}, recebido={returned_session_id}")
        
        # Verificar se o painel de resultados foi acionado
        if chat_data.get("show_flight_results", False):
            logger.info("Chat acionou automaticamente o painel de resultados ✅")
        else:
            logger.warning("Chat não acionou automaticamente o painel de resultados")
        
        # Extrair trecho da resposta para verificação
        if len(chat_text) > 100:
            logger.info(f"Trecho da resposta: {chat_text[:200]}...")
        
        # Passo 2: Simular confirmação da busca
        logger.info("Esperando 2 segundos antes de buscar resultados...")
        import time
        time.sleep(2)
        
        # Passo 3: Buscar resultados de voo diretamente
        logger.info(f"Buscando resultados de voo para session_id: {returned_session_id}")
        flight_response = requests.get(
            f"{base_url}/api/flight_results/{returned_session_id}"
        )
        
        if flight_response.status_code != 200:
            logger.error(f"Erro ao buscar resultados de voo: {flight_response.status_code} - {flight_response.text}")
            logger.error("❌ TESTE FALHOU: Verifique os logs para detalhes.")
            return False
        
        # Processar resposta dos resultados de voo
        flight_data = flight_response.json()
        
        # Verificar se há erro na resposta
        if 'error' in flight_data and flight_data['error']:
            logger.error(f"Erro nos resultados de voo: {flight_data['error']}")
            logger.error("❌ TESTE FALHOU: Verifique os logs para detalhes.")
            return False
        
        # Verificar se há resultados
        flight_count = len(flight_data.get('data', []))
        if flight_count > 0:
            logger.info(f"✅ TESTE BEM-SUCEDIDO: {flight_count} voos encontrados")
            logger.info(f"Fonte dos dados: {flight_data.get('source', 'não especificada')}")
            
            # Verificar preço do primeiro voo
            if flight_count > 0 and 'price' in flight_data['data'][0]:
                first_price = flight_data['data'][0]['price']['total']
                currency = flight_data['data'][0]['price']['currency']
                logger.info(f"Preço do primeiro voo: {currency} {first_price}")
            
            return True
        else:
            logger.warning("Resposta bem-sucedida, mas sem dados de voos")
            logger.error("❌ TESTE FALHOU: Nenhum resultado de voo encontrado")
            return False
            
    except Exception as e:
        logger.error(f"Erro durante o teste de integração: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("❌ TESTE FALHOU: Exceção durante a execução")
        return False

if __name__ == "__main__":
    success = test_direct_amadeus_integration()
    sys.exit(0 if success else 1)

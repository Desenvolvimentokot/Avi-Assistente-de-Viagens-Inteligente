#!/usr/bin/env python3
"""
Teste de autenticação com a API Amadeus usando o token bearer
"""
import logging
import sys
from services.amadeus_sdk_service import AmadeusSDKService

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_amadeus_auth')

def test_auth_token():
    """Testa obtenção de token de autenticação"""
    logger.info("=== TESTE DE AUTENTICAÇÃO COM API AMADEUS ===")
    
    try:
        # Inicializar serviço
        service = AmadeusSDKService()
        
        # Obter token
        token = service.get_auth_token()
        
        if token:
            logger.info(f"✅ TOKEN OBTIDO COM SUCESSO: {token[:10]}...{token[-10:]}")
            logger.info(f"Válido até: {service.token_expiry}")
            return True
        else:
            logger.error("❌ FALHA AO OBTER TOKEN")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERRO NO TESTE: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_auth_token()
    sys.exit(0 if success else 1)
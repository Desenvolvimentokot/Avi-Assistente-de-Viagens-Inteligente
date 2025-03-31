#!/usr/bin/env python3
"""
Teste de integração do fluxo de chat com a API Amadeus
"""

import logging
import os
import json
import sys
import uuid

from services.chat_processor import ChatProcessor
from services.flight_service_connector import flight_service_connector

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_integration')

def test_chat_flow():
    """
    Testa o fluxo completo de chat para extração de informações e busca de voos reais
    """
    logger.info("=== TESTE DE INTEGRAÇÃO DO FLUXO DE CHAT PARA BUSCA DE VOOS ===")
    
    try:
        # 1. Iniciar o chat processor
        logger.info("Inicializando chat processor...")
        chat_processor = ChatProcessor()
        
        # 2. Gerar um ID de conversa simulado
        conversation_id = str(uuid.uuid4())
        logger.info(f"ID de conversa: {conversation_id}")
        
        # 3. Enviar mensagem de usuário simulada
        user_message = "Oi, preciso viajar de São Paulo para Miami no dia 30 de abril de 2025"
        logger.info(f"Mensagem do usuário: '{user_message}'")
        
        # 4. Processar a mensagem
        logger.info("Processando mensagem...")
        response = chat_processor.process_message(
            message=user_message,
            user_id=1,  # ID simulado
            conversation_id=conversation_id
        )
        
        # 5. Mostrar resultados
        logger.info(f"Resposta recebida: {json.dumps(response, indent=2)}")
        
        # 6. Verificar se temos show_flight_results
        if response.get('show_flight_results', False):
            logger.info("✅ Painel de voos será mostrado")
            logger.info(f"Mensagem para o painel: '{response.get('message', '')}'")
            
            # 7. Buscar resultados diretamente pelo conector
            logger.info(f"Buscando resultados de voos para a sessão {conversation_id}")
            
            # Extrair as informações da viagem
            travel_info = {
                'origin': 'GRU',  # São Paulo - Guarulhos
                'destination': 'MIA',  # Miami
                'departure_date': '2025-04-30'
            }
            
            # Fazer a busca direta
            results = flight_service_connector.search_flights_from_chat(
                travel_info=travel_info,
                session_id=conversation_id
            )
            
            if 'error' in results:
                logger.error(f"❌ Erro na busca: {results['error']}")
                return False
            
            flight_count = len(results.get('data', []))
            logger.info(f"✅ {flight_count} voos encontrados")
            
            if flight_count > 0:
                logger.info("Mostrando resumo dos 3 primeiros voos:")
                for i, flight in enumerate(results['data'][:3]):
                    price = flight.get('price', {}).get('total', 'N/A')
                    currency = flight.get('price', {}).get('currency', 'N/A')
                    logger.info(f"Voo {i+1}: Preço {currency} {price}")
                    
                    # Mostrar itinerários
                    for j, itinerary in enumerate(flight.get('itineraries', [])):
                        for k, segment in enumerate(itinerary.get('segments', [])):
                            departure = segment.get('departure', {})
                            arrival = segment.get('arrival', {})
                            carrier = segment.get('carrierCode', 'N/A')
                            flight_number = segment.get('number', 'N/A')
                            
                            logger.info(f"  Segmento {j+1}.{k+1}: {carrier}{flight_number} - " +
                                    f"{departure.get('iataCode', 'N/A')} → {arrival.get('iataCode', 'N/A')}")
            
            return flight_count > 0
        else:
            logger.warning("⚠️ Painel de voos não será mostrado")
            logger.info(f"Resposta do bot: '{response.get('message', '')}'")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERRO NO TESTE: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_chat_flow()
    sys.exit(0 if success else 1)
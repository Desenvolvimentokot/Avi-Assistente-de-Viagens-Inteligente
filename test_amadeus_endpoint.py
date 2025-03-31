#!/usr/bin/env python3
"""
Teste de conexão direta com endpoints da API Amadeus usando o formato correto V2
"""
import os
import json
import logging
import requests
import sys
from datetime import datetime, timedelta
from services.amadeus_sdk_service import AmadeusSDKService

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_amadeus_endpoint')

def test_flight_search():
    """Testa a busca de voos usando o formato correto da API V2"""
    logger.info("=== TESTE DE BUSCA DE VOOS COM API AMADEUS V2 ===")
    
    try:
        # 1. Obter token de autenticação
        service = AmadeusSDKService()
        token = service.get_auth_token()
        
        if not token:
            logger.error("❌ FALHA AO OBTER TOKEN DE AUTENTICAÇÃO")
            return False
            
        logger.info("✅ Token de autenticação obtido com sucesso")
        
        # 2. Preparar o corpo da requisição no formato V2
        request_body = {
            "currencyCode": "BRL",
            "originDestinations": [
                {
                    "id": "1",
                    "originLocationCode": "GRU",
                    "destinationLocationCode": "MIA",
                    "departureDateTimeRange": {
                        "date": "2025-04-30"
                    }
                }
            ],
            "travelers": [
                {
                    "id": "1",
                    "travelerType": "ADULT"
                }
            ],
            "sources": ["GDS"],
            "searchCriteria": {
                "maxFlightOffers": 20,
                "flightFilters": {
                    "cabinRestrictions": [
                        {
                            "cabin": "ECONOMY",
                            "coverage": "MOST_SEGMENTS",
                            "originDestinationIds": ["1"]
                        }
                    ]
                }
            }
        }
        
        # 3. Enviar a requisição
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Enviando requisição para: {url}")
        logger.info(f"Corpo da requisição: {json.dumps(request_body, indent=2)}")
        
        start_time = datetime.now()
        response = requests.post(
            url,
            headers=headers,
            json=request_body,
            timeout=30
        )
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        # 4. Processar a resposta
        logger.info(f"Resposta recebida em {elapsed_time:.2f} segundos - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            flight_count = len(result.get('data', []))
            logger.info(f"✅ SUCESSO! {flight_count} voos encontrados")
            
            # Imprimir algumas informações sobre os voos encontrados
            if flight_count > 0:
                for i, flight in enumerate(result['data'][:3]):  # Mostrar apenas os 3 primeiros
                    price = flight.get('price', {}).get('total', 'N/A')
                    currency = flight.get('price', {}).get('currency', 'N/A')
                    logger.info(f"Voo {i+1}: Preço {currency} {price}")
                    
                    # Obter detalhes dos segmentos
                    for j, itinerary in enumerate(flight.get('itineraries', [])):
                        for k, segment in enumerate(itinerary.get('segments', [])):
                            departure = segment.get('departure', {})
                            arrival = segment.get('arrival', {})
                            carrier = segment.get('carrierCode', 'N/A')
                            flight_number = segment.get('number', 'N/A')
                            
                            logger.info(f"  Segmento {j+1}.{k+1}: {carrier}{flight_number} - " +
                                       f"{departure.get('iataCode', 'N/A')} → {arrival.get('iataCode', 'N/A')}")
            
            return True
        else:
            logger.error(f"❌ ERRO NA REQUISIÇÃO: {response.status_code}")
            logger.error(f"Detalhes: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERRO NO TESTE: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_flight_search()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
import os
import json
from datetime import datetime, timedelta
from amadeus import Client, ResponseError

"""
Script de teste usando o SDK oficial da Amadeus.
Este script tenta buscar ofertas de voos usando a API Flight Offers Search.
"""

# Configurar logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('amadeus_sdk_test')

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, '='))
    print("="*80 + "\n")

def test_flight_search():
    """Testa a busca de voos usando o SDK oficial da Amadeus"""
    print_section("TESTE DE BUSCA DE VOOS COM SDK OFICIAL")
    
    # Obter credenciais das variáveis de ambiente
    api_key = os.environ.get('AMADEUS_API_KEY')
    api_secret = os.environ.get('AMADEUS_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("Credenciais da API não estão configuradas nas variáveis de ambiente")
        print("❌ ERRO: Variáveis de ambiente AMADEUS_API_KEY e/ou AMADEUS_API_SECRET não estão configuradas.")
        return
    
    # Configuração do SDK
    print("Configurando cliente Amadeus SDK...")
    amadeus = Client(
        client_id=api_key,
        client_secret=api_secret,
        logger=logger
    )
    
    # Definir parâmetros de busca
    tomorrow = datetime.now() + timedelta(days=1)
    return_date = tomorrow + timedelta(days=7)
    
    params = {
        'originLocationCode': 'GRU',
        'destinationLocationCode': 'CDG',
        'departureDate': tomorrow.strftime('%Y-%m-%d'),
        'returnDate': return_date.strftime('%Y-%m-%d'),
        'adults': 1,
        'max': 5
    }
    
    print(f"Parâmetros de busca:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    print("\nEnviando requisição via SDK oficial...")
    
    try:
        # Realizar a busca de voos
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=params['originLocationCode'],
            destinationLocationCode=params['destinationLocationCode'],
            departureDate=params['departureDate'],
            returnDate=params['returnDate'],
            adults=params['adults'],
            max=params['max']
        )
        
        # Verificar resposta bem-sucedida
        print(f"\n✅ Busca bem-sucedida!")
        print(f"Código de status: {response.status_code}")
        print(f"Total de ofertas: {len(response.data)} voos encontrados")
        
        # Exibir detalhes das 2 primeiras ofertas
        if response.data:
            for i, offer in enumerate(response.data[:2], 1):
                print(f"\nOferta {i}:")
                print(f"  ID: {offer['id']}")
                
                if 'price' in offer:
                    price = offer['price']
                    print(f"  Preço: {price.get('total')} {price.get('currency', '')}")
                
                if 'itineraries' in offer:
                    for j, itinerary in enumerate(offer['itineraries'], 1):
                        print(f"  Itinerário {j}:")
                        
                        for k, segment in enumerate(itinerary.get('segments', []), 1):
                            print(f"    Segmento {k}:")
                            
                            departure = segment.get('departure', {})
                            print(f"      Origem: {departure.get('iataCode')} - {departure.get('at')}")
                            
                            arrival = segment.get('arrival', {})
                            print(f"      Destino: {arrival.get('iataCode')} - {arrival.get('at')}")
        
    except ResponseError as error:
        print(f"\n❌ Erro na busca de voos")
        print(f"Código de status: {error.response.status_code}")
        
        # Extrair informações detalhadas do erro
        errors = error.response.result.get('errors', [])
        for err in errors:
            print(f"  Erro: {err.get('title', 'Erro desconhecido')}")
            print(f"  Detalhes: {err.get('detail', '')}")
            
            # Verificar se é erro de permissão
            if error.response.status_code == 401:
                if any('apiproduct' in str(err) for err in errors):
                    print("\n🔑 PROBLEMA DE PERMISSÃO DETECTADO:")
                    print("  Este erro indica que sua conta Amadeus não tem permissão para acessar a API Flight Offers Search.")
                    print("  Você precisa atualizar sua assinatura Amadeus para incluir acesso a este endpoint.")
                    print("  Entre em contato com a Amadeus ou acesse o portal de desenvolvedores para fazer upgrade do seu plano.")
            
            # Verificar detalhes do erro
            source = err.get('source', {})
            if source:
                if 'parameter' in source:
                    print(f"  Parâmetro: {source['parameter']}")
                if 'example' in source:
                    print(f"  Exemplo correto: {source['example']}")
        
        # Exibir resposta completa para diagnóstico
        print("\nResposta completa do erro:")
        print(json.dumps(error.response.result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")

if __name__ == "__main__":
    test_flight_search()
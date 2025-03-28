#!/usr/bin/env python3
import os
import json
from datetime import datetime, timedelta
from services.amadeus_service_sdk import AmadeusService

"""
Script para testar o serviço Amadeus implementado com o SDK oficial
"""

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, '='))
    print("="*80 + "\n")

def test_connection():
    """Testa a conexão com a API Amadeus usando o serviço"""
    print_section("TESTE DE CONEXÃO COM A API AMADEUS")
    
    service = AmadeusService()
    result = service.test_connection()
    
    print(f"Status: {result['status']}")
    print(f"Mensagem: {result['message']}")
    
    if result['details']:
        print("\nDetalhes:")
        for key, value in result['details'].items():
            print(f"  {key}: {value}")
    
    return result['status'] == 'success'

def test_flight_search():
    """Testa a busca de voos"""
    print_section("TESTE DE BUSCA DE VOOS")
    
    service = AmadeusService()
    
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
    
    print("\nExecutando busca...")
    result = service.search_flights(params)
    
    print(f"\nStatus: {result['status']}")
    print(f"Mensagem: {result['message']}")
    
    if result['status'] == 'success' and result['data']:
        print(f"\nResultados encontrados: {len(result['data'])} voos")
        
        # Exibir detalhes dos 2 primeiros voos
        for i, offer in enumerate(result['data'][:2], 1):
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
    elif result['status'] == 'error':
        print("\nErro na busca de voos:")
        if 'error_details' in result:
            details = result['error_details']
            print(f"  Código de status: {details.get('status_code')}")
            print(f"  Detalhes: {details.get('error_detail')}")
    
    return result['status'] == 'success'

def test_flight_price():
    """Testa a verificação de preço de um voo"""
    print_section("TESTE DE VERIFICAÇÃO DE PREÇO DE VOO")
    
    service = AmadeusService()
    
    # Primeiro, buscar uma oferta para usar no teste
    tomorrow = datetime.now() + timedelta(days=1)
    
    search_params = {
        'originLocationCode': 'GRU',
        'destinationLocationCode': 'CDG',
        'departureDate': tomorrow.strftime('%Y-%m-%d'),
        'adults': 1,
        'max': 1
    }
    
    search_result = service.search_flights(search_params)
    
    if search_result['status'] != 'success' or not search_result['data']:
        print("❌ Não foi possível obter uma oferta de voo para testar o preço")
        return False
    
    # Usar a primeira oferta para verificar o preço
    flight_offer = search_result['data'][0]
    
    print(f"Verificando preço da oferta ID: {flight_offer['id']}")
    print(f"Origem-Destino: {flight_offer['itineraries'][0]['segments'][0]['departure']['iataCode']} - {flight_offer['itineraries'][0]['segments'][-1]['arrival']['iataCode']}")
    
    price_result = service.get_flight_price(flight_offer)
    
    print(f"\nStatus: {price_result['status']}")
    print(f"Mensagem: {price_result['message']}")
    
    if price_result['status'] == 'success' and price_result['data']:
        flight_offers = price_result['data'].get('flightOffers', [])
        
        if flight_offers:
            offer = flight_offers[0]
            print("\nDetalhes do preço verificado:")
            
            if 'price' in offer:
                price = offer['price']
                print(f"  Total: {price.get('total')} {price.get('currency', '')}")
                print(f"  Base: {price.get('base', '')}")
                
                if 'fees' in price:
                    print("  Taxas:")
                    for fee in price['fees']:
                        print(f"    {fee.get('type', '')}: {fee.get('amount', '')}")
    
    return price_result['status'] == 'success'

def main():
    """Função principal para executar todos os testes"""
    print_section("TESTES DO SERVIÇO AMADEUS COM SDK OFICIAL")
    
    results = []
    
    # Teste 1: Conexão com a API
    print("\n[Teste 1/3] Testando conexão com a API Amadeus...")
    connection_success = test_connection()
    results.append(("Conexão com a API", connection_success))
    
    # Se a conexão falhou, não executar os outros testes
    if not connection_success:
        print("\n❌ A conexão com a API falhou. Não será possível executar os outros testes.")
        return
    
    # Teste 2: Busca de voos
    print("\n[Teste 2/3] Testando busca de voos...")
    flight_search_success = test_flight_search()
    results.append(("Busca de voos", flight_search_success))
    
    # Teste 3: Verificação de preço
    print("\n[Teste 3/3] Testando verificação de preço...")
    price_check_success = test_flight_price()
    results.append(("Verificação de preço", price_check_success))
    
    # Resumo dos resultados
    print_section("RESUMO DOS RESULTADOS")
    
    for name, success in results:
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"{status}: {name}")
    
    total_success = sum(1 for _, success in results if success)
    print(f"\nTestes bem-sucedidos: {total_success}/{len(results)}")
    
    if total_success == len(results):
        print("\n🎉 Todos os testes foram bem-sucedidos! O serviço Amadeus está funcionando corretamente.")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os detalhes acima.")

if __name__ == "__main__":
    main()
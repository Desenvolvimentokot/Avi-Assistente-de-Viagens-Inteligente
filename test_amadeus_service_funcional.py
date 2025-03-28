#!/usr/bin/env python3
import os
import json
import time
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('amadeus_funcional')

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, '='))
    print("="*80 + "\n")

def test_flight_search():
    """Testa a funcionalidade de busca de voos"""
    print_section("TESTE DE BUSCA DE VOOS")
    
    from services.amadeus_service import AmadeusService
    
    # Instanciar o serviço
    service = AmadeusService()
    
    # Definir parâmetros de busca realistas
    tomorrow = datetime.now() + timedelta(days=1)
    return_date = tomorrow + timedelta(days=7)
    
    params = {
        'origin': 'GRU',               # São Paulo - Guarulhos
        'destination': 'CDG',          # Paris - Charles de Gaulle
        'departure_date': tomorrow.strftime('%Y-%m-%d'),
        'return_date': return_date.strftime('%Y-%m-%d'),
        'adults': 1,
        'max': 3,
        'currency': 'BRL'
    }
    
    print(f"Parâmetros de busca:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    # Medir tempo de resposta
    start_time = time.time()
    
    # Executar a busca
    print("\nExecutando busca de voos...")
    result = service.search_flights(params)
    
    # Calcular tempo de resposta
    response_time = time.time() - start_time
    print(f"Tempo de resposta: {response_time:.2f} segundos")
    
    # Verificar resultado
    if 'error' in result:
        print(f"❌ Erro na busca: {result['error']}")
        return False, None
    
    if 'data' in result and result['data']:
        flights = result['data']
        print(f"✅ Busca bem-sucedida: {len(flights)} voos encontrados")
        
        # Mostrar amostra dos resultados
        if flights:
            print("\nAmostra do primeiro resultado:")
            first_flight = flights[0]
            
            # Extrair informações básicas
            try:
                flight_id = first_flight.get('id', 'N/A')
                price = first_flight.get('price', {}).get('total', 'N/A')
                currency = first_flight.get('price', {}).get('currency', 'N/A')
                
                # Obter informações do itinerário
                itineraries = first_flight.get('itineraries', [])
                segments_count = sum(len(it.get('segments', [])) for it in itineraries)
                
                print(f"  ID: {flight_id}")
                print(f"  Preço: {price} {currency}")
                print(f"  Itinerários: {len(itineraries)}")
                print(f"  Total de segmentos: {segments_count}")
                
                # Se existe um segmento, mostrar detalhes da primeira partida
                if itineraries and itineraries[0].get('segments'):
                    first_segment = itineraries[0]['segments'][0]
                    departure = first_segment.get('departure', {})
                    arrival = first_segment.get('arrival', {})
                    carrier = first_segment.get('carrierCode', 'N/A')
                    
                    print(f"  Primeiro voo:")
                    print(f"    De: {departure.get('iataCode', 'N/A')} em {departure.get('at', 'N/A')}")
                    print(f"    Para: {arrival.get('iataCode', 'N/A')} em {arrival.get('at', 'N/A')}")
                    print(f"    Companhia: {carrier}")
            except Exception as e:
                print(f"Erro ao processar detalhes do voo: {str(e)}")
        
        return True, flights[0] if flights else None
    else:
        print("❌ Nenhum voo encontrado na busca")
        return False, None

def test_flight_price(flight_offer):
    """Testa a verificação de preço de um voo"""
    if not flight_offer:
        print("Não há oferta de voo para testar preço.")
        return False
    
    print_section("TESTE DE VERIFICAÇÃO DE PREÇO")
    
    from services.amadeus_service import AmadeusService
    
    # Instanciar o serviço
    service = AmadeusService()
    
    print("Verificando preço para a oferta encontrada...")
    
    # Medir tempo de resposta
    start_time = time.time()
    
    # Executar a verificação de preço
    result = service.get_flight_price(flight_offer)
    
    # Calcular tempo de resposta
    response_time = time.time() - start_time
    print(f"Tempo de resposta: {response_time:.2f} segundos")
    
    # Verificar resultado
    if 'error' in result:
        print(f"❌ Erro na verificação de preço: {result['error']}")
        return False
    
    if 'data' in result:
        print(f"✅ Verificação de preço bem-sucedida")
        
        # Mostrar informações básicas do preço
        try:
            flight_offers = result['data'].get('flightOffers', [])
            if flight_offers:
                offer = flight_offers[0]
                price = offer.get('price', {})
                print(f"  Preço total: {price.get('total', 'N/A')} {price.get('currency', 'N/A')}")
                
                # Mostrar detalhes de taxas se disponíveis
                if 'fees' in price:
                    print(f"  Taxas:")
                    for fee in price['fees']:
                        print(f"    {fee.get('type', 'N/A')}: {fee.get('amount', 'N/A')}")
        except Exception as e:
            print(f"Erro ao processar detalhes do preço: {str(e)}")
        
        return True
    else:
        print("❌ Nenhum dado de preço retornado")
        return False

def main():
    """Função principal para executar os testes"""
    print_section("TESTES FUNCIONAIS DO SERVIÇO AMADEUS (IMPLEMENTAÇÃO SDK)")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar variáveis de ambiente
    print("\nVerificando configuração:")
    api_key = os.environ.get('AMADEUS_API_KEY')
    api_secret = os.environ.get('AMADEUS_API_SECRET')
    print(f"  AMADEUS_API_KEY: {'✅ Configurada' if api_key else '❌ Não configurada'}")
    print(f"  AMADEUS_API_SECRET: {'✅ Configurada' if api_secret else '❌ Não configurada'}")
    
    if not api_key or not api_secret:
        print("\n⚠️ AVISO: Credenciais não configuradas. Configure as variáveis de ambiente AMADEUS_API_KEY e AMADEUS_API_SECRET para executar os testes.")
        return
    
    # Resultado dos testes
    results = []
    flight_offer = None
    
    # Teste 1: Busca de voos
    print("\n[Teste 1/2] Executando busca de voos...")
    flights_success, flight_offer = test_flight_search()
    results.append(("Busca de voos", flights_success))
    
    # Teste 2: Verificação de preço (se houver oferta)
    if flight_offer:
        print("\n[Teste 2/2] Executando verificação de preço...")
        price_success = test_flight_price(flight_offer)
        results.append(("Verificação de preço", price_success))
    else:
        print("\n[Teste 2/2] Verificação de preço não será executada (nenhuma oferta disponível)")
        results.append(("Verificação de preço", None))
    
    # Resumo dos resultados
    print_section("RESUMO DOS RESULTADOS")
    
    for name, success in results:
        if success is None:
            status = "⚠️ NÃO EXECUTADO"
        else:
            status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"{status}: {name}")
    
    executed_tests = [success for success in [r[1] for r in results] if success is not None]
    total_success = sum(1 for success in executed_tests if success)
    total_executed = len(executed_tests)
    
    print(f"\nTestes bem-sucedidos: {total_success}/{total_executed}")
    
    if total_success == total_executed and total_executed > 0:
        print("\n🎉 Todos os testes foram bem-sucedidos! A implementação SDK está funcionando corretamente.")
    elif total_executed == 0:
        print("\n⚠️ Nenhum teste foi executado completamente. Verifique os logs acima.")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os detalhes acima.")

if __name__ == "__main__":
    main()
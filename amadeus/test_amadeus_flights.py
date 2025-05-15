#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
from services.amadeus_service_optimized import AmadeusService

def main():
    print("=== TESTE DE BUSCA DE VOOS AMADEUS ===")
    service = AmadeusService()
    
    # Definir datas para busca
    tomorrow = datetime.now() + timedelta(days=1)
    return_date = tomorrow + timedelta(days=7)
    
    # Parâmetros de busca
    params = {
        'originLocationCode': 'GRU',
        'destinationLocationCode': 'CDG',
        'departureDate': tomorrow.strftime('%Y-%m-%d'),
        'returnDate': return_date.strftime('%Y-%m-%d'),
        'adults': 1,
        'max': 5,
        'currencyCode': 'BRL'
    }
    
    print(f"Parâmetros de busca:")
    print(json.dumps(params, indent=2))
    
    # Realizar busca
    print("\nRealizando busca...")
    result = service.search_flights(params)
    
    # Verificar resultado
    if 'error' in result:
        print(f"\n❌ Erro na busca: {result.get('error')}")
        if 'details' in result:
            print(f"Detalhes: {result.get('details')}")
    else:
        flights = result.get('data', [])
        print(f"\n✅ Busca bem-sucedida! {len(flights)} voos encontrados.")
        
        # Exibir meta-informações se disponíveis
        if 'meta' in result:
            print("\nMeta-informações:")
            print(json.dumps(result['meta'], indent=2))
        
        # Exibir informações do primeiro voo se disponível
        if flights:
            print("\nPrimeiro resultado:")
            first_flight = flights[0]
            
            # ID e tipo
            print(f"ID: {first_flight.get('id')}")
            print(f"Tipo: {first_flight.get('type')}")
            
            # Preço
            if 'price' in first_flight:
                price = first_flight['price']
                print(f"Preço total: {price.get('total')} {price.get('currency')}")
                
                if 'grandTotal' in price:
                    print(f"Total geral: {price.get('grandTotal')}")
            
            # Informações básicas dos itinerários
            if 'itineraries' in first_flight:
                print("\nItinerários:")
                for i, itinerary in enumerate(first_flight['itineraries'], 1):
                    print(f"  Itinerário {i}:")
                    print(f"  Duração: {itinerary.get('duration')}")
                    
                    if 'segments' in itinerary:
                        print(f"  Segmentos: {len(itinerary['segments'])}")
                        
                        # Mostrar origem e destino do primeiro e último segmento
                        first_segment = itinerary['segments'][0]
                        last_segment = itinerary['segments'][-1]
                        
                        dep = first_segment.get('departure', {})
                        arr = last_segment.get('arrival', {})
                        
                        print(f"  Origem: {dep.get('iataCode')} ({dep.get('at')})")
                        print(f"  Destino: {arr.get('iataCode')} ({arr.get('at')})")
            
            # Se quiser ver a estrutura completa
            print("\nDeseja ver a estrutura completa dos dados? (s/n)")
            answer = input().lower()
            if answer.startswith('s'):
                print("\nEstrutura completa do resultado:")
                print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
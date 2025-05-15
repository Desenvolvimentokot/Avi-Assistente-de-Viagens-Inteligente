#!/usr/bin/env python3
"""
Script para testar a implementação do serviço Amadeus usando o SDK oficial.
"""
import os
import sys
import json
from datetime import datetime, timedelta
from amadeus import Client, ResponseError

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    print("\n" + "=" * 80)
    print(f"{title.center(80, '=')}")
    print("=" * 80 + "\n")

def main():
    """Função principal para testar o SDK da Amadeus"""
    print_section("TESTE DE BUSCA DE VOOS COM SDK OFICIAL")
    
    # Obter credenciais do ambiente
    api_key = os.environ.get('AMADEUS_API_KEY')
    api_secret = os.environ.get('AMADEUS_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Erro: Credenciais da API Amadeus não encontradas nas variáveis de ambiente.")
        print("Defina AMADEUS_API_KEY e AMADEUS_API_SECRET.")
        return
    
    try:
        # Inicializar cliente
        print("Configurando cliente Amadeus SDK...")
        amadeus = Client(
            client_id=api_key,
            client_secret=api_secret
        )
        
        # Preparar parâmetros de teste
        tomorrow = datetime.now() + timedelta(days=1)
        next_week = datetime.now() + timedelta(days=8)
        
        params = {
            'originLocationCode': 'GRU',
            'destinationLocationCode': 'CDG',
            'departureDate': tomorrow.strftime('%Y-%m-%d'),
            'returnDate': next_week.strftime('%Y-%m-%d'),
            'adults': 1,
            'max': 5
        }
        
        print("Parâmetros de busca:")
        for key, value in params.items():
            print(f"  {key}: {value}")
        
        print("\nEnviando requisição via SDK oficial...")
        
        # Executar busca de voos
        response = amadeus.shopping.flight_offers_search.get(**params)
        
        # Verificar resposta
        if hasattr(response, 'data'):
            print("\n✅ Busca bem-sucedida!")
            print(f"Código de status: {response.status_code}")
            
            flights = response.data
            print(f"Total de ofertas: {len(flights)} voos encontrados\n")
            
            # Mostrar informações das ofertas
            for i, flight in enumerate(flights[:3], 1):  # Mostra apenas as 3 primeiras
                print(f"Oferta {i}:")
                print(f"  ID: {flight['id']}")
                print(f"  Preço: {flight['price']['total']} {flight['price']['currency']}")
                
                # Mostrar informações do itinerário de ida
                for j, itinerary in enumerate(flight['itineraries'], 1):
                    print(f"  Itinerário {j}:")
                    for k, segment in enumerate(itinerary['segments'], 1):
                        print(f"    Segmento {k}:")
                        print(f"      Origem: {segment['departure']['iataCode']} - {segment['departure']['at']}")
                        print(f"      Destino: {segment['arrival']['iataCode']} - {segment['arrival']['at']}")
                
                print()
            
        else:
            print("\n❌ Busca falhou!")
            print(f"Resposta: {response}")
    
    except ResponseError as error:
        print("\n❌ Erro na API Amadeus:")
        print(f"Status: {error.response.status_code}")
        print(f"Detalhes: {error.response.body}")
    
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
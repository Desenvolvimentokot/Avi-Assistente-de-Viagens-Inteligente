"""
Script para testar a integração com a API do TravelPayouts
"""

import json
import logging
from datetime import datetime, timedelta
from services.travelpayouts_service import TravelPayoutsService

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    print(f"\n{'=' * 80}")
    print(f" {title} ".center(80, '='))
    print(f"{'=' * 80}\n")

def test_configuration():
    """Verifica a configuração do serviço TravelPayouts"""
    print_section("VERIFICAÇÃO DE CONFIGURAÇÃO")
    
    service = TravelPayoutsService()
    
    print(f"API Token: {service.token[:3]}...{service.token[-4:]}")
    print(f"Marker: {service.marker}")
    print(f"URL Preços Recentes: {service.prices_latest_endpoint}")
    print(f"URL Preços Baratos: {service.cheap_prices_endpoint}")
    
    print("\nConfiguração verificada com sucesso.")

def test_flight_search():
    """Testa a busca de voos"""
    print_section("TESTE DE BUSCA DE VOOS")
    
    service = TravelPayoutsService()
    
    # Busca de exemplo: São Paulo (GRU) para Rio de Janeiro (GIG)
    params = {
        'originLocationCode': 'GRU', 
        'destinationLocationCode': 'GIG',
        'departureDate': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        'adults': 1
    }
    
    print(f"Buscando voos com os seguintes parâmetros:")
    print(json.dumps(params, indent=2))
    
    results = service.search_flights(params)
    
    print(f"\nResultados encontrados: {len(results)} voos")
    
    if results:
        # Mostrar detalhes do primeiro resultado
        first_flight = results[0]
        print("\nDetalhes do primeiro voo encontrado:")
        print(f"ID: {first_flight.get('id')}")
        print(f"Companhia: {first_flight.get('validatingAirlineCodes', ['N/A'])[0]}")
        
        # Detalhes de itinerário
        if 'itineraries' in first_flight and first_flight['itineraries']:
            itinerary = first_flight['itineraries'][0]
            if 'segments' in itinerary and itinerary['segments']:
                segment = itinerary['segments'][0]
                print(f"Origem: {segment.get('departure', {}).get('iataCode')}")
                print(f"Destino: {segment.get('arrival', {}).get('iataCode')}")
                print(f"Data/Hora Partida: {segment.get('departure', {}).get('at')}")
                print(f"Data/Hora Chegada: {segment.get('arrival', {}).get('at')}")
        
        # Preço
        if 'price' in first_flight:
            print(f"Preço: {first_flight['price'].get('total')} {first_flight['price'].get('currency')}")
    else:
        print("Nenhum voo encontrado para os parâmetros especificados.")

def test_best_prices():
    """Testa a busca de melhores preços"""
    print_section("TESTE DE MELHORES PREÇOS")
    
    service = TravelPayoutsService()
    
    # Busca de exemplo: São Paulo (GRU) para Rio de Janeiro (GIG)
    origin = 'GRU'
    destination = 'GIG'
    
    # Data de exemplo: mês atual
    current_month = datetime.now().strftime('%Y-%m')
    
    print(f"Buscando melhores preços de {origin} para {destination} em {current_month}")
    
    results = service.search_best_prices(origin, destination, current_month)
    
    print(f"\nResultados encontrados: {len(results)} opções de preços")
    
    if results:
        # Mostrar alguns resultados
        for i, price_data in enumerate(results[:5]):
            print(f"\nOpção {i+1}:")
            print(f"Data de Partida: {price_data.get('departure_date')}")
            print(f"Data de Retorno: {price_data.get('return_date', 'N/A')}")
            print(f"Preço: {price_data.get('price')} BRL")
            print(f"Companhia: {price_data.get('airline')}")
    else:
        print("Nenhum preço encontrado para os parâmetros especificados.")

def test_partner_link():
    """Testa a geração de links de parceiro"""
    print_section("TESTE DE LINKS DE PARCEIRO")
    
    service = TravelPayoutsService()
    
    # Exemplo: São Paulo (GRU) para Rio de Janeiro (GIG)
    origin = 'GRU'
    destination = 'GIG'
    
    # Data de exemplo: 30 dias a partir de hoje
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"Gerando link de parceiro para voo de {origin} para {destination} em {future_date}")
    
    link = service.get_partner_link(origin, destination, future_date)
    
    print(f"\nLink gerado: {link}")

def main():
    """Função principal para execução dos testes"""
    print_section("TESTE DE INTEGRAÇÃO TRAVELPAYOUTS")
    print("Iniciando testes de integração com a API do TravelPayouts...")
    
    # Executar testes
    test_configuration()
    test_flight_search()
    test_best_prices()
    test_partner_link()
    
    print_section("TESTES CONCLUÍDOS")
    print("Todos os testes foram executados.")

if __name__ == "__main__":
    main()
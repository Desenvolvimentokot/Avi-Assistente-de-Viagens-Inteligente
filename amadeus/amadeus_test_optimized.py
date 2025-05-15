#!/usr/bin/env python3
import json
import logging
import sys
from datetime import datetime, timedelta

# Configurando logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Importando o serviço Amadeus otimizado
from services.amadeus_service_optimized import AmadeusService

def print_section(title):
    """Imprime uma seção formada no relatório"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, '='))
    print("="*80 + "\n")

def test_connection():
    """Testa e exibe o diagnóstico de conexão com a API Amadeus"""
    print_section("TESTE DE CONEXÃO COM API AMADEUS")
    
    service = AmadeusService()
    result = service.test_connection()
    
    # Formatar e exibir resultados
    print(f"Status: {'✅ SUCESSO' if result['success'] else '❌ FALHA'}")
    print(f"Ambiente: {result['environment'].upper()}")
    print(f"URL Base: {result['base_url']}")
    
    # Credenciais
    print("\nCredenciais:")
    print(f"  API Key: {'✅ Configurada' if result['credentials']['api_key_set'] else '❌ Não configurada'}")
    print(f"  API Secret: {'✅ Configurada' if result['credentials']['api_secret_set'] else '❌ Não configurada'}")
    print(f"  Válidas: {'✅ Sim' if result['credentials']['valid'] else '❌ Não'}")
    
    # Conectividade
    print("\nConectividade:")
    print(f"  Conexão: {'✅ Estabelecida' if result['connectivity']['can_connect'] else '❌ Falhou'}")
    
    if result['connectivity']['timeout_ms']:
        print(f"  Tempo de resposta: {result['connectivity']['timeout_ms']}ms")
    
    # Informações de endpoint
    if result['connectivity'].get('endpoint'):
        endpoint = result['connectivity']['endpoint']
        print("\nTeste de endpoint:")
        print(f"  URL: {endpoint.get('url')}")
        if endpoint.get('success'):
            print(f"  Status: ✅ {endpoint.get('status', 'OK')}")
            print(f"  Tempo de resposta: {endpoint.get('timeout_ms')}ms")
        else:
            print(f"  Status: ❌ Falha")
            if endpoint.get('error'):
                print(f"  Erro: {endpoint.get('error')}")
    
    # Token
    print("\nToken de autenticação:")
    if result['token']['obtained']:
        print(f"  Status: ✅ Obtido com sucesso")
        print(f"  Token: {result['token']['value']}")
        
        if result['token']['expires_in']:
            print(f"  Expira em: {result['token']['expires_in']} segundos")
    else:
        print(f"  Status: ❌ Falha ao obter token")
    
    # Erros
    if result['errors']:
        print("\nErros encontrados:")
        for i, error in enumerate(result['errors'], 1):
            print(f"  {i}. {error}")

def test_flight_search():
    """Testa a funcionalidade de busca de voos"""
    print_section("TESTE DE BUSCA DE VOOS")
    
    service = AmadeusService()
    
    # Definir parâmetros de teste
    tomorrow = datetime.now() + timedelta(days=1)
    return_date = tomorrow + timedelta(days=7)
    
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
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    print("\nEnviando requisição...")
    result = service.search_flights(params)
    
    if 'error' in result:
        print(f"\n❌ Erro na busca: {result['error']}")
        if 'details' in result:
            print(f"Detalhes: {result['details']}")
    else:
        flights = result.get('data', [])
        dictionaries = result.get('dictionaries', {})
        
        print(f"\n✅ Busca bem-sucedida! {len(flights)} voos encontrados.")
        
        # Exibir detalhes dos voos encontrados
        if flights:
            for i, flight in enumerate(flights[:3], 1):  # Mostrar apenas os 3 primeiros
                try:
                    print(f"\nVoo {i}:")
                    
                    # Informações de preço
                    price = flight.get('price', {})
                    print(f"  Preço: {price.get('total', 'N/A')} {price.get('currency', 'BRL')}")
                    
                    # Informações de itinerários
                    itineraries = flight.get('itineraries', [])
                    if itineraries:
                        for j, itinerary in enumerate(itineraries, 1):
                            print(f"  Itinerário {j}:")
                            
                            segments = itinerary.get('segments', [])
                            if segments:
                                for k, segment in enumerate(segments, 1):
                                    print(f"    Segmento {k}:")
                                    
                                    # Origem
                                    origin = segment.get('departure', {})
                                    print(f"      Origem: {origin.get('iataCode', 'N/A')} - {origin.get('at', 'N/A')}")
                                    
                                    # Destino
                                    destination = segment.get('arrival', {})
                                    print(f"      Destino: {destination.get('iataCode', 'N/A')} - {destination.get('at', 'N/A')}")
                                    
                                    # Companhia aérea
                                    carrier_code = segment.get('carrierCode', 'N/A')
                                    carrier_name = dictionaries.get('carriers', {}).get(carrier_code, carrier_code)
                                    print(f"      Companhia: {carrier_name} ({carrier_code})")
                                    
                                    # Número do voo
                                    print(f"      Voo: {carrier_code}{segment.get('number', 'N/A')}")
                                    
                                    # Duração
                                    print(f"      Duração: {segment.get('duration', 'N/A')}")
                except Exception as e:
                    print(f"  Erro ao processar detalhes do voo: {str(e)}")

def test_hotel_search():
    """Testa a funcionalidade de busca de hotéis"""
    print_section("TESTE DE BUSCA DE HOTÉIS")
    
    service = AmadeusService()
    
    # Parâmetros para buscar hotéis em Paris
    hotel_params = {
        'cityCode': 'PAR',
        'radius': 5,
        'radiusUnit': 'KM',
        'amenities': 'SWIMMING_POOL,SPA',
        'ratings': '4,5'
    }
    
    print(f"Parâmetros de busca de hotéis:")
    for key, value in hotel_params.items():
        print(f"  {key}: {value}")
    
    print("\nEnviando requisição...")
    hotel_result = service.search_hotels(hotel_params)
    
    if 'error' in hotel_result:
        print(f"\n❌ Erro na busca de hotéis: {hotel_result['error']}")
        if 'details' in hotel_result:
            print(f"Detalhes: {hotel_result['details']}")
    else:
        hotels = hotel_result.get('data', [])
        
        print(f"\n✅ Busca bem-sucedida! {len(hotels)} hotéis encontrados.")
        
        # Exibir detalhes dos hotéis encontrados
        if hotels:
            for i, hotel in enumerate(hotels[:3], 1):  # Mostrar apenas os 3 primeiros
                try:
                    print(f"\nHotel {i}:")
                    
                    # Garantir que hotel é um dicionário
                    if isinstance(hotel, dict):
                        print(f"  ID: {hotel.get('hotelId', 'N/A')}")
                        print(f"  Nome: {hotel.get('name', 'N/A')}")
                        print(f"  Tipo: {hotel.get('type', 'N/A')}")
                        
                        # Endereço
                        address = hotel.get('address', {})
                        if address and isinstance(address, dict):
                            addr_lines = []
                            if address.get('lines') and isinstance(address.get('lines'), list):
                                addr_lines.extend(address.get('lines', []))
                            if address.get('postalCode'):
                                addr_lines.append(address.get('postalCode', ''))
                            if address.get('cityName'):
                                addr_lines.append(address.get('cityName', ''))
                            if address.get('countryCode'):
                                addr_lines.append(address.get('countryCode', ''))
                                
                            print(f"  Endereço: {', '.join(filter(None, addr_lines))}")
                        
                        # Contato
                        contact = hotel.get('contact', {})
                        if contact and isinstance(contact, dict):
                            if contact.get('phone'):
                                print(f"  Telefone: {contact.get('phone', 'N/A')}")
                            if contact.get('email'):
                                print(f"  Email: {contact.get('email', 'N/A')}")
                    else:
                        print("  Detalhes do hotel não disponíveis (formato inválido)")
                except Exception as e:
                    print(f"  Erro ao processar detalhes do hotel: {str(e)}")
    
    # Se encontrou hotéis, testar a busca de ofertas para o primeiro hotel
    if 'data' in hotel_result and hotel_result['data']:
        print_section("TESTE DE BUSCA DE OFERTAS DE HOTÉIS")
        
        # Obter ID do primeiro hotel de forma segura
        first_hotel = hotel_result['data'][0]
        hotel_id = first_hotel.get('hotelId') if isinstance(first_hotel, dict) else None
        
        if hotel_id:
            # Datas para check-in/check-out
            check_in_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            check_out_date = (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')
            
            # Parâmetros para buscar ofertas
            offer_params = {
                'hotelIds': hotel_id,
                'adults': 2,
                'checkInDate': check_in_date,
                'checkOutDate': check_out_date,
                'roomQuantity': 1,
                'currency': 'BRL'
            }
            
            print(f"Parâmetros de busca de ofertas:")
            for key, value in offer_params.items():
                print(f"  {key}: {value}")
            
            print("\nEnviando requisição...")
            offer_result = service.search_hotel_offers(offer_params)
            
            if 'error' in offer_result:
                print(f"\n❌ Erro na busca de ofertas: {offer_result['error']}")
                if 'details' in offer_result:
                    print(f"Detalhes: {offer_result['details']}")
            else:
                offers = offer_result.get('data', [])
                
                print(f"\n✅ Busca bem-sucedida! {len(offers)} ofertas encontradas.")
                
                # Exibir detalhes das ofertas encontradas
                if offers:
                    for i, offer_data in enumerate(offers[:2], 1):  # Mostrar apenas as 2 primeiras
                        try:
                            print(f"\nOferta {i}:")
                            
                            # Informações do hotel
                            hotel = offer_data.get('hotel', {}) if isinstance(offer_data, dict) else {}
                            hotel_name = hotel.get('name', 'N/A') if isinstance(hotel, dict) else 'N/A'
                            print(f"  Hotel: {hotel_name}")
                            
                            # Ofertas específicas
                            room_offers = offer_data.get('offers', []) if isinstance(offer_data, dict) else []
                            if room_offers:
                                for j, room_offer in enumerate(room_offers, 1):
                                    print(f"  Quarto {j}:")
                                    
                                    # Preço
                                    price = room_offer.get('price', {})
                                    print(f"    Preço: {price.get('total', 'N/A')} {price.get('currency', 'BRL')}")
                                    
                                    # Tipo de quarto
                                    room = room_offer.get('room', {})
                                    print(f"    Tipo: {room.get('type', 'N/A')}")
                                    print(f"    Descrição: {room.get('description', {}).get('text', 'N/A')}")
                                    
                                    # Regime
                                    board_type = room_offer.get('boardType', 'N/A')
                                    print(f"    Regime: {board_type}")
                        except Exception as e:
                            print(f"  Erro ao processar detalhes da oferta: {str(e)}")

def main():
    """Função principal com suite de testes"""
    print_section("DIAGNÓSTICO DE INTEGRAÇÃO COM API AMADEUS (OTIMIZADO)")
    print("Data e hora: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        # Executar testes
        test_connection()
        test_flight_search()
        test_hotel_search()
        
        print_section("TESTES CONCLUÍDOS")
    except Exception as e:
        print(f"\n❌ ERRO DURANTE TESTES: {str(e)}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script para testar o serviço de busca rápida usando a implementação completa
com Amadeus SDK.
"""
import logging
from services.busca_rapida_service import process_message

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    line = "=" * 70
    print("\n" + line)
    print(f" {title} ".center(70, "="))
    print(line + "\n")

def test_busca_rapida_periodo_flexivel():
    """Testa a busca rápida com período flexível"""
    print_section("Teste de Busca Rápida com Período Flexível")
    
    # Mensagem do usuário buscando passagens com período flexível
    message = "Quero viajar de São Paulo para Miami em maio do próximo ano, qual o melhor preço?"
    
    print("Mensagem do usuário:")
    print(f'"{message}"')
    print("\nProcessando mensagem...")
    
    # Processar a mensagem com limite para testes rápidos
    response = process_message(message, {"max_dates_to_check": 1})
    
    # Verificar se a resposta foi gerada
    if response and "response" in response:
        print("✅ Resposta gerada com sucesso!")
        print("\nResposta (primeiros 150 caracteres):")
        print(f'"{response["response"][:150]}..."')
        
        # Verificar se dados de preço foram incluídos
        if "best_prices_data" in response:
            prices = response["best_prices_data"].get("best_prices", [])
            print(f"\n✅ Dados de melhores preços incluídos: {len(prices)} opções")
            
            # Mostrar alguns exemplos
            if prices:
                print("\nExemplos de preços:")
                for i, price in enumerate(prices[:3]):
                    print(f"   {i+1}. Data: {price['date']} - Preço: {price['price']} {price['currency']}")
        else:
            print("\n❌ Dados de melhores preços não incluídos na resposta")
    else:
        print(f"❌ Erro ao processar mensagem: {response.get('error', 'Erro desconhecido')}")

def test_busca_rapida_data_especifica():
    """Testa a busca rápida com data específica"""
    print_section("Teste de Busca Rápida com Data Específica")
    
    # Mensagem do usuário buscando passagens com data específica
    message = "Preciso de um voo de São Paulo para o Rio de Janeiro no dia 15 de maio de 2025"
    
    print("Mensagem do usuário:")
    print(f'"{message}"')
    print("\nProcessando mensagem...")
    
    # Processar a mensagem com limite para testes rápidos
    response = process_message(message, {"max_dates_to_check": 1})
    
    # Verificar se a resposta foi gerada
    if response and "response" in response:
        print("✅ Resposta gerada com sucesso!")
        print("\nResposta (primeiros 150 caracteres):")
        print(f'"{response["response"][:150]}..."')
        
        # Verificar se dados de voos foram incluídos
        if "flight_data" in response:
            flights = response["flight_data"].get("flights", [])
            print(f"\n✅ Dados de voos incluídos: {len(flights)} opções")
            
            # Mostrar alguns exemplos
            if flights:
                print("\nExemplos de voos:")
                for i, flight in enumerate(flights[:3]):
                    print(f"   {i+1}. {flight.get('airline', 'N/A')} - {flight.get('price', 0)} {flight.get('currency', 'BRL')}")
        else:
            print("\n❌ Dados de voos não incluídos na resposta")
    else:
        print(f"❌ Erro ao processar mensagem: {response.get('error', 'Erro desconhecido')}")

def main():
    """Função principal para executar os testes"""
    print_section("Teste do Serviço de Busca Rápida")
    
    # Executar testes
    test_busca_rapida_periodo_flexivel()
    test_busca_rapida_data_especifica()
    
    print_section("Teste Concluído")

if __name__ == "__main__":
    main()
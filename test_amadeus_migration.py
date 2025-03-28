#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('amadeus_migration_test')

"""
Script para testar a migração do serviço Amadeus para o SDK oficial.
Este script compara a implementação original com a implementação baseada no SDK.
"""

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, '='))
    print("="*80 + "\n")

def test_interface_compatibility():
    """Testa a compatibilidade da interface entre as implementações"""
    print_section("TESTE DE COMPATIBILIDADE DA INTERFACE")
    
    # Importar ambas as implementações
    from services.amadeus_service import AmadeusService as OriginalService
    from services.amadeus_service_sdk_adapted import AmadeusService as SDKService
    
    # Instanciar os serviços
    original_service = OriginalService()
    sdk_service = SDKService()
    
    # Verificar métodos disponíveis
    original_methods = [method for method in dir(original_service) 
                        if not method.startswith('_') and callable(getattr(original_service, method))]
    
    sdk_methods = [method for method in dir(sdk_service) 
                   if not method.startswith('_') and callable(getattr(sdk_service, method))]
    
    print("Métodos na implementação original:")
    for method in sorted(original_methods):
        print(f"  - {method}")
    
    print("\nMétodos na implementação baseada no SDK:")
    for method in sorted(sdk_methods):
        print(f"  - {method}")
    
    # Verificar compatibilidade
    missing_methods = [method for method in original_methods if method not in sdk_methods]
    
    if missing_methods:
        print("\n❌ Métodos ausentes na implementação SDK:")
        for method in missing_methods:
            print(f"  - {method}")
        return False
    else:
        print("\n✅ Todas os métodos da implementação original estão presentes no SDK")
        return True

def test_authentication():
    """Testa a autenticação em ambas as implementações"""
    print_section("TESTE DE AUTENTICAÇÃO")
    
    # Importar ambas as implementações
    from services.amadeus_service import AmadeusService as OriginalService
    from services.amadeus_service_sdk_adapted import AmadeusService as SDKService
    
    # Instanciar os serviços
    original_service = OriginalService()
    sdk_service = SDKService()
    
    # Testar autenticação na implementação original
    print("Autenticação na implementação original:")
    original_token = original_service.get_token()
    print(f"  Token obtido: {'✅ Sim' if original_token else '❌ Não'}")
    
    # Testar autenticação na implementação SDK
    print("\nAutenticação na implementação SDK:")
    sdk_token = sdk_service.get_token()
    print(f"  Token obtido: {'✅ Sim' if sdk_token else '❌ Não'}")
    
    return original_token is not None and sdk_token is not None

def test_flight_search():
    """Testa a busca de voos em ambas as implementações"""
    print_section("TESTE DE BUSCA DE VOOS")
    
    # Importar ambas as implementações
    from services.amadeus_service import AmadeusService as OriginalService
    from services.amadeus_service_sdk_adapted import AmadeusService as SDKService
    
    # Instanciar os serviços
    original_service = OriginalService()
    sdk_service = SDKService()
    
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
    
    # Testar busca na implementação original
    print("\nBusca na implementação original:")
    try:
        original_result = original_service.search_flights(params)
        
        if 'error' in original_result:
            print(f"  ❌ Erro: {original_result['error']}")
            original_success = False
        else:
            flights = original_result.get('data', [])
            print(f"  ✅ Sucesso: {len(flights)} voos encontrados")
            original_success = True
            
    except Exception as e:
        print(f"  ❌ Exceção: {str(e)}")
        original_success = False
    
    # Testar busca na implementação SDK
    print("\nBusca na implementação SDK:")
    try:
        sdk_result = sdk_service.search_flights(params)
        
        if 'error' in sdk_result:
            print(f"  ❌ Erro: {sdk_result['error']}")
            sdk_success = False
        else:
            flights = sdk_result.get('data', [])
            print(f"  ✅ Sucesso: {len(flights)} voos encontrados")
            sdk_success = True
            
    except Exception as e:
        print(f"  ❌ Exceção: {str(e)}")
        sdk_success = False
    
    # Comparar estrutura de dados das respostas
    if original_success and sdk_success:
        print("\nComparando estrutura de dados das respostas:")
        
        original_keys = set(original_result.keys())
        sdk_keys = set(sdk_result.keys())
        
        if original_keys == sdk_keys:
            print("  ✅ Mesmas chaves no nível principal")
        else:
            print("  ❌ Chaves diferentes no nível principal")
            print(f"    Original: {original_keys}")
            print(f"    SDK: {sdk_keys}")
        
        if 'data' in original_result and 'data' in sdk_result and original_result['data'] and sdk_result['data']:
            original_flight = original_result['data'][0]
            sdk_flight = sdk_result['data'][0]
            
            original_flight_keys = set(original_flight.keys())
            sdk_flight_keys = set(sdk_flight.keys())
            
            if original_flight_keys == sdk_flight_keys:
                print("  ✅ Mesmas chaves no objeto de voo")
            else:
                print("  ❌ Chaves diferentes no objeto de voo")
                print(f"    Original: {original_flight_keys}")
                print(f"    SDK: {sdk_flight_keys}")
    
    return original_success and sdk_success

def main():
    """Função principal para executar todos os testes"""
    print_section("TESTES DE MIGRAÇÃO DO SERVIÇO AMADEUS")
    
    results = []
    
    # Teste 1: Compatibilidade da interface
    print("\n[Teste 1/3] Verificando compatibilidade da interface...")
    interface_compatibility = test_interface_compatibility()
    results.append(("Compatibilidade da interface", interface_compatibility))
    
    # Teste 2: Autenticação
    print("\n[Teste 2/3] Testando autenticação...")
    authentication = test_authentication()
    results.append(("Autenticação", authentication))
    
    # Teste 3: Busca de voos
    print("\n[Teste 3/3] Testando busca de voos...")
    flight_search = test_flight_search()
    results.append(("Busca de voos", flight_search))
    
    # Resumo dos resultados
    print_section("RESUMO DOS RESULTADOS")
    
    for name, success in results:
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"{status}: {name}")
    
    total_success = sum(1 for _, success in results if success)
    print(f"\nTestes bem-sucedidos: {total_success}/{len(results)}")
    
    if total_success == len(results):
        print("\n🎉 Todos os testes foram bem-sucedidos! A migração parece compatível.")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os detalhes acima.")

if __name__ == "__main__":
    main()
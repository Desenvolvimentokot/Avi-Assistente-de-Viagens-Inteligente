#!/usr/bin/env python3
"""
Script para testar a funcionalidade de busca de melhores preços 
usando o serviço Amadeus adaptado com SDK.
"""
import os
import logging
from datetime import datetime, timedelta
from services.amadeus_service import AmadeusService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    line = "=" * 70
    print("\n" + line)
    print(f" {title} ".center(70, "="))
    print(line + "\n")

def test_search_best_prices():
    """Testa a funcionalidade de busca de melhores preços"""
    print_section("Teste de Busca de Melhores Preços")
    
    # Inicializar o serviço
    service = AmadeusService()
    
    # Verificar se o serviço está funcionando
    print("Testando conexão com o serviço Amadeus...")
    connection_test = service.test_connection()
    if connection_test["success"]:
        print("✅ Conexão com o Amadeus estabelecida com sucesso.")
        print(f"   - Ambiente: {connection_test.get('environment', 'N/A')}")
    else:
        print("❌ Erro ao conectar com o Amadeus.")
        print(f"   - Erro: {connection_test.get('errors', ['Erro desconhecido'])[0]}")
        return
    
    # Definir parâmetros de teste (com datas mais próximas para teste mais rápido)
    today = datetime.now()
    future_date = today + timedelta(days=2)  # Data mais próxima para teste mais rápido
    future_date_end = future_date + timedelta(days=1)  # Período mais curto de apenas 1 dia
    
    params = {
        'origin': 'GRU',
        'destination': 'MIA',
        'departure_date': future_date.strftime('%Y-%m-%d'),
        'return_date': future_date_end.strftime('%Y-%m-%d'),
        'adults': 1,
        'currency': 'BRL'
    }
    
    print(f"\nBuscando melhores preços de {params['origin']} para {params['destination']}...")
    print(f"Período: {params['departure_date']} a {params['return_date']}")
    
    # Verificar a desativação de dados simulados (conforme política de dados reais)
    print("\nVerificando desativação de dados simulados...")
    simulated_prices_response = service.get_simulated_best_prices(params)
    if 'error' in simulated_prices_response:
        print(f"✅ Dados simulados corretamente desativados: {simulated_prices_response['error']}")
    else:
        print("❌ ERRO: Dados simulados ainda estão habilitados, isso viola a política de dados")
        
    # Adicionar limite máximo para busca mais rápida em testes
    params['max_dates_to_check'] = 1  # Limitamos a apenas 1 data para teste
    
    # Testar a busca real de melhores preços
    print("\nExecutando busca real de melhores preços (limitado a 1 data para teste)...")
    result = service.search_best_prices(params)
    
    # Resumo do teste
    print("\nResumo do teste:")
    print("----------------")
    if "error" not in result and result.get("best_prices"):
        print("✅ Busca de melhores preços implementada e funcionando corretamente.")
        print(f"   Número de resultados: {len(result.get('best_prices', []))}")
        if result.get("best_prices"):
            print("\nExemplo de resultado:")
            sample = result["best_prices"][0] if result["best_prices"] else {}
            for key, value in sample.items():
                print(f"   {key}: {value}")
    else:
        error_msg = result.get("error", "Erro desconhecido")
        print(f"❌ Falha na busca de melhores preços: {error_msg}")

def main():
    """Função principal para executar todos os testes"""
    print_section("Teste do Serviço Amadeus SDK - Busca de Melhores Preços")
    
    # Verificar se as credenciais estão configuradas
    api_key = os.environ.get('AMADEUS_API_KEY')
    api_secret = os.environ.get('AMADEUS_API_SECRET')
    
    if not api_key or not api_secret:
        print("⚠️ Credenciais do Amadeus não encontradas!")
        print("Defina as variáveis de ambiente AMADEUS_API_KEY e AMADEUS_API_SECRET.")
        return
    
    print(f"API Key: {api_key[:5]}{'*' * 10}")
    print(f"API Secret: {api_secret[:5]}{'*' * 10}")
    
    # Executar testes
    test_search_best_prices()
    
    print_section("Teste Concluído")

if __name__ == "__main__":
    main()
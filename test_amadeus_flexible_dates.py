#!/usr/bin/env python3
"""
Script para testar a funcionalidade de busca com datas flexíveis no serviço Amadeus.
Este teste verifica se o parâmetro max_dates_to_check está funcionando corretamente.
"""
import logging
import os
from datetime import datetime
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path para importar os módulos
if os.path.exists('services'):
    sys.path.append('.')

# Importar serviços após ajustar o path
from services.busca_rapida_service import search_best_prices

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    line = "=" * 70
    print("\n" + line)
    print(f"{title}".center(70, "="))
    print(line + "\n")

def test_max_dates_parameter():
    """Testa a funcionalidade do parâmetro max_dates_to_check"""
    print_section("Teste do Parâmetro max_dates_to_check")
    
    # Criar informações de viagem para teste
    travel_info = {
        'origin': 'GRU',  # São Paulo
        'destination': 'RIO',  # Rio de Janeiro
        'date_range_start': '2025-05-01',
        'date_range_end': '2025-05-31',
        'adults': 1,
        'is_flexible': True
    }
    
    # Definir diferentes valores para max_dates_to_check
    test_cases = [
        {'max': 1, 'desc': 'apenas 1 data'},
        {'max': 3, 'desc': '3 datas'},
        {'max': 5, 'desc': '5 datas'}
    ]
    
    for case in test_cases:
        max_dates = case['max']
        desc = case['desc']
        
        print(f"\n🔍 Testando busca com {desc}")
        travel_info['max_dates_to_check'] = max_dates
        
        # Registrar o tempo de início
        start_time = datetime.now()
        
        # Buscar melhores preços
        result = search_best_prices(travel_info)
        
        # Calcular o tempo total
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Verificar resultados
        if 'error' in result:
            print(f"❌ Erro na busca: {result['error']}")
        else:
            best_prices = result.get('best_prices', [])
            print(f"✅ Busca concluída em {elapsed:.2f} segundos")
            print(f"   Datas verificadas: {max_dates}")
            print(f"   Resultados obtidos: {len(best_prices)}")
            
            # Mostrar exemplos de preços
            if best_prices:
                print("\n   Exemplos de preços:")
                for i, price in enumerate(best_prices[:3]):
                    print(f"      {i+1}. Data: {price['date']} - Preço: {price['price']} {price['currency']}")

def main():
    """Função principal para executar o teste"""
    print_section("Teste de Busca com Datas Flexíveis - Amadeus")
    
    # Executar teste
    test_max_dates_parameter()
    
    print_section("Teste Concluído")

if __name__ == "__main__":
    main()
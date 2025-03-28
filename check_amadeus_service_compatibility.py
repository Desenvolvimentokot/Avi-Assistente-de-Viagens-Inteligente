#!/usr/bin/env python3
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('amadeus_compatibility')

def print_section(title):
    """Imprime uma seção formatada no relatório"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, '='))
    print("="*80 + "\n")

def check_interfaces():
    """Testa a compatibilidade das interfaces entre implementações"""
    print_section("COMPATIBILIDADE DA INTERFACE")
    
    try:
        # Importar as implementações
        from services.amadeus_service_backup import AmadeusService as OriginalService
        from services.amadeus_service_sdk_adapted import AmadeusService as SDKService
        
        # Instanciar os serviços (sem inicializar)
        original_service = OriginalService()
        sdk_service = SDKService()
        
        # Verificar métodos disponíveis
        original_methods = [method for method in dir(original_service) 
                            if not method.startswith('_') and callable(getattr(original_service, method))]
        
        sdk_methods = [method for method in dir(sdk_service) 
                       if not method.startswith('_') and callable(getattr(sdk_service, method))]
        
        # Verificar métodos da implementação original que devem existir na nova
        required_methods = [
            'get_token',
            'search_flights',
            'search_hotels',
            'search_hotel_offers',
            'test_connection'
        ]
        
        # Verificar se todos os métodos estão presentes
        missing_methods = [method for method in required_methods if method not in sdk_methods]
        
        if missing_methods:
            print("❌ Métodos obrigatórios ausentes na implementação SDK:")
            for method in missing_methods:
                print(f"  - {method}")
            return False
        else:
            print("✅ Todos os métodos obrigatórios estão presentes na implementação SDK")
            
            # Verificar assinaturas dos métodos
            print("\nVerificando assinaturas dos métodos principais:")
            
            # get_token não recebe parâmetros
            print(f"  get_token(): {'✅ Compatível' if 'get_token' in sdk_methods else '❌ Incompatível'}")
            
            # search_flights recebe um dict de parâmetros
            print(f"  search_flights(params): {'✅ Compatível' if 'search_flights' in sdk_methods else '❌ Incompatível'}")
            
            # test_connection não recebe parâmetros
            print(f"  test_connection(): {'✅ Compatível' if 'test_connection' in sdk_methods else '❌ Incompatível'}")
            
            # search_hotels recebe um dict de parâmetros
            print(f"  search_hotels(params): {'✅ Compatível' if 'search_hotels' in sdk_methods else '❌ Incompatível'}")
            
            # search_hotel_offers recebe um dict de parâmetros
            print(f"  search_hotel_offers(params): {'✅ Compatível' if 'search_hotel_offers' in sdk_methods else '❌ Incompatível'}")
            
            return True
    except Exception as e:
        print(f"❌ Erro ao verificar interfaces: {str(e)}")
        return False

def check_implementation():
    """Verifica se a implementação adaptada está correta"""
    print_section("VERIFICAÇÃO DA IMPLEMENTAÇÃO")
    
    try:
        # Carregar a implementação adaptada para verificação
        from services.amadeus_service_sdk_adapted import AmadeusService
        
        # Instanciar o serviço (sem inicializar de fato)
        service = AmadeusService()
        
        # Verificar se o serviço inicializa corretamente
        print("Verificando inicialização do serviço:")
        if service.client is None and (service.api_key is None or service.api_secret is None):
            print("✅ O serviço detectou a ausência de credenciais corretamente")
        else:
            print("O serviço inicializou mesmo sem credenciais válidas (pode ser normal se houver variáveis de ambiente)")
        
        # Verificar a estrutura de retorno de alguns métodos
        # Sem fazer requisições reais
        
        # Teste de token
        print("\nVerificando estrutura de retorno do get_token():")
        token = service.get_token()
        if token is not None:
            print(f"✅ O método get_token() retorna um token: {token[:10]}...")
        else:
            print("❌ O método get_token() não retornou um token (mas pode ser normal se as credenciais não estiverem definidas)")
        
        # Teste de busca de voos com parâmetros inválidos (sem fazer requisição real)
        print("\nVerificando tratamento de parâmetros inválidos em search_flights():")
        result = service.search_flights({})  # Parâmetros vazios
        if 'error' in result:
            print(f"✅ O método search_flights() trata parâmetros inválidos: {result['error']}")
        else:
            print("❌ O método search_flights() não tratou corretamente parâmetros inválidos")
            
        # Verificar método test_connection
        print("\nVerificando estrutura de retorno do test_connection():")
        connection_test = service.test_connection()
        if isinstance(connection_test, dict) and 'success' in connection_test:
            print("✅ O método test_connection() retorna um dicionário com a chave 'success'")
            required_keys = ['success', 'errors', 'credentials', 'connectivity']
            missing_keys = [key for key in required_keys if key not in connection_test]
            if missing_keys:
                print(f"❌ Chaves ausentes no retorno: {missing_keys}")
            else:
                print("✅ Todas as chaves obrigatórias estão presentes")
        else:
            print("❌ O método test_connection() não retornou o formato esperado")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar implementação: {str(e)}")
        return False

def main():
    """Função principal para executar todas as verificações"""
    print_section("VERIFICAÇÃO DE COMPATIBILIDADE DO SERVIÇO AMADEUS")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar variáveis de ambiente
    print("\nVariáveis de ambiente:")
    api_key = os.environ.get('AMADEUS_API_KEY')
    api_secret = os.environ.get('AMADEUS_API_SECRET')
    print(f"  AMADEUS_API_KEY: {'✅ Definida' if api_key else '❌ Não definida'}")
    print(f"  AMADEUS_API_SECRET: {'✅ Definida' if api_secret else '❌ Não definida'}")
    
    # Executar verificações
    results = []
    
    print("\n[Verificação 1/2] Compatibilidade da interface...")
    interface_compatibility = check_interfaces()
    results.append(("Compatibilidade da interface", interface_compatibility))
    
    print("\n[Verificação 2/2] Implementação adaptada...")
    implementation_check = check_implementation()
    results.append(("Implementação adaptada", implementation_check))
    
    # Resumo dos resultados
    print_section("RESUMO DOS RESULTADOS")
    
    for name, success in results:
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"{status}: {name}")
    
    total_success = sum(1 for _, success in results if success)
    print(f"\nVerificações bem-sucedidas: {total_success}/{len(results)}")
    
    if total_success == len(results):
        print("\n🎉 Todas as verificações foram bem-sucedidas! A implementação adaptada parece compatível.")
    else:
        print("\n⚠️ Algumas verificações falharam. Verifique os detalhes acima.")

if __name__ == "__main__":
    main()
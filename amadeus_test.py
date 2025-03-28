#!/usr/bin/env python3
import os
import sys
import json
import logging
from datetime import datetime

# Configurando logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Importando o serviço Amadeus
sys.path.append('.')
from services.amadeus_service import AmadeusService

def print_section(title):
    """Imprime uma seção no relatório"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, '='))
    print("="*80 + "\n")

def check_environment():
    """Verifica variáveis de ambiente e dependências"""
    print_section("VERIFICAÇÃO DO AMBIENTE ATUAL")
    
    # Verificando variáveis de ambiente
    api_key = os.environ.get('AMADEUS_API_KEY')
    api_secret = os.environ.get('AMADEUS_API_SECRET')
    
    print(f"AMADEUS_API_KEY: {'Configurada' if api_key else 'NÃO CONFIGURADA'}")
    print(f"AMADEUS_API_SECRET: {'Configurada' if api_secret else 'NÃO CONFIGURADA'}")
    
    # Listando dependências
    try:
        import pkg_resources
        print("\nDependências instaladas relacionadas à API:")
        packages = ['requests']
        for package in packages:
            try:
                version = pkg_resources.get_distribution(package).version
                print(f"- {package}: v{version}")
            except pkg_resources.DistributionNotFound:
                print(f"- {package}: NÃO INSTALADO")
    except ImportError:
        print("Não foi possível verificar as dependências instaladas.")

def test_authentication(service):
    """Testa a autenticação OAuth 2.0"""
    print_section("DIAGNÓSTICO DE AUTENTICAÇÃO")
    
    print("Tentando obter token de autenticação...")
    token = service.get_token()
    
    if token:
        print("✅ Autenticação bem-sucedida!")
        print(f"Token obtido: {token[:10]}... (primeiros 10 caracteres)")
    else:
        print("❌ Falha na autenticação!")
        print("Verifique as credenciais e a conexão com a API.")

def test_configuration(service):
    """Analisa a configuração da API"""
    print_section("VALIDAÇÃO DE CONFIGURAÇÕES")
    
    print(f"URL Base: {service.base_url}")
    
    # Verificar ambiente (teste ou produção)
    env_type = "TESTE" if "test.api" in service.base_url else "PRODUÇÃO"
    print(f"Ambiente: {env_type}")
    
    # Verificar estratégia de renovação de token
    if hasattr(service, 'token_expires') or hasattr(service, 'token_expiry'):
        print("Estratégia de renovação de token: Verificação de expiração baseada em tempo")
    else:
        print("Estratégia de renovação de token: Não identificada")
    
    # Verificar se há fallback para mock data
    if hasattr(service, 'use_mock_data'):
        print(f"Fallback para dados simulados: {'Habilitado' if service.use_mock_data else 'Desabilitado'}")
    else:
        print("Fallback para dados simulados: Não configurado")

def test_api_requests(service):
    """Testa requisições à API"""
    print_section("TESTE DE CONEXÃO E REQUISIÇÃO DE PASSAGENS")
    
    # Parâmetros de teste
    test_params = {
        'originLocationCode': 'GRU',
        'destinationLocationCode': 'CDG',
        'departureDate': (datetime.now() + pd.Timedelta(days=30)).strftime('%Y-%m-%d'),
        'adults': 1,
        'currencyCode': 'BRL',
        'max': 2
    }
    
    print(f"Parâmetros de teste: {json.dumps(test_params, indent=2)}")
    
    # Testar busca de voos
    print("\nTestando busca de voos...")
    try:
        flights_result = service.search_flights(test_params)
        
        if 'error' in flights_result:
            print(f"❌ Erro na busca de voos: {flights_result['error']}")
        else:
            flights_count = len(flights_result.get('data', []))
            print(f"✅ Busca de voos bem-sucedida! {flights_count} resultado(s) encontrado(s).")
            
            # Mostrar detalhes do primeiro resultado se houver
            if flights_count > 0:
                first_flight = flights_result['data'][0]
                print("\nPrimeiro resultado:")
                
                try:
                    price = first_flight.get('price', {}).get('total', 'N/A')
                    currency = first_flight.get('price', {}).get('currency', 'N/A')
                    itineraries = first_flight.get('itineraries', [])
                    
                    print(f"Preço: {price} {currency}")
                    
                    if itineraries:
                        first_segment = itineraries[0].get('segments', [])[0]
                        
                        if first_segment:
                            dep = first_segment.get('departure', {})
                            arr = first_segment.get('arrival', {})
                            
                            print(f"Origem: {dep.get('iataCode', 'N/A')} - {dep.get('at', 'N/A')}")
                            print(f"Destino: {arr.get('iataCode', 'N/A')} - {arr.get('at', 'N/A')}")
                except Exception as detail_e:
                    print(f"Erro ao processar detalhes: {str(detail_e)}")
    except Exception as e:
        print(f"❌ Exceção durante a busca de voos: {str(e)}")

def check_api_responses(service):
    """Analisa e verifica as respostas da API"""
    print_section("VERIFICAÇÃO DE RESPOSTAS DA API")
    
    # Testar URL específica para diagnóstico
    print("\nTestando endpoint específico para diagnóstico...")
    token = service.get_token()
    
    if not token:
        print("❌ Sem token de autenticação, não é possível testar endpoints.")
        return
    
    try:
        # Testar um endpoint básico que deve funcionar se a autenticação estiver correta
        url = f"{service.base_url}/reference-data/locations"
        params = {"keyword": "PAR", "subType": "CITY"}
        headers = {"Authorization": f"Bearer {token}"}
        
        import requests
        response = requests.get(url, headers=headers, params=params)
        
        print(f"Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API respondeu corretamente!")
            result = response.json()
            data_count = len(result.get('data', []))
            print(f"Resultados encontrados: {data_count}")
        else:
            print(f"❌ API retornou erro: {response.text}")
    except Exception as e:
        print(f"❌ Exceção durante o teste de endpoint: {str(e)}")

def optimization_recommendations():
    """Recomendações para otimização"""
    print_section("OTIMIZAÇÃO E MELHORIAS")
    
    recommendations = [
        "1. Implementar cache de resultados para reduzir o número de chamadas à API",
        "2. Utilizar tratamento de exceções mais específico para cada tipo de erro da API",
        "3. Adicionar retry automático para falhas temporárias de rede",
        "4. Implementar logging estruturado para facilitar diagnóstico de problemas",
        "5. Utilizar sessões persistentes do requests para melhorar desempenho",
        "6. Configurar timeouts adequados para evitar bloqueios em caso de lentidão da API",
        "7. Verificar regularmente a validade do token e renovar proativamente",
        "8. Implementar monitoramento em tempo real das chamadas à API"
    ]
    
    for rec in recommendations:
        print(rec)
    
    # Exemplo de código otimizado
    print("\nExemplo de código otimizado para requisições:")
    code_example = """
    def search_flights(self, params):
        # Implementar cache para evitar requisições repetidas
        cache_key = json.dumps(params, sort_keys=True)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Usar sessão persistente
        with self.session as session:
            try:
                # Verificar e renovar token automaticamente
                token = self.ensure_valid_token()
                
                headers = {"Authorization": f"Bearer {token}"}
                
                # Configurar timeouts
                response = session.get(
                    f"{self.base_url}/shopping/flight-offers",
                    headers=headers,
                    params=params,
                    timeout=(3.05, 30)  # (connect, read) timeouts
                )
                
                # Implementar retries para falhas de rede
                retries = 3
                while retries > 0 and response.status_code >= 500:
                    time.sleep(1)
                    response = session.get(
                        f"{self.base_url}/shopping/flight-offers",
                        headers=headers,
                        params=params,
                        timeout=(3.05, 30)
                    )
                    retries -= 1
                
                response.raise_for_status()
                result = response.json()
                
                # Armazenar em cache
                self.cache.set(cache_key, result, ttl=600)  # TTL de 10 minutos
                
                return result
            except requests.exceptions.ConnectTimeout:
                logging.error("Timeout ao conectar com a API Amadeus")
                return {"error": "Timeout de conexão"}
            except requests.exceptions.ReadTimeout:
                logging.error("Timeout ao ler resposta da API Amadeus")
                return {"error": "Timeout de leitura"}
            except requests.exceptions.HTTPError as http_err:
                logging.error(f"Erro HTTP {http_err.response.status_code}: {http_err.response.text}")
                return {"error": f"Erro HTTP {http_err.response.status_code}", "details": http_err.response.text}
            except Exception as e:
                logging.error(f"Erro inesperado: {str(e)}")
                return {"error": f"Erro inesperado: {str(e)}"}
    """
    print(code_example)

def main():
    """Função principal de diagnóstico"""
    print_section("DIAGNÓSTICO DE INTEGRAÇÃO COM API AMADEUS")
    print("Data e hora: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Verificar ambiente
    check_environment()
    
    # Criar instância do serviço Amadeus
    try:
        service = AmadeusService()
        
        # Executar testes
        test_authentication(service)
        test_configuration(service)
        test_api_requests(service)
        check_api_responses(service)
        optimization_recommendations()
        
        print_section("DIAGNÓSTICO CONCLUÍDO")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE DIAGNÓSTICO: {str(e)}")

if __name__ == "__main__":
    # Corrigir dependência faltante
    import pandas as pd
    
    # Executar diagnóstico
    main()
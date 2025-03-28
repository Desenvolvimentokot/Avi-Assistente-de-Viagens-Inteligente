#!/usr/bin/env python3
import json
import logging
import sys
import requests
import os
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('amadeus_endpoints_test')

class AmadeusEndpointTester:
    """Classe para testar os diferentes endpoints da API Amadeus"""
    
    def __init__(self):
        """Inicializa o tester com as credenciais da API"""
        self.api_key = os.environ.get('AMADEUS_API_KEY')
        self.api_secret = os.environ.get('AMADEUS_API_SECRET')
        self.base_url = 'https://test.api.amadeus.com/v1'
        self.token = None
        
        # Verificar se as credenciais estão definidas
        if not self.api_key or not self.api_secret:
            logger.error("Credenciais Amadeus não configuradas. Configure as variáveis de ambiente AMADEUS_API_KEY e AMADEUS_API_SECRET.")
            sys.exit(1)
        
        # Obter token de autenticação
        self._get_token()
        
    def _get_token(self):
        """Obtém o token de autenticação da API Amadeus"""
        url = f"{self.base_url}/security/oauth2/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            self.token = result.get('access_token')
            logger.info(f"Token de autenticação obtido com sucesso: {self.token[:10]}...")
            
            return self.token
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter token: {str(e)}")
            if hasattr(e, 'response') and getattr(e, 'response', None):
                logger.error(f"Detalhes: {e.response.text}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Erro inesperado ao obter token: {str(e)}")
            sys.exit(1)
    
    def test_endpoint(self, path, method='get', params=None, json_data=None):
        """
        Testa um endpoint específico da API Amadeus
        
        Args:
            path: Caminho do endpoint (sem o base_url)
            method: Método HTTP (get, post)
            params: Parâmetros da query string para GET
            json_data: Dados JSON para POST
            
        Returns:
            dict: Resultado do teste com status e detalhes
        """
        if not self.token:
            return {
                'endpoint': path,
                'status': 'ERROR',
                'code': 'NO_TOKEN',
                'message': 'Token de autenticação não disponível'
            }
        
        url = f"{self.base_url}/{path}"
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        if method.lower() == 'post' and json_data:
            headers['Content-Type'] = 'application/json'
        
        logger.info(f"Testando endpoint: {url}")
        
        try:
            if method.lower() == 'get':
                response = requests.get(url, headers=headers, params=params)
            else:  # POST
                response = requests.post(url, headers=headers, json=json_data)
            
            status_code = response.status_code
            logger.info(f"Status da resposta: {status_code}")
            
            # Analisar resposta
            try:
                response_data = response.json()
            except:
                response_data = {'text': response.text}
            
            # Verificar erros comuns
            error_info = None
            if status_code != 200:
                if "InvalidAPICallAsNoApiProductMatchFound" in response.text:
                    error_info = "Permissão de API insuficiente para este endpoint. Verifique sua assinatura."
                elif "invalid_client" in response.text:
                    error_info = "Credenciais de cliente inválidas."
                elif "access_denied" in response.text:
                    error_info = "Acesso negado a este recurso."
                elif status_code == 404:
                    error_info = "Endpoint não encontrado ou indisponível."
                elif status_code == 429:
                    error_info = "Limite de requisições excedido."
                elif status_code >= 500:
                    error_info = "Erro no servidor da API."
                else:
                    error_info = f"Erro desconhecido: {response.text}"
            
            return {
                'endpoint': path,
                'url': url,
                'method': method.upper(),
                'status': 'SUCCESS' if status_code == 200 else 'ERROR',
                'code': status_code,
                'error': error_info,
                'data': response_data if status_code == 200 and response_data else None
            }
            
        except Exception as e:
            logger.error(f"Erro ao testar endpoint {url}: {str(e)}")
            return {
                'endpoint': path,
                'url': url,
                'method': method.upper(),
                'status': 'EXCEPTION',
                'code': 'EXCEPTION',
                'error': str(e)
            }
    
    def test_all_endpoints(self):
        """Testa os principais endpoints da API Amadeus"""
        endpoints = [
            # Reference Data APIs
            {
                'name': 'Locations (Cities)',
                'path': 'reference-data/locations',
                'method': 'get',
                'params': {'keyword': 'PAR', 'subType': 'CITY'}
            },
            {
                'name': 'Locations (Airports)',
                'path': 'reference-data/locations',
                'method': 'get',
                'params': {'keyword': 'JFK', 'subType': 'AIRPORT'}
            },
            {
                'name': 'Airlines',
                'path': 'reference-data/airlines',
                'method': 'get',
                'params': {'airlineCodes': 'BA'}
            },
            
            # Shopping APIs
            {
                'name': 'Flight Offers Search v2',
                'path': 'shopping/flight-offers',
                'method': 'get',
                'params': {
                    'originLocationCode': 'GRU',
                    'destinationLocationCode': 'CDG',
                    'departureDate': (datetime.now().strftime('%Y-%m-28')),
                    'adults': 1,
                    'max': 2
                }
            },
            {
                'name': 'Flight Cheapest Date Search',
                'path': 'shopping/flight-dates',
                'method': 'get',
                'params': {
                    'origin': 'GRU',
                    'destination': 'CDG'
                }
            },
            {
                'name': 'Hotel Offers Search v2',
                'path': 'v2/shopping/hotel-offers',
                'method': 'get',
                'params': {
                    'cityCode': 'PAR',
                    'adults': 1
                }
            },
            
            # Trip APIs
            {
                'name': 'Trip Purpose Prediction',
                'path': 'travel/predictions/trip-purpose',
                'method': 'get',
                'params': {
                    'originLocationCode': 'GRU',
                    'destinationLocationCode': 'CDG',
                    'departureDate': (datetime.now().strftime('%Y-%m-28')),
                    'returnDate': (datetime.now().strftime('%Y-%m-30'))
                }
            }
        ]
        
        results = []
        for endpoint in endpoints:
            result = self.test_endpoint(
                endpoint['path'],
                endpoint['method'],
                endpoint.get('params'),
                endpoint.get('json_data')
            )
            result['name'] = endpoint['name']
            results.append(result)
        
        return results
    
    def generate_report(self, results):
        """Gera um relatório formatado dos resultados de testes"""
        print("\n" + "="*80)
        print(" RELATÓRIO DE TESTE DOS ENDPOINTS DA API AMADEUS ".center(80, "="))
        print("="*80 + "\n")
        
        print(f"Data do teste: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Ambiente: {'Produção' if 'api.amadeus.com' in self.base_url else 'Teste/Sandbox'}")
        print(f"URL Base: {self.base_url}\n")
        
        # Resumo
        successful = sum(1 for r in results if r['status'] == 'SUCCESS')
        print(f"Resultado: {successful} de {len(results)} endpoints testados com sucesso.\n")
        
        # Detalhes de cada endpoint
        print("Detalhes dos testes:\n")
        
        for i, result in enumerate(results, 1):
            status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
            print(f"{i}. {status_icon} {result['name']}")
            print(f"   Endpoint: {result['method']} {result['endpoint']}")
            print(f"   Status: {result['code']} ({result['status']})")
            
            if result['status'] != 'SUCCESS' and result.get('error'):
                print(f"   Erro: {result['error']}")
            
            if result['status'] == 'SUCCESS' and result.get('data'):
                # Mostrar apenas um resumo dos dados
                data = result['data']
                if isinstance(data, dict):
                    if 'meta' in data:
                        print(f"   Meta: {data['meta']}")
                    
                    if 'data' in data and isinstance(data['data'], list):
                        print(f"   Resultados: {len(data['data'])} itens encontrados")
            
            print("")  # Linha em branco entre resultados
        
        # Recomendações
        unauthorized_endpoints = [r['name'] for r in results if "Permissão de API insuficiente" in str(r.get('error', ''))]
        
        if unauthorized_endpoints:
            print("\nRecomendações:")
            print("  Os seguintes endpoints requerem permissões adicionais na sua conta Amadeus:")
            for ep in unauthorized_endpoints:
                print(f"   - {ep}")
            print("\n  Para acessar esses endpoints, você precisa:")
            print("   1. Fazer login no portal de desenvolvedores do Amadeus (https://developers.amadeus.com)")
            print("   2. Verificar sua assinatura atual e os endpoints disponíveis")
            print("   3. Fazer upgrade do plano ou solicitar acesso aos endpoints necessários")

def main():
    """Função principal"""
    try:
        tester = AmadeusEndpointTester()
        results = tester.test_all_endpoints()
        tester.generate_report(results)
    except Exception as e:
        logger.error(f"Erro durante a execução do teste: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
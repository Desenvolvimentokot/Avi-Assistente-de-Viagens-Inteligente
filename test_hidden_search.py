"""
Script para testar a funcionalidade de busca oculta (iframe)
Este script testa manualmente a abertura da página de busca oculta com parâmetros.
"""

import requests
import json
import webbrowser
import time
from urllib.parse import urlencode

# Configuração de teste
BASE_URL = "http://localhost:5000"
TEST_PARAMS = {
    "origin": "GRU",
    "destination": "MCZ",
    "departure_date": "2025-05-20",
    "return_date": "2025-05-26",
    "adults": 1,
    "session_id": "test-session-123"
}

def test_hidden_search_page():
    """Testa a abertura direta da página de busca oculta."""
    params = urlencode(TEST_PARAMS)
    url = f"{BASE_URL}/hidden-search?{params}"
    
    print(f"Abrindo página de busca oculta: {url}")
    webbrowser.open(url)
    
    print("Página aberta! Você deve estar vendo a interface de teste com:")
    print(f"- Origem: {TEST_PARAMS['origin']}")
    print(f"- Destino: {TEST_PARAMS['destination']}")
    print(f"- Data ida: {TEST_PARAMS['departure_date']}")
    print(f"- Data volta: {TEST_PARAMS['return_date']}")
    print(f"- Passageiros: {TEST_PARAMS['adults']}")
    print("")
    print("A página deve mostrar o widget do Trip.com e estar buscando voos.")

def test_api_initiate_search():
    """Testa a API que inicia uma busca oculta."""
    url = f"{BASE_URL}/api/initiate-hidden-search"
    
    payload = {
        "flight_info": {
            "origin": TEST_PARAMS["origin"],
            "destination": TEST_PARAMS["destination"],
            "departure_date": TEST_PARAMS["departure_date"],
            "return_date": TEST_PARAMS["return_date"],
            "adults": TEST_PARAMS["adults"]
        },
        "session_id": TEST_PARAMS["session_id"]
    }
    
    print(f"Enviando requisição POST para {url} com payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2)}")
        
        # Se a resposta tiver URL, abrir
        if response.status_code == 200 and response.json().get("success"):
            if response.json().get("url"):
                full_url = f"{BASE_URL}{response.json().get('url')}"
                print(f"Abrindo URL da resposta: {full_url}")
                webbrowser.open(full_url)
            else:
                print("URL não encontrada na resposta.")
        
    except Exception as e:
        print(f"Erro ao chamar API: {str(e)}")

if __name__ == "__main__":
    print("Teste da busca oculta (agora visível)")
    print("-------------------------------------")
    print("1. Testando acesso direto à página de busca")
    test_hidden_search_page()
    
    print("\n\n")
    print("2. Testando API de iniciar busca")
    # Descomente para testar também a API
    # test_api_initiate_search()
#!/usr/bin/env python3
import json
from services.amadeus_service_optimized import AmadeusService

def main():
    print("=== TESTE DE AUTENTICAÇÃO AMADEUS ===")
    service = AmadeusService()
    result = service.test_connection()
    
    # Exibir resultado formatado
    print(json.dumps(result, indent=2))
    
    # Status simplificado
    if result["success"]:
        print("\n✅ Conexão estabelecida com sucesso!")
        print(f"Token: {result['token']['value']}")
        print(f"Expira em: {result['token']['expires_in']} segundos")
    else:
        print("\n❌ Falha na conexão!")
        if result["errors"]:
            for error in result["errors"]:
                print(f"- {error}")

if __name__ == "__main__":
    main()
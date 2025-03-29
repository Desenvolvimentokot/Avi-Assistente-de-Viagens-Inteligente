#!/usr/bin/env python3
import requests
import json
import logging
import uuid
import os
from flask import Flask, jsonify

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Example route (replace with your actual routes)
@app.route('/api/test/flight_results')
def test_flight_results_api():
    """
    Endpoint de teste para verificar a funcionalidade do painel lateral
    Tenta buscar dados reais da API Amadeus, com fallback para dados simulados
    """
    try:
        # Tentar buscar dados reais da API Amadeus
        from services.amadeus_service import AmadeusService

        amadeus_service = AmadeusService()
        # Definir para não usar dados simulados
        amadeus_service.use_mock_data = False

        test_params = {
            'originLocationCode': 'GRU',
            'destinationLocationCode': 'MIA',
            'departureDate': '2025-05-01',
            'returnDate': '2025-05-10',
            'adults': 1,
            'currencyCode': 'BRL',
            'max': 5
        }

        # Verificar conexão com Amadeus
        conn_test = amadeus_service.test_connection()
        logging.info(f"Teste de conexão Amadeus: {conn_test}")

        # Tentar obter dados reais
        results = amadeus_service.search_flights(test_params)

        # Verificar se houve erro ou se não há dados
        if 'error' in results or not results.get('data'):
            logging.warning(f"Usando dados simulados após falha na API: {results.get('error', 'Sem dados')}")
            # Obter dados simulados como fallback
            results = amadeus_service._get_mock_flights(test_params)
            results['is_simulated'] = True
        else:
            logging.info(f"Sucesso! Dados REAIS obtidos da API Amadeus: {len(results.get('data', []))} resultados")
            results['is_simulated'] = False

        # Retornar para testes do painel
        return jsonify(results)
    except Exception as e:
        logging.error(f"Erro ao processar requisição: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


if __name__ == "__main__":
    app.run(debug=True)
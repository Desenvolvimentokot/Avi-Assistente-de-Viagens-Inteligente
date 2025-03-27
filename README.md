# Flai - Assistente de Viagens Inteligente

## Configuração da API Amadeus

Este projeto utiliza a API Amadeus para busca de voos. As credenciais já estão armazenadas nos Secrets do Replit:

- `AMADEUS_API_KEY`: Chave de API do Amadeus
- `AMADEUS_API_SECRET`: Segredo da API do Amadeus

### Funcionalidades da Integração Amadeus

1. **Autenticação OAuth 2.0**: O sistema gera automaticamente tokens de acesso para a API Amadeus.
2. **Busca de Ofertas de Voos**: Endpoint `/api/search-flights` permite buscar voos com os seguintes parâmetros:
   - `origin`: Código IATA do aeroporto de origem (ex: GRU para Guarulhos)
   - `destination`: Código IATA do aeroporto de destino (ex: JFK para Nova York)
   - `departure_date`: Data de partida no formato YYYY-MM-DD
   - `return_date`: Data de retorno no formato YYYY-MM-DD (opcional)
   - `adults`: Número de adultos (padrão: 1)

### Exemplo de Uso

```
GET /api/search-flights?origin=GRU&destination=JFK&departure_date=2025-04-18&return_date=2025-04-28&adults=2
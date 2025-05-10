# Migração para TravelPayouts REST API

## Visão Geral

Este documento detalha a migração da integração com o TravelPayouts de uma abordagem baseada em Playwright (automação de browser) para uma abordagem baseada em API REST direta. Esta mudança traz vários benefícios importantes:

1. **Melhor performance**: Chamadas de API REST são significativamente mais rápidas que automação de browser
2. **Maior estabilidade**: Elimina problemas de renderização de página, tempos limite e falhas de extração de dados
3. **Simplificação do código**: Redução da complexidade de manipulação do DOM e espera por elementos
4. **Manutenção simplificada**: Menor dependência de estruturas de HTML que podem mudar
5. **Uso oficial de APIs**: Utilização de canais oficiais fornecidos pelo TravelPayouts

## Componentes Principais

A nova implementação é baseada nos seguintes componentes:

### 1. TravelPayoutsRestAPI

Esta classe fornece métodos específicos para interagir diretamente com os diferentes endpoints da API REST do TravelPayouts:

- Busca de preços de calendário (mensal)
- Busca de preços mais baratos para uma data específica
- Busca de matriz de preços para um mês inteiro
- Criação de links de redirecionamento quando não há dados disponíveis

Localização: `services/travelpayouts_rest_api.py`

### 2. TravelPayoutsConnector

O conector foi atualizado para usar exclusivamente a nova API REST em vez da automação de browser. Ele mantém a mesma interface para garantir compatibilidade com o código existente, mas internamente usa apenas chamadas REST.

Localização: `services/travelpayouts_connector.py`

### 3. Rotas e Endpoints

Os endpoints existentes foram preservados, mas atualizados para usar a nova implementação REST:

- `/widget/direct_search` - Busca direta de voos
- `/widget/search` - Inicia uma busca (compatibilidade com código anterior)
- `/widget/status` - Verifica o status da busca (compatibilidade)
- `/widget/results` - Obtém os resultados da busca (compatibilidade)

Uma nova rota de demonstração foi adicionada para mostrar a funcionalidade da API REST:

- `/widget/rest-demo` - Interface para testar a busca via API REST direta

## Como Funciona

### 1. Fluxo de Busca Direta

1. Cliente envia solicitação para `/widget/direct_search` com parâmetros de busca
2. O sistema usa `TravelPayoutsConnector` para buscar dados
3. O conector usa `TravelPayoutsRestAPI` para fazer chamadas REST diretas
4. A API tenta buscar dados em várias fontes (calendário, preços baratos, matriz)
5. Os resultados são formatados de forma consistente e retornados ao cliente

### 2. Tratamento de Erros e Fallbacks

- Se uma fonte de dados falhar, a API tenta a próxima fonte
- Se todas as fontes falharem, é gerado um link de redirecionamento para o widget do TravelPayouts
- Erros de conexão e dados inválidos são tratados de forma robusta

### 3. Integração no Chat

O sistema de chat da AVI continua funcionando sem alterações, recebendo os mesmos dados que antes, mas agora obtidos diretamente via API REST em vez de automação de browser.

## Benefícios

### 1. Performance

- Tempo de resposta reduzido de 5-10 segundos para menos de 1 segundo
- Menor uso de CPU e memória sem necessidade de browser headless

### 2. Confiabilidade

- Eliminação de falhas por mudanças na estrutura HTML
- Menor probabilidade de falhas por tempo limite

### 3. Manutenção

- Código mais simples e direto
- Dependências reduzidas (não requer Playwright)
- Atualizações mais fáceis ao lidar apenas com endpoints de API

## Exemplos de Uso

### Busca Simples de Voos

```python
from services.travelpayouts_rest_api import travelpayouts_api

# Buscar voos diretamente
results = travelpayouts_api.search_flights(
    origin="GRU",
    destination="JFK",
    departure_date="2025-06-15"
)

# Processar resultados
for flight in results:
    print(f"Voo: {flight['id']}")
    print(f"Preço: {flight['price']['total']} {flight['price']['currency']}")
    print(f"URL de Reserva: {flight['booking_url']}")
```

### Integração com o Chat

A integração com o chat continua a mesma, mas agora usa a API REST:

```python
# No manipulador do chat, quando extraímos informações de viagem
travel_info = {
    "origin": "GRU",
    "destination": "LIS",
    "departure_date": "2025-07-10",
    "return_date": "2025-07-20",
    "adults": 2
}

# Usar o conector atualizado (que agora usa API REST)
results = travelpayouts_connector.search_flights_from_chat(
    travel_info=travel_info,
    session_id=session_id
)

# Resultados agora vêm diretamente da API REST
```

## Considerações Futuras

1. **Cache de Resultados**: Implementar um sistema de cache para resultados frequentes
2. **Expansão para Hotéis**: Considerar a integração de APIs de hotel do TravelPayouts
3. **Métricas de Performance**: Monitorar tempos de resposta e taxas de sucesso da API
4. **Fallback Avançado**: Desenvolver lógica mais sofisticada para quando certas APIs falhem

---

*Documento atualizado em 10 de maio de 2025*
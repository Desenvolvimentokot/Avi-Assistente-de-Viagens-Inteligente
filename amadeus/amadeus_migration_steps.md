# Passos para Migração do Amadeus Service para SDK Oficial

## 1. Backup do Serviço Atual

Antes de qualquer modificação, vamos fazer backup do serviço atual para garantir que possamos reverter se necessário.

```bash
cp services/amadeus_service.py services/amadeus_service_backup.py
```

## 2. Substituição do Serviço

Substituir o serviço atual pelo novo serviço baseado no SDK:

```bash
cp services/amadeus_service_sdk.py services/amadeus_service.py
```

## 3. Ajustes na Implementação

### 3.1 Verificação de Interface

O novo serviço deve manter a mesma interface pública do serviço atual:

- `get_token()`
- `search_flights(params)`
- `search_hotels(params)`
- `search_hotel_offers(params)`
- `get_flight_price(flight_offer)`
- `get_hotel_offer(offer_id)`
- `test_connection()`

### 3.2 Formato de Resposta

O novo serviço deve manter o mesmo formato de resposta para garantir compatibilidade com o código existente:

```python
# Formato atual de resposta
{
    "data": [...],  # Dados de voos/hotéis
    "error": "mensagem de erro"  # Opcional, presente apenas em caso de erro
}
```

## 4. Testes Específicos

### 4.1 Teste de Integração com app.py

Testar os endpoints que usam o serviço Amadeus:
- `/api/search` com type=flights
- `/api/search` com type=hotels

### 4.2 Teste de Integração com busca_rapida_service.py

Testar a função `search_flights()` que utiliza o serviço Amadeus como fallback.

## 5. Implementação da Migração

1. Criar versão modificada do serviço baseado no SDK que seja compatível com a interface atual
2. Implementar o método `get_token()` que retorne um objeto compatível
3. Garantir que os métodos retornem o mesmo formato de dados
4. Ajustar tratamento de erros para compatibilidade

## 6. Monitoramento Pós-Migração

1. Adicionar logs detalhados para monitorar chamadas à API
2. Verificar taxa de sucesso vs. erro
3. Medir tempo de resposta
4. Monitorar uso da quota da API

## 7. Rollback Plan

Em caso de problemas, restaurar o backup:

```bash
cp services/amadeus_service_backup.py services/amadeus_service.py
```
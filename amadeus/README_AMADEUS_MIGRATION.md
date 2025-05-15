# Migração do Serviço Amadeus

## Resumo da Alteração

O serviço de integração com a API Amadeus foi migrado da implementação personalizada para o SDK oficial da Amadeus. Esta migração resolve problemas de acesso ao endpoint `/v2/shopping/flight-offers` e melhora a robustez da integração.

## Arquivos Alterados

- `services/amadeus_service.py` - Substituído pela implementação baseada no SDK

## Arquivos de Backup

- `services/amadeus_service_backup.py` - Backup da implementação original

## Como Testar a Nova Implementação

Execute o script de teste funcional para verificar se a nova implementação está funcionando corretamente:

```bash
python test_amadeus_service_funcional.py
```

O script testará as principais funcionalidades:
1. Busca de voos
2. Verificação de preços

## Procedimento de Rollback

Se surgirem problemas com a nova implementação, siga este procedimento para reverter para a implementação anterior:

1. Substitua o arquivo do serviço com o backup:

```bash
cp services/amadeus_service_backup.py services/amadeus_service.py
```

2. Reinicie o servidor da aplicação:

```bash
# Se estiver usando Flask
kill -HUP $(pgrep -f "gunicorn main:app")

# Ou reinicie o workflow
# [Instruções para reiniciar o workflow específico da sua plataforma]
```

3. Verifique se a aplicação voltou a funcionar com a implementação original.

## Documentação Adicional

Para mais informações sobre a migração e implementação, consulte:

- [Relatório de Implementação do SDK](./amadeus_sdk_implementation_report.md)
- [Passos de Migração](./amadeus_migration_steps.md)
- [Testes de Migração](./test_amadeus_migration.py)
- [Testes Funcionais](./test_amadeus_service_funcional.py)

## Dependências

A nova implementação requer o SDK oficial da Amadeus:

```
pip install amadeus
```

Esta dependência foi adicionada aos requisitos do projeto.

## Monitoramento

Após a migração, monitore os logs da aplicação para verificar:

- Taxa de sucesso das chamadas à API
- Tempo de resposta das chamadas
- Mensagens de erro relacionadas à API Amadeus

## Contato

Em caso de problemas com a migração, entre em contato com:

- Equipe de Desenvolvimento
- Administrador do Projeto
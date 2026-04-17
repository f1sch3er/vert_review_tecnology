# 🏦 Financial Transaction Ledger - Backend Training (VERT)

Este projeto é um simulador de sistema de liquidação financeira desenvolvido para treinar competências de Engenharia Backend Pleno, com foco em **Python/Django**, **Mensageria (Kafka/RabbitMQ)** e **Integridade de Dados**.

## 🎯 Objetivos de Aprendizagem
O foco é demonstrar senioridade em sistemas críticos, abordando:
1.  **Consistência de Dados:** Garantir que o saldo nunca fique inconsistente em ambientes concorrentes.
2.  **Idempotência:** Evitar duplicação de transações em caso de falhas de rede.
3.  **Arquitetura de Eventos:** Desacoplar processos pesados da API principal.

---

## 🚀 Guia de Implementação (To-Do List)

### Fase 1: Infraestrutura e Modelagem (O "Coração")
- [ ] **Dockerização:** Criar um `docker-compose.yml` com PostgreSQL, Redis e Kafka/RabbitMQ.
- [ ] **Database Schema:** - Tabela `Accounts`: ID, Nome, Saldo.
    - Tabela `Transactions`: ID Único, Conta Origem, Valor, Tipo (Credit/Debit), Status, IdempotencyKey.
- [ ] **Constraints de Banco:** Implementar uma `CheckConstraint` no Django para garantir que o saldo da conta nunca seja negativo.

### Fase 2: API de Transações & Resiliência
- [ ] **Atomicidade:** Usar `transaction.atomic` para garantir que a transação só seja salva se o saldo for atualizado com sucesso.
- [ ] **Locking Pessimista:** Implementar `select_for_update()` no Django para evitar o problema de "Lost Update" quando dois processos tentam atualizar a mesma conta ao mesmo tempo.
- [ ] **Mecanismo de Idempotência:** Criar um Middleware ou Decorator que valide a `X-Idempotency-Key` no header das requisições para evitar duplicidade.

### Fase 3: Mensageria e Assincronismo
- [ ] **Producer (Django):** Após o commit da transação, disparar um evento `transaction_created` para o tópico do Kafka.
- [ ] **Consumer (Worker):** Criar um script Python independente que consome o tópico e simula o processamento de um recibo ou notificação.
- [ ] **DLQ (Dead Letter Queue):** Implementar uma lógica básica para mensagens que falham no processamento (ex: salvar num log de erros para reprocessamento).

### Fase 4: Dados e Observabilidade
- [ ] **Queries Avançadas:** Criar um endpoint de "Fechamento Diário" utilizando SQL puro ou Django `Aggregate` para somar volumes transacionados por período.
- [ ] **Logging Estruturado:** Configurar o log do sistema para imprimir em formato JSON, facilitando a análise de erros.
- [ ] **Health Checks:** Implementar uma rota que valide a conexão com o banco e o broker de mensagens.

---

## 🛠️ Tecnologias Sugeridas
- **Linguagem:** Python 3.11+
- **Framework:** Django & Django REST Framework (DRF)
- **Banco de Dados:** PostgreSQL
- **Mensageria:** Confluent Kafka ou RabbitMQ
- **Testes:** Pytest (Foco em Testes de Integração e Concorrência)

---

## 💡 Como testar este sistema?
1. **Teste de Concorrência:** Simular 10 requisições simultâneas de saque numa conta com apenas 100 reais de saldo. O sistema deve permitir apenas uma e rejeitar as outras com erro de concorrência.
2. **Teste de Idempotência:** Enviar a mesma transação duas vezes com a mesma chave. A segunda deve retornar `200 OK` (ou `409 Conflict`) com o resultado da primeira, sem descontar o valor novamente.
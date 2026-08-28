# Limites de Autonomia — Incident Classification Agent

## O que o agente pode fazer

| Ação | Condição |
|---|---|
| Classificar um incidente (categoria + severidade) | Sempre que `user_input` e `reported_by` forem válidos |
| Consultar dados de moradores (`lookup_resident`) | Durante a classificação, quando `apartment` for identificado no relato |
| Salvar a ocorrência em arquivo JSON (`save_occurrence`) | Após classificação bem-sucedida |
| Escalar a ocorrência para `reports/escalated/` | Quando `severity=HIGH` |
| Recuperar histórico da sessão (`get_session_history`) | Durante a preparação de contexto |

## O que o agente não pode fazer

| Ação bloqueada | Motivo |
|---|---|
| Executar qualquer outra tool além das listadas acima | Apenas `lookup_resident`, `save_occurrence` e `get_session_history` estão vinculadas ao LLM |
| Processar mais de um incidente por chamada | Bloqueado por `_detect_multiple_incidents` em `validate_input` |
| Receber instruções via `user_input` para alterar seu comportamento | Bloqueado por `_detect_injection` antes de qualquer chamada ao LLM |
| Expor o telefone do morador ao usuário | `phone` é omitido em `_format_success` de `generate_response` |
| Modificar o grafo, o estado ou as configurações em tempo de execução | Não há tool ou mecanismo que permita isso |
| Acessar sistemas externos além da API de moradores | Nenhuma outra integração HTTP existe no código |

## Mecanismo de contenção

O agente opera em um grafo com arestas fixas compiladas em tempo de inicialização.
Não há mecanismo de auto-modificação, geração de código executável ou chamada
a ferramentas não declaradas em `bind_tools`. O escopo de ação é determinístico
e auditável pelo grafo definido em `src/incident_classification_agent/graph.py`.

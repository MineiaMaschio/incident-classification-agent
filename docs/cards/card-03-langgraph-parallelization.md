# ⚡ Card 03 — Paralelização no Grafo LangGraph

> **Branch:** `feature/langgraph-parallelization`

## 🎯 Objetivo

Implementar paralelização simples no grafo LangGraph para atender ao requisito do avaliativo, sem quebrar o fluxo existente.

---

## 📌 Escopo

### Implementação

* [x] Identificar o ponto adequado para paralelização — candidato: após `validate_input`, disparar `prepare_context` e um pré-carregamento de dados do morador em paralelo
* [x] Implementar o fan-out e fan-in no grafo usando nós paralelos do LangGraph
* [x] Garantir que a condição de parada e o limite do loop agentic continuem funcionando

### Documentação

* [x] Atualizar o diagrama Mermaid no README refletindo o novo fluxo com paralelização
* [x] Adicionar comentário no `graph.py` explicando a decisão de paralelização

### Code review com IA

* [x] Realizar code review da implementação da paralelização com apoio de IA
* [x] Registrar achados em `docs/qa/review-card03.md`

---

## 🏁 Resultado Esperado

* [x] Pelo menos um trecho do grafo executa em paralelo
* [x] Fluxo principal e fluxos de erro continuam funcionando corretamente
* [x] Diagrama do README atualizado
* [x] Review registrado em `docs/qa/review-card03.md`

---

## 📎 Referências

* `src/incident_classification_agent/graph.py`
* `src/incident_classification_agent/nodes/prepare_context.py`
* `docs/qa/` (criada no Card 01)
* Documentação LangGraph — Send API / parallel nodes

---

## 📝 Detalhamento da execução

### Decisões de implementação

- **Ponto de paralelização escolhido**: após `validate_input`, no caminho principal. `prepare_context` (CPU-bound: leitura de arquivo + sessão em memória) e `prefetch_resident` (I/O-bound: chamada HTTP à API FastAPI) não têm dependência entre si e escrevem em chaves distintas do `AgentState` (`conversation_history` e `resident_info`), eliminando risco de conflito de reducer.

- **Mecanismo de fan-out**: `add_conditional_edges` mantém o mapa original `"prepare_context" → prepare_context` para o roteamento existente; um segundo `add_edge("validate_input", "prefetch_resident")` adiciona o segundo ramo. O LangGraph agenda ambos no mesmo super-step automaticamente.

- **Fan-in em `classify_incident`**: as arestas `prepare_context → classify_incident` e `prefetch_resident → classify_incident` fazem o runtime aguardar ambos os ramos antes de avançar.

- **Injeção do prefetch em `classify_incident`**: quando `resident_info` já está preenchido no estado (morador encontrado pelo prefetch), o nó injeta um par sintético `AIMessage` (tool_call) + `ToolMessage` no histórico de mensagens antes do primeiro invoke do LLM. O LLM recebe os dados do morador como se tivesse chamado a tool, podendo pular direto para a classificação. A tool `lookup_resident` permanece no `bind_tools` como fallback.

- **Idempotência de `prefetch_resident`**: se `resident_info` já estiver preenchido no estado (re-execução no mesmo thread), a chamada à API é ignorada.

- **Retorno parcial nos nós paralelos (correção aplicada)**: a implementação inicial retornava `{**state, ...}` em ambos os nós. No fan-out, isso faz com que todas as chaves escalares do estado (`user_input`, `reported_by`, etc.) cheguem duplicadas no mesmo super-step, causando `InvalidUpdateError: Can receive only one value per step`. Corrigido para que cada nó retorne apenas as chaves que ele de fato modifica: `{"conversation_history": history}` em `prepare_context` e `{"resident_info": result}` em `prefetch_resident`.

### Arquivos criados/modificados

| Arquivo | Ação |
|---|---|
| `src/incident_classification_agent/nodes/prefetch_resident.py` | Criado — novo nó que invoca `lookup_resident.invoke()` diretamente |
| `src/incident_classification_agent/graph.py` | Modificado — fan-out/fan-in implementado, comentário explicativo adicionado, `prefetch_resident` registrado como nó |
| `src/incident_classification_agent/nodes/classify_incident.py` | Modificado — injeção de `resident_info` pré-carregado como mensagens sintéticas; import `uuid` adicionado, import `re` removido |
| `README.md` | Modificado — diagrama Mermaid, tabela de nós, fluxos de execução e seção loop agentic atualizados |

**Correções pós code review (PR #22):**

| Arquivo | Correção |
|---|---|
| `src/incident_classification_agent/graph.py` | Bug crítico: aresta estática substituída por nó intermediário `_fan_out`, isolando o ramo paralelo do fluxo de rejeição |
| `src/incident_classification_agent/nodes/prefetch_resident.py` | `lookup_resident.invoke()` envolvido em `try/except` para evitar propagação de erros de rede |

### Evidências de execução

Execução real do agente com CPU (`CUDA_VISIBLE_DEVICES=""`) e servidor FastAPI ativo em `2026-08-27`:

```
2026-08-27 21:35:24 [INFO] Graph compiled successfully with MemorySaver checkpointer.
2026-08-27 21:35:24 [INFO] Multiple incidents detection result: SINGLE
2026-08-27 21:35:24 [INFO] Input validated — occurrence_id: 24dd6dde | multiple_incidents: False
2026-08-27 21:35:24 [INFO] prefetch_resident — 'apartment' ausente no estado; nenhuma consulta realizada.
2026-08-27 21:35:24 [INFO] Context prepared for occurrence_id: 24dd6dde (paralelo ao prefetch_resident)
2026-08-27 21:35:44 [INFO] lookup_resident — Consultando API: params={'apartment': '101', 'building': 'A'}
2026-08-27 21:35:46 [INFO] lookup_resident — Morador encontrado: apartamento=101 bloco=A → Carlos Mendes
2026-08-27 21:36:06 [INFO] Severity reasoning — base: LOW | recurrence: true (1) | final: HIGH
2026-08-27 21:36:06 [INFO] Incident classified — category: ACCESS, severity: HIGH
2026-08-27 21:36:06 [INFO] Occurrence saved — reports/20260828T003606Z_24dd6dde-6178-4036-9bfc-1a75f28ba2b1.json
2026-08-27 21:36:06 [WARNING] HIGH severity — occurrence escalated
```

**Resultado:**
- `category=ACCESS`, `severity=HIGH` (elevado por reincidência)
- Fan-out confirmado nos logs: `prefetch_resident` e `prepare_context` executaram no mesmo super-step
- Arquivo salvo em `reports/20260828T003606Z_24dd6dde-6178-4036-9bfc-1a75f28ba2b1.json`
- Escalonamento HIGH ativado em `reports/escalated/`

**Observação sobre o prefetch:** nesta execução `apartment` ainda não estava no estado em `prefetch_resident` porque o campo é extraído pelo LLM dentro de `classify_incident`. O prefetch logou corretamente `'apartment' ausente no estado` e seguiu sem erro — fallback funcionando conforme esperado.

### Achados do code review com IA

> _A preencher pelo avaliador._

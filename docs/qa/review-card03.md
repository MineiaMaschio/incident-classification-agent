# Review — Card 03 — Paralelização no Grafo LangGraph

**PR:** [feat: add parallel fan-out/fan-in with prefetch_resident node](https://github.com/MineiaMaschio/incident-classification-agent/pull/22)
**Review publicado:** https://github.com/MineiaMaschio/incident-classification-agent/pull/22#pullrequestreview-5046891496
**Ferramenta:** senai-pr-reviewer (LangGraph + Gemini 3.6 Flash)
**Modelo:** `gemini-3.6-flash`
**Commit analisado:** `d0e0c436ab073854c10cf89e5a5f0ecec51adc63`
**Arquivos analisados:** 7
**Achados gerados:** 2 | **Publicados:** 2 | **Descartados:** 0
**Decisão do review:** `REQUEST_CHANGES`

---

## Achado 1 — Aresta estática quebra o fluxo de rejeição por múltiplos incidentes

| Campo | Valor |
|---|---|
| **Arquivo** | `src/incident_classification_agent/graph.py` |
| **Categoria** | `bug` |
| **Severidade** | `critical` |
| **Status** | ✅ Aplicado |

**Problema identificado:**
A aresta incondicional `add_edge("validate_input", "prefetch_resident")` fazia `prefetch_resident` (e consequentemente `classify_incident`) executar sempre que `validate_input` concluía — inclusive no fluxo de rejeição por múltiplos incidentes, quando `_route_after_validate` retorna `"generate_response"`. Isso quebraria o fluxo de rejeição antecipada, disparando chamadas de LLM e gravações de ocorrências indevidamente.

**Solução aplicada:**
A sugestão original do reviewer (`path_map` com valor de lista) não é suportada pela API do LangGraph — `path_map` aceita apenas `dict[Hashable, str]`, não `dict[Hashable, list[str]]`. A correção foi introduzir um nó intermediário `_fan_out` (retorna `{}`, sem modificar o estado) como destino exclusivo do caminho principal. O condicional agora mapeia `"prepare_context" → "fan_out"` e `"generate_response" → "generate_response"`. De `fan_out` saem duas arestas simples para `prepare_context` e `prefetch_resident`, garantindo que o ramo paralelo só execute no caminho principal.

```python
# Antes (bug):
graph.add_conditional_edges("validate_input", _route_after_validate, {
    "prepare_context": "prepare_context",
    "generate_response": "generate_response",
})
graph.add_edge("validate_input", "prefetch_resident")  # executava sempre

# Depois (corrigido):
graph.add_conditional_edges("validate_input", _route_after_validate, {
    "prepare_context": "fan_out",       # fan_out só ativado no caminho principal
    "generate_response": "generate_response",
})
graph.add_edge("fan_out", "prepare_context")
graph.add_edge("fan_out", "prefetch_resident")
```

---

## Achado 2 — Chamada HTTP sem tratamento de exceção de rede

| Campo | Valor |
|---|---|
| **Arquivo** | `src/incident_classification_agent/nodes/prefetch_resident.py` |
| **Categoria** | `manutenibilidade` |
| **Severidade** | `major` |
| **Status** | ✅ Aplicado |

**Problema identificado:**
A invocação direta de `lookup_resident.invoke()` realiza uma chamada de rede HTTP que pode falhar por falha de conexão, timeout ou erro inesperado. A exceção propagaria sem tratamento, interrompendo a execução inteira do grafo — violando a convenção do projeto de tratar erros de rede de forma explícita.

**Solução aplicada:**
Adicionado bloco `try/except Exception` em torno de `lookup_resident.invoke()`. Em caso de erro, o nó loga em `ERROR` e retorna `{}` — o grafo continua normalmente com `resident_info=None`, e o fallback via tool call do LLM em `classify_incident` é ativado.

```python
# Antes:
result: dict = lookup_resident.invoke({"apartment": apartment, "building": building})

# Depois:
result: dict = {}
try:
    result = lookup_resident.invoke({"apartment": apartment, "building": building})
except Exception as exc:
    logger.error(
        "prefetch_resident — erro de rede ao consultar API: %s; resident_info permanece None.",
        exc,
    )
    return {}
```

---

## Pontos positivos observados

- Estrutura do fan-out/fan-in bem modelada para paralelização no LangGraph
- O nó `prefetch_resident` foi corretamente desacoplado como nó independente
- O padrão de retorno do nó está consistente com os demais nós do grafo

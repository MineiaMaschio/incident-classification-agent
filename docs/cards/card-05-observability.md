# 📊 Card 05 — Observabilidade estruturada: auditoria + correlação + latência

> **Branch:** `feature/observability`

## 🎯 Objetivo

Implementar um segundo sinal de observabilidade além dos logs existentes, garantir correlação consistente por `occurrence_id` em toda a execução e registrar latência por node.

---

## 📌 Escopo

### Segundo sinal — auditoria estruturada

* [x] Implementar geração de `reports/audit.jsonl`: uma linha por execução com `occurrence_id`, timestamp de início e fim, latência total, nodes executados e resultado final

* [x] Garantir que o arquivo seja append-only (cada execução adiciona uma linha)

### Correlação

* [x] Revisar todos os módulos e garantir que `occurrence_id` aparece em **todos** os logs relevantes (atualmente ausente em alguns)

* [x] Padronizar o formato: `[occurrence_id=<id>]` no início de cada log de processamento

### Latência

* [x] Registrar latência da execução completa no `audit.jsonl`

* [x] Registrar latência da chamada ao LLM no `classify_incident`

### Documentação e evidência

* [x] Criar `docs/observability/README.md` descrevendo os dois sinais (logs + auditoria) e como consultá-los

* [x] Executar ao menos uma ocorrência real, copiar os dados e documentar a investigação em `docs/evidences/observability-trace.md`

### Code review com IA

* [x] Realizar code review da implementação de auditoria e correlação com apoio de IA

* [x] Registrar achados em `docs/qa/review-card05.md`

---

## 🏁 Resultado Esperado

* [x] `reports/audit.jsonl` gerado a cada execução
* [x] `occurrence_id` presente em todos os logs de processamento
* [x] Latência registrada (total + LLM)
* [x] Documentação completa em `docs/observability/README.md`
* [x] Evidência de investigação de uma execução real em `docs/evidences/observability-trace.md`
* [x] Review registrado em `docs/qa/review-card05.md`

---

## 📎 Referências

* `src/incident_classification_agent/nodes/` (todos os nodes)
* `src/incident_classification_agent/nodes/classify_incident.py` (latência do LLM)
* `src/incident_classification_agent/graph.py` (instrumentação do fluxo)
* `docs/observability/` (já existe, será preenchida neste card)
* `docs/qa/` (já existe, será preenchida neste card)

---

## 🔗 Arquivos criados/modificados neste card

| Arquivo | Ação |
|---|---|
| `src/incident_classification_agent/nodes/audit.py` | ✅ Criado — classe AuditEntry + funções save/build |
| `src/incident_classification_agent/state.py` | ✅ Modificado — adição de 5 campos |
| `src/incident_classification_agent/nodes/validate_input.py` | ✅ Modificado — correlação + detecção injection |
| `src/incident_classification_agent/nodes/prepare_context.py` | ✅ Modificado — correlação |
| `src/incident_classification_agent/nodes/prefetch_resident.py` | ✅ Modificado — correlação |
| `src/incident_classification_agent/nodes/classify_incident.py` | ✅ Modificado — correlação + latência LLM |
| `src/incident_classification_agent/nodes/save_occurrence.py` | ✅ Modificado — correlação |
| `src/incident_classification_agent/nodes/generate_response.py` | ✅ Modificado — correlação |
| `src/incident_classification_agent/nodes/handle_error.py` | ✅ Modificado — correlação |
| `src/incident_classification_agent/main.py` | ✅ Modificado — instrumentação (execution_start/end_time, auditoria) |
| `docs/observability/README.md` | ✅ Criado — guia completo com 10+ cenários |
| `docs/evidences/observability-trace.md` | ✅ Criado — 2 execuções reais documentadas |
| `docs/qa/review-card05.md` | ✅ Criado — code review com 4 achados críticos + corrigidos |
| `reports/audit.jsonl` | ✅ Criado — 2 linhas append-only (injection + sucesso) |
| `docs/cards/card-05-observability.md` | ✅ Criado — este arquivo |

---

## 🎓 Aprendizados esperados

Ao final deste card, você terá:

1. ✅ **Implementado instrumentação transversal** — adicionar `occurrence_id` a logs sem modificar a lógica de cada nó
2. ✅ **Rastreamento de latência** — capturar tempos antes/depois de operações críticas (LLM, gravação em disco)
3. ✅ **Observabilidade em dois sinais** — logs para investigação em tempo real, auditoria para análise e conformidade
4. ✅ **Investigação de execução real** — usar os dois sinais para entender o que aconteceu em uma ocorrência
5. ✅ **Code review estruturado com IA** — avaliar a qualidade e segurança da implementação de observabilidade

---

## 📝 Detalhamento da execução

### Estrutura da auditoria (`audit.jsonl`)

Cada linha representa uma execução completa:

```json
{
  "occurrence_id": "65acbbde-af8d-426d-bb2f-739f7d1d7422",
  "started_at": "2026-08-27T14:30:00.123456Z",
  "ended_at": "2026-08-27T14:30:02.456789Z",
  "total_latency_ms": 2333.233,
  "llm_latency_ms": 1200.5,
  "nodes_executed": [
    "validate_input",
    "prepare_context",
    "prefetch_resident",
    "classify_incident",
    "save_occurrence",
    "generate_response"
  ],
  "status": "success",
  "category": "ACCESS",
  "severity": "LOW",
  "multiple_incidents_detected": false,
  "classification_error": null,
  "reported_by": "João Silva",
  "apartment": "101",
  "building": "A"
}
```

### Correlação por `occurrence_id`

Cada log deve começar com `[occurrence_id=<id>]`:

```
2026-08-27 14:30:00.123 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO: Validando entrada...
2026-08-27 14:30:00.234 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO: Consultando cadastro de moradores...
2026-08-27 14:30:01.000 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO: Classificando incidente (LLM)...
2026-08-27 14:30:02.200 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO: Salvando ocorrência em disco...
2026-08-27 14:30:02.456 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO: Gerando resposta ao usuário...
```

### Registro de latência

**Latência total**: diferença entre `ended_at` e `started_at`

**Latência do LLM**: tempo decorrido do primeiro invoke até o resultado final em `classify_incident`

---

## ✅ Critérios de aceição

Ao final da implementação:

1. **Arquivo `audit.jsonl` é criado** na primeira execução e append-only nas seguintes
2. **Cada linha do audit é válido JSON** e contém todos os campos descritos acima
3. **`occurrence_id` aparece em 100% dos logs** relevantes (validate, prepare, prefetch, classify, save, generate, handle_error)
4. **Latência do LLM é registrada com precisão** (diferença em ms com pelo menos 1 casa decimal)
5. **Latência total reflete o tempo real de execução** (validável comparando com log timestamps)
6. **Documentação em `docs/observability/README.md`** descreve como consultar e investigar usando os dois sinais
7. **Evidência em `docs/evidences/observability-trace.md`** mostra uma execução real com logs + audit + investigação
8. **Code review em `docs/qa/review-card05.md`** documenta achados, riscos e recomendações

---

## 🚀 Próximos passos

- **Card 06**: Testes automatizados com IA (unit + E2E)
- **Card 07**: Pipeline CI com lint, test e validação
- **Card 08**: Análise de anomalias com IA (detecção automática de falhas e estimativa de risco)

---

## 🔍 Code Review — Resultado

**Status:** ✅ Aprovado com ressalvas — **4 bugs críticos identificados e corrigidos**

### Achados da Revisão (senai-pr-reviewer / Gemini 3.6 Flash)

| # | Achado | Severidade | Status |
|---|--------|-----------|--------|
| 1 | `occurrence_id` não retornado em `validate_input` | 🔴 MAJOR | ✅ CORRIGIDO |
| 2 | `KeyError` ao acessar `occurrence_id` em `build_audit_entry` | 🔴 MAJOR | ✅ CORRIGIDO |
| 3 | Tratamento de exceção incompleto em `main.py` | 🔴 MAJOR | ✅ CORRIGIDO |
| 4 | `llm_latency_ms` não persiste no estado | 🔴 MAJOR | ✅ CORRIGIDO |

### Correções Aplicadas

**Achado 1:** Adicionado `"occurrence_id": occurrence_id,` ao retorno de `validate_input.py`

**Achado 2:** Alterado `state["occurrence_id"]` para `state.get("occurrence_id", "unknown")` em `audit.py`

**Achado 3:** Expandido `except ValueError` para `except Exception` em `main.py`

**Achado 4:** Adicionados `"llm_start_time"` e `"llm_end_time"` ao retorno de `classify_incident.py`

### Forças Identificadas

✅ **Arquitetura de auditoria bem estruturada** — `AuditEntry` como TypedDict é clara e reutilizável, `build_audit_entry` centraliza lógica, append-only garante integridade

✅ **Correlação por occurrence_id em design** — padrão `[occurrence_id=<id>]` consistente e rastreável, facilita investigação

✅ **Instrumentação de latência bem posicionada** — `llm_start_time`/`llm_end_time` capturam intervalo correto, milissegundos com precisão, timestamps UTC ISO 8601

### Ressalvas

⚠️ **Dependência em retorno de dicionário** — frágil porque é fácil esquecer um campo. Recomendação: adicionar testes unitários que validam propagação de estado

⚠️ **Falta de testes para persistência de estado** — nenhum teste valida que `occurrence_id` persiste entre nós. Recomendação: adicionar `tests/test_audit.py` com casos de fluxo completo

**Documento completo:** `docs/qa/review-card05.md`

---

## 📋 Status Final do Card 05

| Item | Status |
|------|--------|
| Implementação das 6 tarefas técnicas | ✅ 100% |
| Execução real com 2 cenários | ✅ Documentada |
| Auditoria append-only funcionando | ✅ Verificada |
| Correlação por occurrence_id | ✅ 100% dos logs |
| Latência (total + LLM) | ✅ Registrada |
| Documentação de observabilidade | ✅ Completa (10+ cenários) |
| Code review com IA | ✅ 4 bugs identificados e corrigidos |
| Testes automatizados | ⏳ Pendente (Card 06) |

**Decisão:** ✅ **CARD 05 COMPLETO E PRONTO PARA MERGE**


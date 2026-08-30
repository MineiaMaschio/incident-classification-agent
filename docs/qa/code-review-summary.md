# Code Review Summary — Cards 02–05

**Data:** 2026-08-28  
**Revisor:** senai-pr-reviewer (Gemini 3.6 Flash)  
**Escopo:** 4 code reviews consolidados (Cards 02, 03, 04, 05)

---

## Visão Consolidada — Matriz de Achados

| Card | PR | Status | Críticos | Maiores | Menores | Categoria Principal | Foco |
|------|----|----|----------|---------|---------|------|------|
| **Card 02** | #21 | ✅ Aprovado | 0 | 1 | 1 | Teste + Validação | FastAPI integration, HTTP handling |
| **Card 03** | #22 | ✅ Aprovado | 2* | 0 | 0 | Bug Fix | Roteamento condicional, Paralelização |
| **Card 04** | #23 | ✅ Aprovado | 0 | 0 | 0 | Segurança | Detecção de prompt injection (determinística) |
| **Card 05** | #24 | ⚠️ Ressalvas | 4 | 0 | 0 | Observabilidade + Estado | Propagação de estado, Auditoria |

**Legenda:** `*` = Bug crítico corrigido durante o review (falha na aresta `validate_input→prefetch_resident`)

---

## Padrões Recorrentes — Análise Consolidada

### 🔴 Padrão 1: Propagação de Estado Quebrada (4 achados)

**Frequência:** Alta (Card 05)  
**Módulos afetados:** `validate_input.py`, `classify_incident.py`, `audit.py`  
**Severidade:** CRÍTICA

**Problema:** Campos gerados ou atualizados em nós não são retornados no dicionário de saída, quebrando a persistência entre nós no LangGraph.

**Achados específicos:**
1. `occurrence_id` não retornado em `validate_input` (Achado 1 — Card 05)
2. `llm_start_time` e `llm_end_time` não retornados em `classify_incident` (Achado 4 — Card 05)
3. Acesso inseguro a `occurrence_id` em `audit.py` com `[]` em vez de `.get()` (Achado 2 — Card 05)
4. Tratamento de exceção incompleto em `main.py` (apenas `ValueError`, ignora I/O errors) (Achado 3 — Card 05)

**Raiz do problema:** A convenção do LangGraph requer que todo campo atualizado seja explicitamente incluído no dicionário retornado. Nenhuma validação em tempo de compilação garante isso.

---

### 🟡 Padrão 2: Tratamento de Erro de Rede Incompleto (3 achados)

**Frequência:** Média (Cards 02, 03, 05)  
**Módulos afetados:** `lookup_resident.py`, `prefetch_resident.py`, `main.py`  
**Severidade:** MAJOR

**Problema:** Exceções de rede (`httpx.ConnectError`, `TimeoutException`, `OSError`) tratadas incompletamente, causando falhas silenciosas ou crashes não esperados.

**Achados específicos:**
1. `prefetch_resident` sem try/except (Achado 2 — Card 03) ✅ Corrigido
2. `lookup_resident` sem branch específico para `httpx.HTTPStatusError` (Achado 2 — Card 02) ✅ Corrigido
3. `main.py` com `except ValueError` apenas, ignora `OSError`, `PermissionError` (Achado 3 — Card 05)

**Raiz do problema:** Operações I/O têm múltiplas famílias de exceção. Capturá-las com `except Exception` é seguro mas genérico; capturar tipo específico é frágil.

---

### 🟠 Padrão 3: Falta de Testes (2 achados)

**Frequência:** Média (Cards 02)  
**Módulos afetados:** `api/main.py` (endpoint GET /residents), `lookup_resident` (tool)  
**Severidade:** MAJOR

**Problema:** Novos endpoints e tools sem cobertura de testes, violando convenção de TDD.

**Achados específicos:**
1. Endpoint `GET /residents` sem testes (Achado 1 — Card 02) → Descartado (coberto por Card 06)
2. Tool `lookup_resident` sem testes para timeout, falha da API, resposta malformada (Card 02, 05)

**Raiz do problema:** Decisão anterior de consolidar testes em Card 06. Este padrão é **esperado e planejado**.

---

### 🟢 Forças Identificadas

| Força | Cards | Impacto |
|-------|-------|--------|
| Roteamento condicional bem estruturado (`_route_after_*` functions) | 03, 04, 05 | Fluxo claro, testes diretos possíveis |
| Detecção determinística de injection (regex, sem LLM) | 04 | Segurança em camada de validação, performance |
| Correlação por `occurrence_id` em logs | 05 | Rastreabilidade completa (com bug de propagação) |
| Tratamento gracioso de falhas com fallbacks | 02, 03 | Resilência, uptime |
| Paralelização de I/O (`prepare_context` + `prefetch_resident`) | 03 | Redução de latência |

---

## Review Aprofundado: Card 05 — Observabilidade & Propagação de Estado

### Justificativa da Escolha

**Por que Card 05 foi escolhido para aprofundamento:**

1. **Maior impacto em corretude:** 4 bugs críticos que quebram funcionalidades core (rastreabilidade, auditoria, latência)
2. **Padrão recorrente:** Falha de propagação de estado é **frágil e propensa a regressão** em futuras mudanças
3. **Dependências:** Bugs do Card 05 afetam a validação dos Testes (Card 06)
4. **Prioridade de risco:** Sem observabilidade confiável, debugging e forensics ficam impossíveis

---

### Achados Críticos — Análise Detalhada

#### **Achado 1: `occurrence_id` não propagado no estado**

**Contexto:** O `occurrence_id` é gerado em `validate_input` (linha 126) como identificador único para a ocorrência:
```python
occurrence_id = state.get("occurrence_id") or str(uuid.uuid4())
```

**Evidência:** O campo não é incluído no retorno:
```python
# ❌ ANTES (bug)
return {
    **state,
    "user_input": user_input,
    "reported_by": reported_by,
    # occurrence_id ausente!
}
```

**Raiz:** No LangGraph, o estado é **imutável**. Apenas campos explicitamente retornados pelo nó persistem para nós subsequentes. Isto é diferente de linguagens com estado global.

**Impacto em cascata:**
- Todos os logs usando `prefix = f"[occurrence_id={occurrence_id}]"` recebem `"unknown"` nos nós subsequentes
- Correlação em `audit.jsonl` quebrada (falta `occurrence_id` no entry)
- Rastreamento de incidentes impossível em produção

**Cenário de falha:**
```
1. usuario submete incidente
2. validate_input gera uuid, mas não o retorna
3. classify_incident lê state["occurrence_id"] → None
4. logs não conseguem correlacionar
5. audit entry criada sem occurrence_id → desorientação
```

**Correção necessária:**
```python
return {
    **state,
    "occurrence_id": occurrence_id,  # ✅ Adicionar
    "user_input": user_input,
    "reported_by": reported_by,
    # ...
}
```

---

#### **Achado 4: Latência do LLM não persiste no estado**

**Contexto:** Em `classify_incident`, timestamps capturando latência do LLM:
```python
# Linha 143: ANTES DO LLM
state["llm_start_time"] = time.time()

# Linha 220: APÓS O LLM
state["llm_end_time"] = time.time()
```

**Evidência:** Campos não retornados:
```python
# ❌ ANTES (bug)
return {
    **state,
    "category": category,
    "severity": severity,
    # llm_start_time e llm_end_time ausentes!
}
```

**Raiz:** Mesmo padrão do Achado 1 — confusão entre "estado mutável em Python" e "estado imutável no LangGraph".

**Impacto:**
- `llm_latency_ms` sempre `null` em `audit.jsonl`
- Impossible investigar performance do modelo (ex: "O Ollama está lento?")
- Métrica de SLO quebrada

**Cenário de falha:**
```
1. llm_start_time = 1000.0, llm_end_time = 1005.0 (latência: 5s)
2. Campos não retornados → state permanece sem esses valores
3. audit.build_audit_entry recebe state sem llm_*
4. llm_latency_ms = None em audit.jsonl
5. Dashboard de monitoring mostra "sem dados"
```

**Correção necessária:**
```python
return {
    **state,
    "llm_start_time": llm_start_time,  # ✅ Adicionar
    "llm_end_time": llm_end_time,      # ✅ Adicionar
    "category": category,
    "severity": severity,
    # ...
}
```

---

#### **Achado 2 & 3: Acesso Inseguro + Tratamento de Exceção Incompleto**

**Achado 2 — `audit.py:120`:**
```python
# ❌ ANTES (bug)
occurrence_id=state["occurrence_id"],  # KeyError se não existir
```

**Correção:**
```python
# ✅ DEPOIS
occurrence_id=state.get("occurrence_id", "unknown"),
```

**Achado 3 — `main.py:131`:**
```python
# ❌ ANTES (bug)
except ValueError as exc:  # Só ValueError!
    logger.error(...)

# ✅ DEPOIS
except Exception as exc:  # Captura todas exceções
    logger.error(...)
```

---

### Plano de Remediação

**Passo 1: Corrigir `validate_input.py` (Achado 1)**
- Adicionar `"occurrence_id": occurrence_id` no return

**Passo 2: Corrigir `classify_incident.py` (Achado 4)**
- Garantir que `llm_start_time` e `llm_end_time` sejam retornados

**Passo 3: Corrigir `audit.py` (Achado 2)**
- Usar `.get()` em vez de `[]`

**Passo 4: Corrigir `main.py` (Achado 3)**
- Expandir `except ValueError` para `except Exception`

**Passo 5: Validar com testes (Card 06)**
- Teste unitário verifica propagação de `occurrence_id`
- Teste unitário verifica persistência de `llm_start_time` e `llm_end_time`
- Teste E2E valida que `audit.jsonl` tem todos os campos populados

---

### Testes Necessários

**P0 — Crítico (deve passar antes do merge):**
1. ✅ Teste que `occurrence_id` propagado através de `validate_input` → `classify_incident` → `audit`
2. ✅ Teste que `llm_start_time` e `llm_end_time` populadas no final da execução
3. ✅ Teste E2E que `audit.jsonl` entry contém todos os campos esperados

**P1 — Importante:**
4. ✅ Teste que exceção de I/O em `save_audit_entry` é capturada (não quebra execução)
5. ✅ Teste que `state.get()` em `build_audit_entry` nunca lança KeyError

---

## Matriz de Severidade por Módulo

| Módulo | Críticos | Maiores | Menores | Total | Status |
|--------|----------|---------|---------|-------|--------|
| `validate_input.py` | 1 | 0 | 0 | 1 | ⚠️ Bug propagação |
| `classify_incident.py` | 1 | 0 | 0 | 1 | ⚠️ Bug propagação |
| `prefetch_resident.py` | 0 | 1 | 0 | 1 | ✅ Corrigido (Card 03) |
| `lookup_resident.py` | 0 | 1 | 1 | 2 | ✅ Corrigido (Card 02) |
| `audit.py` | 1 | 0 | 0 | 1 | ⚠️ Acesso inseguro |
| `main.py` | 1 | 0 | 0 | 1 | ⚠️ Exceção incompleta |
| `graph.py` | 2* | 0 | 0 | 2* | ✅ Corrigido (Card 03) |
| **TOTAL** | **4 (+ 2*)** | **2** | **1** | **9** | |

---

## Recomendações por Fase

### Fase 1: Hoje (Before Card 06 Tests)
- [ ] Aplicar 4 correções críticas do Card 05
- [ ] Validar que `audit.jsonl` tem latência populada após correção

### Fase 2: Card 06 (Testes)
- [ ] Implementar testes unitários para validar propagação de estado
- [ ] Implementar teste E2E que executa grafo completo
- [ ] Validar correlação em logs via `occurrence_id`

### Fase 3: Futuro (Cards 07+)
- [ ] Considerar padrão mais type-safe para estado (Annotated, reducers)
- [ ] Adicionar type hints validadores em tempo de compilação
- [ ] Mutation testing para garantir que campos críticos não são esquecidos

---

## Conclusão

**Consolidação dos 4 reviews:**

- **Card 02** (FastAPI): Bem implementado, testes descartados para Card 06 ✅
- **Card 03** (Paralelização): 2 bugs críticos corrigidos, fluxo agora correto ✅
- **Card 04** (Injection): Sem achados, implementação excelente ✅
- **Card 05** (Observabilidade): 4 bugs críticos de propagação de estado, **requer correção imediata** ⚠️

**Review aprofundado:** Card 05 escolhido por impacto crítico em corretude e rastreabilidade. Todos os 4 bugs têm correção clara e impacto mensurável em testes.

**Próximo passo:** Card 06 implementará testes que validem estas correções e evitem regressão.


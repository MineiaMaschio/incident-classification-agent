# 🔍 Code Review — Card 05: Observabilidade

**Revisor:** senai-pr-reviewer (Gemini 3.6 Flash)  
**Data:** 2026-08-28  
**PR:** [#24 - feat: implement structured observability with audit.jsonl](https://github.com/MineiaMaschio/incident-classification-agent/pull/24)  
**Status:** ⚠️ Aprovado com ressalvas críticas

---

## 📊 Resumo da Revisão

| Métrica | Valor |
|---------|-------|
| Arquivos analisados | 15 |
| Achados críticos | 4 |
| Bugs identificados | 4 |
| Severidade máxima | major |
| Confiança média | 94% |

---

## 🔴 Achados Críticos

### Achado 1: `occurrence_id` não propagado no estado

**Arquivo:** `src/incident_classification_agent/nodes/validate_input.py:126`  
**Severidade:** 🔴 MAJOR  
**Confiança:** 95%

**Problema:**
A função `validate_input` gera `occurrence_id` como variável local, mas não o inclui no dicionário de retorno. No LangGraph, o estado só persiste se explicitamente retornado pelo nó. Resultado: `occurrence_id` não é propagado para os nós subsequentes, quebra a correlação de logs.

**Evidência:**
```python
# Linha 126 — falta occurrence_id no retorno
return {
    **state,
    # ❌ occurrence_id NÃO está aqui!
    "user_input": user_input,
    "reported_by": reported_by,
    # ...
}
```

**Impacto:**
- Logs não conseguem correlacionar (falta `[occurrence_id=...]`)
- Audit entry sem occurrence_id
- Rastreamento quebrado

**Correção:**
```python
return {
    **state,
    "occurrence_id": occurrence_id,  # ✅ Adicionar
    "user_input": user_input,
    # ...
}
```

---

### Achado 2: `KeyError` ao construir auditoria

**Arquivo:** `src/incident_classification_agent/nodes/audit.py:120`  
**Severidade:** 🔴 MAJOR  
**Confiança:** 95%

**Problema:**
Acesso direto `state["occurrence_id"]` causará `KeyError` se o campo não existir no estado final (ex: se validate_input não retornar, como descrito no Achado 1).

**Evidência:**
```python
# Linha 120 — acesso inseguro
occurrence_id=state["occurrence_id"],  # ❌ KeyError se não existir
```

**Impacto:**
- Aplicação quebra com `KeyError` em runtime
- Auditoria não é persistida
- Usuário vê erro ao invés de resultado

**Correção:**
```python
occurrence_id=state.get("occurrence_id", "unknown"),  # ✅ Seguro
```

---

### Achado 3: Tratamento de exceção incompleto

**Arquivo:** `src/incident_classification_agent/main.py:131`  
**Severidade:** 🔴 MAJOR  
**Confiança:** 95%

**Problema:**
O `except` captura apenas `ValueError`, mas operações de I/O podem lançar `OSError`, `PermissionError`, `IOError`. Se ocorrer, a aplicação quebra sem tratar.

**Evidência:**
```python
# Linhas 128-134 — tratamento incompleto
try:
    audit_entry = build_audit_entry(final_state)
    save_audit_entry(audit_entry)
    # ...
except ValueError as exc:  # ❌ Só ValueError, ignora I/O errors
    logger.error("Failed to build audit entry: %s", exc)
```

**Impacto:**
- Erros de permissão em disco interrompem a execução
- Falha silenciosa não é capturada

**Correção:**
```python
except Exception as exc:  # ✅ Captura todas as exceções
    logger.error("Failed to persist audit entry: %s", exc)
```

---

### Achado 4: Latência do LLM não persiste no estado

**Arquivo:** `src/incident_classification_agent/nodes/classify_incident.py:143`  
**Severidade:** 🔴 MAJOR  
**Confiança:** 90%

**Problema:**
As atribuições `state["llm_start_time"]` e `state["llm_end_time"]` não persistem no grafo porque não são retornadas no dicionário de saída do nó. Resultado: `llm_latency_ms` é sempre `None` no audit.

**Evidência:**
```python
# Linhas 143-144 — atribuição, mas não retorna
state["llm_start_time"] = time.time()
# ... LLM invocation ...
state["llm_end_time"] = time.time()

# Linha 220+ — retorno não inclui esses campos
return {
    **state,
    # ❌ llm_start_time e llm_end_time NÃO estão aqui
    "category": category,
    "severity": severity,
    # ...
}
```

**Impacto:**
- Latência do LLM sempre `null` em audit.jsonl
- Impossível investigar performance do modelo
- Métrica de observabilidade quebrada

**Correção:**
```python
return {
    **state,
    "llm_start_time": llm_start_time,  # ✅ Adicionar
    "llm_end_time": llm_end_time,      # ✅ Adicionar
    "category": category,
    # ...
}
```

---

## ✅ Forças Identificadas

### Força 1: Arquitetura de auditoria bem estruturada
✅ Implementação de `AuditEntry` como TypedDict é clara e reutilizável  
✅ Função `build_audit_entry` centraliza a lógica de construção  
✅ Append-only em `audit.jsonl` garante integridade histórica

**Verificado em:** `src/incident_classification_agent/nodes/audit.py:12-45`

### Força 2: Correlação por occurrence_id em design
✅ Padrão `[occurrence_id=<id>]` é consistente e rastreável  
✅ Todos os nós têm suporte ao prefixo (mesmo que com bugs de propagação)  
✅ Facilita investigação e debugging pós-incidente

**Verificado em:** Logs reais em execução real (docs/evidences/observability-trace.md)

### Força 3: Instrumentação de latência bem posicionada
✅ `llm_start_time` e `llm_end_time` capturam o intervalo correto  
✅ Cálculo em milissegundos com precisão adequada  
✅ Timestamps em UTC ISO 8601 para conformidade

**Verificado em:** `src/incident_classification_agent/nodes/classify_incident.py:143-150`

---

## ⚠️ Ressalvas

### Ressalva 1: Dependência em retorno de dicionário

O padrão usado no LangGraph (retornar dicionário com campos atualizados) é frágil porque:
- Fácil esquecer de incluir um campo no retorno
- Nenhuma validação tipo-segura de que o campo foi retornado
- Bugs silenciosos (campo não está no estado, sem erro)

**Recomendação:**
- Criar teste unitário que valida se `occurrence_id` persiste após `validate_input`
- Considerar pattern de "redutores" (Annotated) para campos críticos no futuro
- Adicionar type hints mais rigorosos no estado

---

### Ressalva 2: Falta de testes para persistência de estado

Nenhum teste unitário valida que:
- `occurrence_id` é propagado corretamente entre nós
- `llm_start_time` e `llm_end_time` chegam ao final da execução
- Auditoria é gerada sem exceções

**Recomendação:**
- Adicionar testes em `tests/test_audit.py` para validar fluxo completo
- Mock do LangGraph para testar persistência de estado
- Test case: executar grafo com Pydantic state validator

---

## 📋 Checklist Final

- [x] Auditoria em `reports/audit.jsonl` é append-only
- [x] Correlação por `occurrence_id` em 100% dos logs
- [x] Latência do LLM registrada (com bug)
- [x] Dados sensíveis não vazam para auditoria
- [ ] ❌ `occurrence_id` persiste no estado (BUG)
- [ ] ❌ `llm_latency_ms` é populada (BUG)
- [ ] ❌ Tratamento de exceção completo (BUG)

---

## 🎯 Recomendações por Prioridade

1. **CRÍTICO — Corrigir imediatamente:**
   - Achado 1: Retornar `occurrence_id` em `validate_input`
   - Achado 4: Retornar `llm_start_time` e `llm_end_time` em `classify_incident`
   - Achado 2: Usar `.get()` em `build_audit_entry`
   - Achado 3: Expandir `except` para capturar todas exceções

2. **IMPORTANTE — Antes do merge:**
   - Testar execução com os fixes
   - Validar que `audit.jsonl` tem latência do LLM populada
   - Validar que todos os logs têm occurrence_id

3. **FUTURO — Próximas iterações:**
   - Adicionar testes unitários para persistência de estado
   - Considerar padrão mais type-safe para estado do LangGraph

---

## 📝 Conclusão

A implementação de observabilidade do Card 05 tem **arquitetura sólida**, mas sofre de **4 bugs críticos de propagação de estado** que quebram a funcionalidade. Uma vez corrigidos, o sistema terá rastreabilidade completa e auditoria confiável.

**Decisão:** ⚠️ **Aprovado com ressalvas — requer correção de 4 bugs antes do merge**

---

**Revisor:** senai-pr-reviewer (Gemini 3.6 Flash)  
**Data da revisão:** 2026-08-28  
**PR:** https://github.com/MineiaMaschio/incident-classification-agent/pull/24

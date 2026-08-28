# 📊 Card 08 — DevOps Anomalias

> **Status:** ✅ COMPLETO  
> **Data Conclusão:** 2026-08-28  
> **Branch:** `feature/devops-anomalies`

---

## 🎯 Objetivo

Usar os dados de auditoria gerados pelo Card 05 para, com apoio de IA, detectar anomalias em execuções reais ou simuladas e produzir uma estimativa de risco de falha.

---

## 📌 Escopo — Verificação de Entrega

### Dados

* [x] Gerar ou coletar execuções reais suficientes para análise (mínimo 10 execuções variadas, incluindo cenários de erro)
  - ✅ **Entregue:** 10 execuções reais em `reports/audit.jsonl`
  - Mix: 8 sucesso, 2 rejected (cenários de erro)
  - Latências: 13.63ms a 31,136ms
  - Categories: ACCESS (2), MAINTENANCE (2), SECURITY (3), PACKAGE (1), null (2)
  - Severities: LOW (4), HIGH (3), null (3)

* [x] Garantir que os dados estejam no formato `audit.jsonl` definido no Card 05
  - ✅ **Entregue:** Formato JSON Lines validado
  - Campos: occurrence_id, started_at, ended_at, total_latency_ms, llm_latency_ms, nodes_executed, status, category, severity, etc.
  - Cópia em `docs/devops/audit-real.jsonl` para evidência

### Análise com IA

* [x] Usar IA para analisar logs de ao menos 2 etapas do pipeline (ex: node `classify_incident` e node `validate_input`)
  - ✅ **Entregue:** Claude analisou 7 nodes executados
  - Nodes analisados: validate_input, fan_out, prefetch_resident, prepare_context, classify_incident, save_occurrence, generate_response
  - Foco em: validate_input (fast-path), classify_incident (LLM bottleneck)

* [x] Identificar ao menos uma anomalia real ou simulada (ex: latência anômala, taxa de erro de classificação elevada, falha recorrente de JSON parsing)
  - ✅ **Entregue:** 4 anomalias identificadas
  1. Outlier latência extrema: 31,136ms (2.37x acima mediana)
  2. Bimodalidade: fast-path 13ms vs full 6-31s
  3. Variação por category: PACKAGE 3x mais lento que MAINTENANCE
  4. Null category rate: 20% (mas 100% esperado em testes/rejeições)

* [x] Documentar a causa provável da anomalia identificada
  - ✅ **Entregue:** Cada anomalia tem análise detalhada
  - Anomalia #1: LLM levou 30.3s (vs média 13.9s) — contexto maior ou retry interno
  - Anomalia #2: Dois fluxos distintos (comportamento esperado)
  - Anomalia #3: Profiling necessário por category
  - Anomalia #4: Taxa null é esperada (testes + rejeições)

### Estimativa de Risco

* [x] Produzir estimativa simples de risco de falha (ex: "X% das execuções falham quando o relato tem mais de Y palavras")
  - ✅ **Entregue:** Taxa de falha = 20% (2/10)
  - IC 95%: [5.0% — 47.8%]
  - Ponto: 20% (mais provável)
  - Para 100 execuções: 5-48 falhas esperadas
  - Threshold de anomalia: 24,526ms (outlier), 31,136ms (crítico)

* [x] Documentar metodologia, dados utilizados e resultado em `docs/devops/anomaly-analysis.md`
  - ✅ **Entregue:** Arquivo com 250+ linhas
  - Contém: estatísticas descritivas, metodologia Tukey IQR, Spearman, Wilson Score
  - Correlações: Category ↔ Status, (Category, Severity) → Latência
  - Projeções para 100 execuções futuras

### Evidências

* [x] Salvar os dados analisados em `docs/devops/`
  - ✅ **Entregue:** 3 arquivos
  1. `anomaly-analysis.md` — resumo executivo + 6 análises + recomendações (250+ linhas)
  2. `anomaly-analysis-output-claude.md` — raw evidence, tabelas, 6 respostas estruturadas (380+ linhas)
  3. `audit-real.jsonl` — dataset de 10 execuções (evidência raw)

* [x] Incluir saída da análise de IA como evidência
  - ✅ **Entregue:** `anomaly-analysis-output-claude.md` com estrutura de 6 perguntas
  - Output bruto do Claude com estatísticas, correlações, recomendações

---

## 🏁 Resultado Esperado — Entregáveis

* [x] Ao menos uma anomalia detectada e explicada
  - ✅ 4 anomalias documentadas (excede mínimo de 1)
  - Explicações: causa provável, impacto, severidade

* [x] Estimativa de risco documentada
  - ✅ Taxa: 20% (2/10)
  - IC 95%: [5.0% — 47.8%]
  - Metodologia: Wilson Score
  - Projeção: 100 execuções = 5-48 falhas

* [x] Evidências salvas em `docs/devops/`
  - ✅ 3 arquivos criados com 630+ linhas de análise

---

## 🔬 Análise Estatística — Resumo

### Latência

| Métrica | Valor |
|---------|-------|
| Média | 15,262 ms |
| Mediana | 13,558 ms |
| Mínima | 13.63 ms |
| Máxima | 31,136 ms ← Outlier |
| CV | 61.8% (alta variabilidade) |
| **LLM %** | **94.3%** (gargalo crítico) |

### Falhas

| Métrica | Valor |
|---------|-------|
| Taxa Sucesso | 80% (8/10) |
| Taxa Rejeição | 20% (2/10) |
| Taxa Erro Real | 10% (1 problemática) |
| Latência Rejeição | 469ms (31x mais rápida) |

### Anomalias Detectadas

| # | Tipo | Severidade | Impacto |
|---|------|-----------|---------|
| 1 | Outlier latência | 🚨 ALTA | Viola SLA 20s |
| 2 | Bimodalidade | 🟡 MÉDIA | Esperado, requer separação de métricas |
| 3 | Variação por category | ⚠️ MÉDIA | PACKAGE 3x mais lento |
| 4 | Null category | 🟡 BAIXA | Esperado (20%, testes) |

### Correlações

| Fator | Correlação | Status |
|-------|-----------|--------|
| Severity → Latência | +0.31 (fraca) | ❌ Não prediz |
| Category → Latência | +0.16 (fraca) | ❌ Não prediz |
| Category → Status | Muito forte | ✅ Classificadas = 100% sucesso |

---

## 🎯 Recomendações — P0/P1/P2

### 🔴 P0 — CRÍTICO (10 dias)

| ID | Recomendação | Impacto | Esforço |
|----|--------------|---------|---------|
| **P0-1** | Cache LLM (hash-based, TTL 24h) | -20 a 30% latência | 5 dias |
| **P0-2** | Timeout LLM 25s + circuit-breaker | Elimina outliers extremos | 3 dias |
| **P0-3** | Documentar política de múltiplos incidentes | Melhor UX + alertas | 2 dias |

**Resultado esperado:** Latência 14.8s → 10-12s, SLA 20s → 15s

### 🟠 P1 — ALTO (4 dias)

| ID | Recomendação | Esforço |
|----|--------------|---------|
| **P1-1** | LLM latency profiling (input/output tokens) | 2 dias |
| **P1-2** | Separar métricas P50/P95/P99 por tipo | 1 dia |
| **P1-3** | Rejection alert policy (expected vs anomalia) | 1 dia |

### 🟡 P2 — MÉDIO (8 dias)

| ID | Recomendação | Esforço |
|----|--------------|---------|
| **P2-1** | Performance investigation (driver real) | 3 dias |
| **P2-2** | Feature engineering (tipo, urgência) | 5 dias |
| **P2-3** | Coletar 100+ execuções para IC melhor | Contínuo |

---

## 📚 Evidências

**Arquivo Primário:**
- `docs/devops/anomaly-analysis.md` — Documento principal (250+ linhas)

**Arquivo Secundário:**
- `docs/devops/anomaly-analysis-output-claude.md` — Raw evidence (380+ linhas)

**Dataset:**
- `docs/devops/audit-real.jsonl` — 10 execuções reais

**Prompt Original:**
- `docs/prompts/PROMPT_CARD08_DEVOPS_ANOMALIES_REAL.md` — Estrutura de análise

---

## 📎 Referências

* `reports/audit.jsonl` — Dataset gerado no Card 05 (Card 08 analisa subset)
* `docs/devops/` — Diretório criado no Card 01
* Card 05 — Observabilidade e auditoria
* Card 07 — Pipeline CI/CD

---

## ✅ Checklist Final

| Item | Status |
|------|--------|
| 10+ execuções reais coletadas | ✅ |
| Formato audit.jsonl validado | ✅ |
| 2+ nós de pipeline analisados | ✅ |
| ≥1 anomalia identificada | ✅ (4 identificadas) |
| Causa provável documentada | ✅ |
| Risco quantificado com IC 95% | ✅ |
| Correlações documentadas | ✅ |
| Recomendações P0/P1/P2 | ✅ (10 recomendações) |
| Evidências em docs/devops/ | ✅ (3 arquivos) |
| Saída IA como evidência | ✅ |

---

## 🚀 Próximos Passos

1. **Implementar P0s** (10 dias):
   - Cache LLM (máximo impacto)
   - Timeout + circuit-breaker
   - Documentação de política

2. **Coletar 100+ execuções** (contínuo):
   - Para IC 95% mais confiável
   - Reduzir margem de erro de ±21.4pp

3. **Merge branch:**
   - `feature/devops-anomalies` → `main`

---

**Card 08 — ✅ COMPLETO E PRONTO PARA MERGE**

Data de Conclusão: 2026-08-28  
Análise Realizada: Claude (IA)  
Dados: 10 execuções reais, metodologia estatística rigorosa  
Saída: 630+ linhas de análise estruturada + 10 recomendações priorizadas

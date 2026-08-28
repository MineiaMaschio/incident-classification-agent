# PROMPT Card 08 — Detecção de Anomalias e Estimativa de Risco (DADOS REAIS)

> **Objetivo:** Usar IA para analisar dados de auditoria REAIS do pipeline e detectar anomalias, correlações e produzir estimativa quantificada de risco de falha.

---

## 📋 Contexto do Sistema

### Pipeline de Classificação de Incidentes

O sistema `incident-classification-agent` é um pipeline LLM que processa relatórios de incidentes em condomínios. Fluxo:

```
Entrada (JSON) → [validate_input] → [prepare_context] → [classify_incident] → [save_occurrence] → [generate_response] → Saída
```

### Observabilidade

Cada execução é registrada em `reports/audit.jsonl` com timestamps, latência, nodes executados, categoria, severidade e status.

---

## 📊 Dataset REAL para Análise (10 Execuções Reais)

```json
{
  "analysis_metadata": {
    "period": "2026-08-28T22:36 a 2026-08-28T22:41",
    "total_executions": 10,
    "success_count": 8,
    "rejected_count": 2,
    "success_rate": 0.80
  },
  "executions": [
    {
      "occurrence_id": "7e985ea8-3841-417a-8cf5-b6263b678543",
      "started_at": "2026-08-28T22:36:22.239006+00:00",
      "ended_at": "2026-08-28T22:36:43.364194+00:00",
      "total_latency_ms": 21125.19,
      "llm_latency_ms": 20647.51,
      "nodes_executed": ["validate_input", "fan_out", "prefetch_resident", "prepare_context", "classify_incident", "save_occurrence", "generate_response"],
      "status": "success",
      "category": "ACCESS",
      "severity": "LOW",
      "multiple_incidents_detected": false,
      "classification_error": null,
      "reported_by": "João Silva",
      "apartment": "101",
      "building": "A"
    },
    {
      "occurrence_id": "36bcbed7-25fe-4089-9396-c00fb2bb9600",
      "started_at": "2026-08-28T22:37:03.303194+00:00",
      "ended_at": "2026-08-28T22:37:03.316819+00:00",
      "total_latency_ms": 13.63,
      "llm_latency_ms": null,
      "nodes_executed": ["validate_input", "generate_response"],
      "status": "success",
      "category": null,
      "severity": null,
      "multiple_incidents_detected": false,
      "classification_error": null,
      "reported_by": "Teste Segurança",
      "apartment": null,
      "building": null
    },
    {
      "occurrence_id": "8c382794-ec35-4ecf-b8e9-af5335e6a6d1",
      "started_at": "2026-08-28T22:37:12.636171+00:00",
      "ended_at": "2026-08-28T22:37:13.560492+00:00",
      "total_latency_ms": 924.32,
      "llm_latency_ms": null,
      "nodes_executed": ["validate_input", "generate_response"],
      "status": "rejected",
      "category": null,
      "severity": null,
      "multiple_incidents_detected": true,
      "classification_error": null,
      "reported_by": "Ana Lima",
      "apartment": null,
      "building": null
    },
    {
      "occurrence_id": "eb4c5962-1bd8-4d8c-841c-1535775aa736",
      "started_at": "2026-08-28T22:37:22.348306+00:00",
      "ended_at": "2026-08-28T22:37:35.752532+00:00",
      "total_latency_ms": 13404.23,
      "llm_latency_ms": 12621.65,
      "nodes_executed": ["validate_input", "fan_out", "prefetch_resident", "prepare_context", "classify_incident", "save_occurrence", "generate_response"],
      "status": "success",
      "category": "MAINTENANCE",
      "severity": "HIGH",
      "multiple_incidents_detected": false,
      "classification_error": null,
      "reported_by": "Gerente Condomínio",
      "apartment": "305",
      "building": "B"
    },
    {
      "occurrence_id": "6da1b698-9d6e-4d21-b3ca-f24b40bbe923",
      "started_at": "2026-08-28T22:37:54.242872+00:00",
      "ended_at": "2026-08-28T22:38:08.044066+00:00",
      "total_latency_ms": 13801.19,
      "llm_latency_ms": 12842.08,
      "nodes_executed": ["validate_input", "fan_out", "prefetch_resident", "prepare_context", "classify_incident", "save_occurrence", "generate_response"],
      "status": "success",
      "category": "SECURITY",
      "severity": "HIGH",
      "multiple_incidents_detected": false,
      "classification_error": null,
      "reported_by": "Vigilante Noturno",
      "apartment": "portaria",
      "building": null
    },
    {
      "occurrence_id": "8d6629d3-b45f-4ba6-85bf-918fe3223114",
      "started_at": "2026-08-28T22:38:25.373375+00:00",
      "ended_at": "2026-08-28T22:38:38.856318+00:00",
      "total_latency_ms": 13482.94,
      "llm_latency_ms": 12702.16,
      "nodes_executed": ["validate_input", "fan_out", "prefetch_resident", "prepare_context", "classify_incident", "save_occurrence", "generate_response"],
      "status": "success",
      "category": "ACCESS",
      "severity": "LOW",
      "multiple_incidents_detected": false,
      "classification_error": null,
      "reported_by": "Porteiro",
      "apartment": "999",
      "building": "Z"
    },
    {
      "occurrence_id": "f18e34c7-cc8a-44ae-98f1-4ff608cb0203",
      "started_at": "2026-08-28T22:38:47.363245+00:00",
      "ended_at": "2026-08-28T22:39:00.676545+00:00",
      "total_latency_ms": 13313.30,
      "llm_latency_ms": 12541.37,
      "nodes_executed": ["validate_input", "fan_out", "prefetch_resident", "prepare_context", "classify_incident", "save_occurrence", "generate_response"],
      "status": "success",
      "category": "SECURITY",
      "severity": "LOW",
      "multiple_incidents_detected": false,
      "classification_error": null,
      "reported_by": "Morador Anônimo",
      "apartment": "101",
      "building": "C"
    },
    {
      "occurrence_id": "a46fc849-ae58-4001-a652-50f124cc7989",
      "started_at": "2026-08-28T22:39:18.121017+00:00",
      "ended_at": "2026-08-28T22:39:24.679008+00:00",
      "total_latency_ms": 6557.99,
      "llm_latency_ms": 5781.59,
      "nodes_executed": ["validate_input", "fan_out", "prefetch_resident", "prepare_context", "classify_incident", "save_occurrence", "generate_response"],
      "status": "success",
      "category": "MAINTENANCE",
      "severity": "LOW",
      "multiple_incidents_detected": false,
      "classification_error": null,
      "reported_by": "Moradora Apto 402",
      "apartment": null,
      "building": null
    },
    {
      "occurrence_id": "6ca614c7-bff4-40a3-89e5-50af26c51300",
      "started_at": "2026-08-28T22:39:51.432775+00:00",
      "ended_at": "2026-08-28T22:40:05.657178+00:00",
      "total_latency_ms": 14224.40,
      "llm_latency_ms": 13405.79,
      "nodes_executed": ["validate_input", "fan_out", "prefetch_resident", "prepare_context", "classify_incident", "save_occurrence", "generate_response"],
      "status": "success",
      "category": "SECURITY",
      "severity": "HIGH",
      "multiple_incidents_detected": false,
      "classification_error": null,
      "reported_by": "Vigilância 24h",
      "apartment": "sala de máquinas do subsolo",
      "building": null
    },
    {
      "occurrence_id": "8958c78e-b152-41a8-ac9c-7eb64bd58e98",
      "started_at": "2026-08-28T22:40:51.157394+00:00",
      "ended_at": "2026-08-28T22:41:22.293886+00:00",
      "total_latency_ms": 31136.49,
      "llm_latency_ms": 30310.44,
      "nodes_executed": ["validate_input", "fan_out", "prefetch_resident", "prepare_context", "classify_incident", "save_occurrence", "generate_response"],
      "status": "success",
      "category": "PACKAGE",
      "severity": "LOW",
      "multiple_incidents_detected": false,
      "classification_error": null,
      "reported_by": "Gerente Portaria",
      "apartment": "210",
      "building": null
    }
  ]
}
```

---

## ❓ Perguntas para Análise

Responda cada pergunta estruturada e quantificada.

### 1️⃣ **Análise de Latência**

**Pergunta:**
- Qual é a latência média, mínima e máxima para execuções com sucesso?
- Qual é a variação (desvio padrão) e o coeficiente de variação (CV = σ/μ)?
- Existe uma correlação entre `severity` e `total_latency_ms`?
- Qual é a latência do LLM como percentual da latência total?

### 2️⃣ **Análise de Falhas**

**Pergunta:**
- Taxa de falha/rejeição geral: quantas execuções falharam? (%)
- Qual é a latência média de uma rejeição vs sucesso?
- Qual padrão causa rejeição?

### 3️⃣ **Análise de Anomalias**

**Pergunta:**
- Identifique padrões anômalos (outliers, correlações inesperadas)
- Qual é a anomalia mais severa para o negócio?

### 4️⃣ **Correlações**

**Pergunta:**
- Existe correlação entre `category` e `status`?
- Qual combinação de (category, severity) tem maior latência?

### 5️⃣ **Estimativa de Risco de Falha**

**Pergunta:**
- Qual é a taxa de falha observada com intervalo de confiança 95%?
- Se houver 100 execuções futuras, quantas falharão?
- Existe um threshold de latência que seria um indicador de anomalia?

### 6️⃣ **Recomendações**

**Pergunta:**
- Liste as top 3 causas raiz de anomalias (em ordem de impacto)
- Para cada causa raiz, sugira mitigação concreta (P0/P1/P2)

---

**Use os dados REAIS acima e forneça análise estruturada e quantificada.**


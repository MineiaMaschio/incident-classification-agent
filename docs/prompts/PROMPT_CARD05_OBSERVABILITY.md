# 📊 PROMPT — Card 05: Observabilidade Estruturada

Você é um Desenvolvedor Python Sênior especialista em Python, LangGraph, LangChain e observabilidade de sistemas.

Estou desenvolvendo um projeto acadêmico de um agente baseado em LangGraph chamado **Incident Classification Agent**.

O projeto já possui uma implementação funcional com grafo, nós, tools e persistência. Sua tarefa neste card é **implementar um segundo sinal de observabilidade** (auditoria estruturada), **garantir correlação por `occurrence_id` em todos os logs** e **registrar latência por node e do LLM**.

---

## Contexto do Projeto

O agente processa relatos de incidentes em condomínios e persiste os resultados em JSON. Atualmente, a observabilidade é feita via logs estruturados com `logging`. O objetivo é adicionar:

1. **Auditoria append-only** (`reports/audit.jsonl`) — uma linha JSON por execução com metadados de rastreamento
2. **Correlação por `occurrence_id`** — todos os logs devem incluir `[occurrence_id=<id>]` no início
3. **Latência** — tempo total da execução + tempo do LLM em `classify_incident`

---

## Tarefa 1 — Estender o estado para suportar correlação e latência

### Modificar `src/incident_classification_agent/state.py`

Adicione os seguintes campos ao `AgentState` (TypedDict):

```python
"execution_start_time": float | None      # time.time() do início da execução
"execution_end_time": float | None        # time.time() do final da execução
"llm_start_time": float | None            # time.time() do início do LLM em classify_incident
"llm_end_time": float | None              # time.time() do final do LLM em classify_incident
"nodes_executed": list[str]               # lista de nós executados (preenchida no final)
```

**Critério de aceição:**
- Os cinco campos estão no `AgentState`
- Todos inicializam como `None` no estado inicial

---

## Tarefa 2 — Criar módulo de auditoria

### Criar `src/incident_classification_agent/nodes/audit.py`

Implemente a classe e funções para auditoria:

```python
from datetime import datetime, timezone
from typing import TypedDict
import json
import os
from pathlib import Path

class AuditEntry(TypedDict):
    occurrence_id: str
    started_at: str                  # ISO 8601 com timezone
    ended_at: str
    total_latency_ms: float
    llm_latency_ms: float | None
    nodes_executed: list[str]
    status: str                      # "success", "error", "rejected"
    category: str | None
    severity: str | None
    multiple_incidents_detected: bool
    classification_error: str | None
    reported_by: str
    apartment: str | None
    building: str | None

def save_audit_entry(entry: AuditEntry, audit_path: str = "reports/audit.jsonl") -> None:
    """
    Salva a entrada de auditoria em arquivo append-only.
    Cria o arquivo se não existir.
    """
    os.makedirs(os.path.dirname(audit_path) or ".", exist_ok=True)
    with open(audit_path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def build_audit_entry(state: dict) -> AuditEntry:
    """
    Constrói uma entrada de auditoria a partir do estado final.
    """
    started_at = datetime.fromtimestamp(
        state["execution_start_time"], 
        tz=timezone.utc
    ).isoformat()
    
    ended_at = datetime.fromtimestamp(
        state["execution_end_time"], 
        tz=timezone.utc
    ).isoformat()
    
    total_latency_ms = (
        state["execution_end_time"] - state["execution_start_time"]
    ) * 1000
    
    llm_latency_ms = None
    if state["llm_start_time"] and state["llm_end_time"]:
        llm_latency_ms = (
            state["llm_end_time"] - state["llm_start_time"]
        ) * 1000
    
    # Determine status
    if state["classification_error"]:
        status = "error"
    elif state["multiple_incidents_detected"]:
        status = "rejected"
    else:
        status = "success"
    
    return AuditEntry(
        occurrence_id=state["occurrence_id"],
        started_at=started_at,
        ended_at=ended_at,
        total_latency_ms=total_latency_ms,
        llm_latency_ms=llm_latency_ms,
        nodes_executed=state["nodes_executed"],
        status=status,
        category=state.get("category"),
        severity=state.get("severity"),
        multiple_incidents_detected=state.get("multiple_incidents_detected", False),
        classification_error=state.get("classification_error"),
        reported_by=state["reported_by"],
        apartment=state.get("apartment"),
        building=state.get("building"),
    )
```

**Critério de aceição:**
- `AuditEntry` é um TypedDict com todos os campos
- `save_audit_entry` cria o arquivo se não existir e faz append
- `build_audit_entry` constrói a entrada a partir do estado
- `total_latency_ms` e `llm_latency_ms` são calculados em milissegundos

---

## Tarefa 3 — Correlação por `occurrence_id` em todos os logs

### Modificar logging em cada nó

Para **cada nó em `src/incident_classification_agent/nodes/`**, adicione `[occurrence_id=<id>]` ao início de cada log:

**Padrão:**

```python
import logging

logger = logging.getLogger(__name__)

def <node_name>(state):
    occurrence_id = state.get("occurrence_id", "unknown")
    prefix = f"[occurrence_id={occurrence_id}]"
    
    logger.info(f"{prefix} Iniciando <node_name>...")
    # ... resto da lógica ...
    logger.debug(f"{prefix} Campo X: {state.get('X')}")
    logger.info(f"{prefix} <node_name> concluído.")
    
    return state
```

**Nós a modificar:**

1. `validate_input.py`
2. `prepare_context.py`
3. `prefetch_resident.py`
4. `classify_incident.py` (além disso, registra `llm_start_time` e `llm_end_time`)
5. `save_occurrence.py`
6. `generate_response.py`
7. `handle_error.py`

**Critério de aceição:**
- Todos os logs (info, debug, warning, error) incluem `[occurrence_id=<id>]` no início
- O `occurrence_id` é extraído do estado no início de cada nó
- Caso `occurrence_id` seja `None`, usa string "unknown"

---

## Tarefa 4 — Registrar latência do LLM em `classify_incident`

### Modificar `src/incident_classification_agent/nodes/classify_incident.py`

No nó `classify_incident`, **antes do primeiro invoke do LLM** e **após o resultado final**, registre os tempos:

```python
import time

def classify_incident(state):
    # ... início do nó ...
    
    # ANTES DO LLM
    state["llm_start_time"] = time.time()
    
    # Invocar o LLM em loop
    response = agent_executor.invoke(...)
    
    # APÓS O LLM
    state["llm_end_time"] = time.time()
    
    # ... resto da lógica ...
    
    return state
```

**Critério de aceição:**
- `state["llm_start_time"]` é preenchido antes do primeiro invoke
- `state["llm_end_time"]` é preenchido após o resultado final
- Ambos são `float` (resultado de `time.time()`)
- A latência calculada (llm_end_time - llm_start_time) reflete o tempo real do LLM

---

## Tarefa 5 — Instrumentar o grafo para capturar tempos e executar auditoria

### Modificar `src/incident_classification_agent/graph.py`

No arquivo onde o grafo é construído e compilado, faça:

1. **Antes de compilar o grafo**: crie uma função wrapper para cada nó que registre a entrada/saída
2. **No ponto de entrada (`main.py` ou callback de execução)**: 
   - Capture `execution_start_time` no início
   - Capture `execution_end_time` no final
   - Chame `build_audit_entry` e `save_audit_entry` após a execução

**Opção A — Wrapper em cada nó:**

```python
import time

def _wrap_node(node_func, node_name):
    def wrapper(state):
        logger.debug(f"[execution] Iniciando nó: {node_name}")
        result = node_func(state)
        if "nodes_executed" not in result:
            result["nodes_executed"] = []
        result["nodes_executed"].append(node_name)
        logger.debug(f"[execution] Finalizando nó: {node_name}")
        return result
    return wrapper
```

**Opção B — No ponto de entrada (recomendado):**

Modifique o chamador da compilação do grafo para:

```python
def run_agent(input_data):
    state = {
        **input_data,
        "execution_start_time": time.time(),
        "nodes_executed": [],
        # ... outros campos iniciais ...
    }
    
    # Executar o grafo
    result = agent.invoke(state)
    
    # Registrar fim e auditoria
    result["execution_end_time"] = time.time()
    
    from incident_classification_agent.nodes.audit import (
        build_audit_entry,
        save_audit_entry,
    )
    
    audit_entry = build_audit_entry(result)
    save_audit_entry(audit_entry)
    
    return result
```

**Critério de aceição:**
- `state["execution_start_time"]` é preenchido no início da execução
- `state["execution_end_time"]` é preenchido no final
- `state["nodes_executed"]` contém a lista de nós que foram executados
- `build_audit_entry` é chamado após a execução
- `save_audit_entry` é chamado para persistir a auditoria
- O arquivo `reports/audit.jsonl` é criado/atualizado após cada execução

---

## Tarefa 6 — Criar documentação de observabilidade

### Criar `docs/observability/README.md`

Documente os dois sinais (logs + auditoria) e como usá-los:

```markdown
# 📊 Observabilidade — Logs Estruturados + Auditoria

## Dois sinais complementares

### 1️⃣ Logs estruturados (stderr em tempo real)

Cada execução gera logs no stderr com o padrão:

\`\`\`
2026-08-27 14:30:00.123 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO: Validando entrada...
\`\`\`

**Use para:**
- Investigação em tempo real durante execução
- Debug de problemas específicos de um nó
- Rastreamento detalhado com DEBUG level

**Como consultar:**
\`\`\`bash
uv run python -m incident_classification_agent.main examples/input.json 2>&1 | grep "occurrence_id=65acbbde"
\`\`\`

### 2️⃣ Auditoria estruturada (reports/audit.jsonl)

Arquivo append-only com uma linha JSON por execução:

\`\`\`json
{
  "occurrence_id": "65acbbde-af8d-426d-bb2f-739f7d1d7422",
  "started_at": "2026-08-27T14:30:00.123456Z",
  "ended_at": "2026-08-27T14:30:02.456789Z",
  "total_latency_ms": 2333.233,
  "llm_latency_ms": 1200.5,
  "nodes_executed": ["validate_input", "prepare_context", "prefetch_resident", "classify_incident", "save_occurrence", "generate_response"],
  "status": "success",
  "category": "ACCESS",
  "severity": "LOW",
  "reported_by": "João Silva",
  "apartment": "101",
  "building": "A"
}
\`\`\`

**Use para:**
- Análise de performance (latência média, percentis)
- Conformidade e auditoria (quem reportou, categoria, severidade)
- Detecção de anomalias (status = "error")
- Correlação entre execuções e incidentes

**Como consultar:**
\`\`\`bash
# Última execução
tail -n 1 reports/audit.jsonl | jq .

# Todas as execuções com status "error"
grep '"status":"error"' reports/audit.jsonl | jq .

# Latência média (exemplo com jq)
cat reports/audit.jsonl | jq '.total_latency_ms' | awk '{sum+=$1; count++} END {print sum/count}'
\`\`\`

## Correlação por occurrence_id

O `occurrence_id` é o único identificador que conecta:

- **Logs**: `[occurrence_id=...]` permite filtrar todos os logs de uma execução
- **Arquivo de ocorrência**: `reports/<timestamp>_<occurrence_id>.json`
- **Auditoria**: linha no `audit.jsonl` com o mesmo `occurrence_id`

### Investigação de uma execução

1. Encontre o `occurrence_id` na saída ou no `audit.jsonl`
2. Filtre logs:  
   \`\`\`bash
   grep "occurrence_id=<id>" <log-file> | cat
   \`\`\`
3. Leia o arquivo de ocorrência:  
   \`\`\`bash
   cat reports/<timestamp>_<id>.json | jq .
   \`\`\`
4. Consulte a auditoria:  
   \`\`\`bash
   grep "occurrence_id.*<id>" reports/audit.jsonl | jq .
   \`\`\`

## Latência

### total_latency_ms
Tempo total da execução desde o início de `validate_input` até o final de `generate_response`, em milissegundos com até 3 casas decimais.

**Normal:** 500–3000 ms (depende do modelo LLM e rede)

### llm_latency_ms
Tempo gasto **apenas** na execução do LLM (loop agentic com tool calls) em `classify_incident`, em milissegundos.

**Normal:** 200–2000 ms (depende do modelo e complexidade da resposta)

### Razão llm_latency_ms / total_latency_ms
Indica o quanto da latência total é devida ao LLM. Idealmente > 70% (o LLM é o fator dominante).

## 🎯 Cenários típicos de investigação

### "Por que essa ocorrência demorou 5 segundos?"
1. Consulte `audit.jsonl`: busque o occurrence_id e veja `llm_latency_ms`
2. Se llm_latency_ms ≈ total_latency_ms, o problema é o LLM (modelo lento, pergunta complexa)
3. Se llm_latency_ms << total_latency_ms, o problema está em outro nó (I/O em `prefetch_resident`?, gravação em disco lenta?)

### "Quais execuções tiveram erro?"
\`\`\`bash
grep '"status":"error"' reports/audit.jsonl | jq '{occurrence_id, reported_by, classification_error}'
\`\`\`

### "Qual é o occurrence_id do incidente do João Silva?"
\`\`\`bash
grep '"reported_by":"João Silva"' reports/audit.jsonl | tail -n 1 | jq '.occurrence_id'
\`\`\`

---

## 🔧 Manutenção

- **Arquivo audit.jsonl cresce indefinidamente**: para ambientes de produção, considere rotação diária/semanal
- **Logs podem ficar grandes**: configure o nível de log em produção para `INFO` (não `DEBUG`)
```

**Critério de aceição:**
- Documentação descreve os dois sinais (logs + auditoria)
- Exemplos de como consultar logs e auditoria
- Explicação de correlação por `occurrence_id`
- Guia de investigação de execução real
- Interpretação de latência

---

## Restrições

- Não modifique o prompt do classificador (`prompts/classifier.md`)
- Não altere a estrutura do estado além dos campos especificados
- Não remova ou altere nós existentes
- A latência deve ser medida em **milissegundos com até 3 casas decimais**
- O `audit.jsonl` deve ser append-only (nunca sobrescrever)

---

## Entrega

Ao final, apresente:

1. Modificações em `state.py` com novos campos
2. Novo módulo `nodes/audit.py` com classes e funções
3. Modificações em todos os nós com correlação por `occurrence_id`
4. Modificações em `classify_incident.py` com latência do LLM
5. Modificações em `graph.py` com instrumentação
6. Arquivo `docs/observability/README.md` completo

**Tarefas 7 e 8 (execução real + code review) serão executadas manualmente pelo desenvolvedor após a implementação.**

---

## 🎓 Aprendizados

Ao final deste card, você terá experiência em:

✅ Observabilidade estruturada (correlação + latência)
✅ Logging distribuído (transversal em todos os nós)
✅ Auditoria para conformidade
✅ Instrumentação de grafo com LangGraph

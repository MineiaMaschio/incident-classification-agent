# 📊 Observabilidade — Logs Estruturados + Auditoria

## Dois sinais complementares

A observabilidade no Incident Classification Agent é implementada através de dois canais:

1. **Logs estruturados**: Sinais em tempo real durante a execução
2. **Auditoria append-only**: Persistência histórica para análise e conformidade

Ambos são correlacionados pelo `occurrence_id` único de cada execução.

---

## 1️⃣ Logs Estruturados (stderr em tempo real)

### Formato

Cada log inclui um prefixo de correlação `[occurrence_id=<id>]` no início da mensagem:

```
2026-08-27 14:30:00.123 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO incident_classification_agent.nodes.validate_input — Iniciando validate_input...
2026-08-27 14:30:00.234 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO incident_classification_agent.nodes.prepare_context — Context prepared — histórico atualizado.
2026-08-27 14:30:00.500 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] DEBUG incident_classification_agent.nodes.classify_incident — LLM invocation started.
2026-08-27 14:30:02.100 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] DEBUG incident_classification_agent.nodes.classify_incident — LLM invocation ended — latency: 1600.00ms
2026-08-27 14:30:02.150 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO incident_classification_agent.nodes.classify_incident — Incident classified — category: ACCESS, severity: LOW
2026-08-27 14:30:02.200 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO incident_classification_agent.nodes.save_occurrence — Occurrence saved to reports/20260827T143002Z_65acbbde-af8d-426d-bb2f-739f7d1d7422.json
2026-08-27 14:30:02.250 [occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422] INFO incident_classification_agent.nodes.generate_response — Response generated e adicionada ao histórico.
```

### Nós que geram logs com correlação

Todos os nós do grafo incluem `[occurrence_id]` em seus logs:

- `validate_input` — Validação de entrada e detecção de injection/múltiplos incidentes
- `prepare_context` — Preparação do prompt com contexto histórico
- `prefetch_resident` — Consulta HTTP à API de moradores
- `classify_incident` — Invocação do LLM com loop agentic + latência
- `save_occurrence` — Persistência do JSON e atualização do session.json
- `generate_response` — Formatação e exibição da resposta final
- `handle_error` — Tratamento de erros de classificação

### Níveis de log

- **INFO**: Eventos principais (início/fim de nó, classificação concluída, arquivo salvo)
- **DEBUG**: Detalhes técnicos (contexto construído, latência, injeção pré-carregada)
- **WARNING**: Situações incomuns (injection detectado, falha de rede, rejeição de múltiplos incidentes)
- **ERROR**: Falhas (erro de classificação, I/O, dados inválidos)

### Como consultar logs em tempo real

**Filtrar por um occurrence_id específico:**
```bash
# Assumindo que logs estão no stderr ou em um arquivo
grep "occurrence_id=65acbbde-af8d-426d-bb2f-739f7d1d7422" <log-file>

# Ou capturando stderr durante execução:
uv run python -m incident_classification_agent.main examples/input.json 2>&1 | grep "occurrence_id=65acbbde"
```

**Ver apenas erros e warnings:**
```bash
grep -E "\[ERROR\]|\[WARNING\]" <log-file> | grep "occurrence_id=<id>"
```

**Ver latência do LLM:**
```bash
grep "LLM invocation ended" <log-file> | grep "occurrence_id=<id>"
```

---

## 2️⃣ Auditoria Estruturada (reports/audit.jsonl)

### Arquivo append-only

A auditoria é persistida em `reports/audit.jsonl` — arquivo de texto onde cada linha é um JSON válido (JSONL format). Uma linha por execução, para permitir leitura incremental.

### Formato de uma entrada

```json
{
  "occurrence_id": "65acbbde-af8d-426d-bb2f-739f7d1d7422",
  "started_at": "2026-08-27T14:30:00.123456+00:00",
  "ended_at": "2026-08-27T14:30:02.456789+00:00",
  "total_latency_ms": 2333.233,
  "llm_latency_ms": 1600.5,
  "nodes_executed": [
    "validate_input",
    "fan_out",
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

### Interpretação dos campos

| Campo | Significado |
|-------|-------------|
| `occurrence_id` | Identificador único da execução, correlacionado com logs e arquivo individual |
| `started_at` | Timestamp ISO 8601 UTC do início (antes de qualquer nó) |
| `ended_at` | Timestamp ISO 8601 UTC do fim (após generate_response) |
| `total_latency_ms` | Tempo total da execução em milissegundos (3 casas decimais) |
| `llm_latency_ms` | Tempo do LLM em classify_incident, ou `null` se error/rejected |
| `nodes_executed` | Lista ordenada dos nós que foram executados |
| `status` | `"success"`, `"error"` (erro de classificação), ou `"rejected"` (múltiplos incidentes) |
| `category` | Categoria classificada (ex: "ACCESS", "NOISE") ou `null` |
| `severity` | Severidade classificada (ex: "LOW", "HIGH") ou `null` |
| `multiple_incidents_detected` | `true` se relato continha múltiplos incidentes |
| `classification_error` | Mensagem de erro ou `null` se sucesso |
| `reported_by` | Nome de quem reportou |
| `apartment` | Apartamento envolvido ou `null` |
| `building` | Bloco/torre envolvido ou `null` |

### Use cases de auditoria

#### Análise de performance

**Latência média (últimas 100 execuções):**
```bash
tail -n 100 reports/audit.jsonl | jq '.total_latency_ms' | awk '{sum+=$1; count++} END {print "Média: " sum/count " ms"}'
```

**Percentil 95 de latência:**
```bash
cat reports/audit.jsonl | jq '.total_latency_ms' | sort -n | awk 'BEGIN {p=0.95} END {print $0}' FS='\n' | tail -1
```

**Latência do LLM (excluindo nulos):**
```bash
cat reports/audit.jsonl | jq 'select(.llm_latency_ms != null) | .llm_latency_ms' | awk '{sum+=$1; count++} END {print "LLM médio: " sum/count " ms"}'
```

#### Conformidade e rastreabilidade

**Todas as ocorrências de um apartamento:**
```bash
grep -F '"apartment":"101"' reports/audit.jsonl | jq '.occurrence_id, .reported_by, .started_at, .category, .severity'
```

**Todas as execuções com erro:**
```bash
grep -F '"status":"error"' reports/audit.jsonl | jq '.occurrence_id, .reported_by, .classification_error'
```

**Incidentes de HIGH severity (escalonados):**
```bash
grep -F '"severity":"HIGH"' reports/audit.jsonl | jq '.occurrence_id, .reported_by, .apartment, .building'
```

**Execuções rejeitadas (múltiplos incidentes):**
```bash
grep -F '"status":"rejected"' reports/audit.jsonl | jq '.occurrence_id, .reported_by'
```

#### Detecção de anomalias

**Execuções que demoraram mais de 5 segundos:**
```bash
cat reports/audit.jsonl | jq 'select(.total_latency_ms > 5000) | {occurrence_id, total_latency_ms, llm_latency_ms, nodes_executed}'
```

**Execuções onde o LLM demorou mais que 70% do tempo total (comportamento anômalo):**
```bash
cat reports/audit.jsonl | jq 'select(.llm_latency_ms != null and (.llm_latency_ms / .total_latency_ms > 0.7) == false) | {occurrence_id, total_latency_ms, llm_latency_ms, ratio: (.llm_latency_ms / .total_latency_ms)}'
```

---

## 🔗 Correlação por occurrence_id

O `occurrence_id` é a chave que conecta todos os sinais:

1. **Logs estruturados** — todos os logs de uma execução compartilham o mesmo `[occurrence_id]`
2. **Arquivo de ocorrência** — salvo em `reports/<timestamp>_<occurrence_id>.json`
3. **Auditoria** — uma linha em `reports/audit.jsonl` com o mesmo `occurrence_id`

### Investigação completa de uma execução

Suponha que você precisa investigar a execução com `occurrence_id = abc123def`:

**Passo 1: Leia os logs em tempo real (se disponível):**
```bash
grep "occurrence_id=abc123def" app.log
```

**Passo 2: Encontre o arquivo de ocorrência:**
```bash
ls reports/*abc123def*.json
# Exemplo: reports/20260827T143002Z_abc123def.json
```

**Passo 3: Inspecione o arquivo (resultado classificado):**
```bash
cat reports/20260827T143002Z_abc123def.json | jq .
```

**Passo 4: Consulte a auditoria:**
```bash
grep "abc123def" reports/audit.jsonl | jq .
```

**Passo 5: Analise a latência:**
```bash
grep "abc123def" reports/audit.jsonl | jq '{total_latency_ms, llm_latency_ms, nodes_executed}'
```

---

## ⏱️ Interpretação de Latência

### total_latency_ms

Tempo total da execução desde `execution_start_time` (início de `validate_input`) até `execution_end_time` (fim de `generate_response`).

**Composição típica:**
- Validação de entrada: 10–50 ms
- Detecção de múltiplos incidentes (LLM): 0–1000 ms (se necessário)
- Preparação de contexto: 5–20 ms
- Prefetch de residente (HTTP): 50–500 ms (I/O de rede)
- Classificação (LLM + tools): 800–2500 ms
- Persistência (I/O de disco): 10–50 ms
- Geração de resposta: 5–10 ms

**Faixa normal:** 500–3500 ms (depende da velocidade do LLM e da rede)

### llm_latency_ms

Tempo gasto **apenas** no loop agentic de `classify_incident`, desde o primeiro `llm_with_tools.invoke()` até o resultado final. Inclui:

- Chamadas ao LLM
- Execução de tool calls (lookup_resident, get_session_history)
- Espera por respostas das tools

**Faixa normal:** 200–2000 ms

### Razão llm_latency_ms / total_latency_ms

Indica o quanto da latência total é devida ao LLM. Valores típicos:

- **> 70%**: Normal — o LLM é o fator dominante
- **50–70%**: I/O de rede (prefetch) está significativo
- **< 50%**: Possível anomalia — verificar se há travamento em outro nó (I/O de disco, rede, detecção de múltiplos incidentes)

### Cenário: latência total muito alta

Se `total_latency_ms > 5000`:

1. Consulte `audit.jsonl` para esse `occurrence_id`
2. Compare `llm_latency_ms` com `total_latency_ms`:
   - Se `llm_latency_ms ≈ total_latency_ms`: Problema no LLM (modelo lento, pergunta complexa, timeout)
   - Se `llm_latency_ms << total_latency_ms`: Problema fora do LLM — verifique logs para identifi car qual nó está lento

**Exemplo: investigação de latência alta**
```bash
# Encontre execução lenta
cat reports/audit.jsonl | jq 'select(.total_latency_ms > 5000) | .occurrence_id' | head -1

# Substitua <id> pelo resultado
id="<id>"

# Veja a latência
grep "$id" reports/audit.jsonl | jq '{total_latency_ms, llm_latency_ms}'

# Se llm_latency_ms << total_latency_ms, verifique logs
grep "occurrence_id=$id" app.log | grep -E "prefetch_resident|prepare_context|save_occurrence"
```

---

## 🎯 Cenários Típicos de Investigação

### "Por que essa ocorrência foi rejeitada?"

```bash
id="<occurrence_id>"
grep "$id" reports/audit.jsonl | jq '{status, multiple_incidents_detected, reported_by}'
```

Se `status = "rejected"` e `multiple_incidents_detected = true`, o usuário reportou múltiplos incidentes. Consulte o arquivo JSON para ver o `user_input` original.

### "Quais são as execuções mais lentas?"

```bash
cat reports/audit.jsonl | jq -s 'sort_by(.total_latency_ms) | reverse | .[0:10] | .[] | {occurrence_id, total_latency_ms, reported_by}'
```

### "Qual é a latência média por categoria?"

```bash
cat reports/audit.jsonl | jq -s 'group_by(.category) | map({category: .[0].category, avg_latency_ms: (map(.total_latency_ms) | add / length)}) | sort_by(.avg_latency_ms) | reverse'
```

### "Quantas execuções tiveram erro?"

```bash
grep '"status":"error"' reports/audit.jsonl | wc -l
```

### "Qual é o reporter que mais gera incidentes?"

```bash
cat reports/audit.jsonl | jq -s 'group_by(.reported_by) | map({reported_by: .[0].reported_by, count: length}) | sort_by(.count) | reverse | .[0:5]'
```

### "Quais são os incidentes não resolvidos (sem arquivo salvo)?"

Incidentes com `status = "success"` devem ter um arquivo salvo. Se não encontrar, pode indicar erro de I/O:

```bash
# Liste todos os occurrence_id de sucesso
grep '"status":"success"' reports/audit.jsonl | jq -r '.occurrence_id' > /tmp/success_ids.txt

# Verifique quais NÃO têm arquivo correspondente
while read id; do
  if ! ls reports/*${id}.json 2>/dev/null; then
    echo "Faltante: $id"
  fi
done < /tmp/success_ids.txt
```

---

## 🔧 Manutenção e Operação

### Rotação de audit.jsonl

O arquivo `audit.jsonl` cresce indefinidamente. Para ambientes de produção, considere rotação:

**Rotação diária (manual):**
```bash
# No início de cada dia:
if [ -f reports/audit.jsonl ]; then
  mv reports/audit.jsonl reports/audit_$(date +%Y%m%d).jsonl
fi
# Um novo audit.jsonl será criado na próxima execução
```

**Rotação automática (via cron, executar diariamente às 00:00):**
```bash
0 0 * * * [ -f /path/to/reports/audit.jsonl ] && mv /path/to/reports/audit.jsonl "/path/to/reports/audit_$(date +\%Y\%m\%d).jsonl"
```

### Análise histórica

Com rotação diária, você pode analisar tendências:

```bash
# Latência média de cada dia
for f in reports/audit_*.jsonl; do
  echo "$(basename $f):"
  cat "$f" | jq '.total_latency_ms' | awk '{sum+=$1; count++} END {print "  Média: " sum/count " ms"}'
done
```

### Limpeza de logs antigos

Se houver logs estruturados em arquivo (não apenas stderr), considere:

```bash
# Remover logs com mais de 30 dias
find /var/log/incident-agent -name "*.log" -mtime +30 -delete
```

### Monitoramento em tempo real

**Assistir execuções em tempo real (via logs):**
```bash
tail -f app.log | grep "occurrence_id="
```

**Assistir auditoria em tempo real:**
```bash
watch 'tail -n 5 reports/audit.jsonl | jq .'
```

---

## 📋 Checklist de Observabilidade

Ao revisar observabilidade de uma execução:

- [ ] Todo log contém `[occurrence_id=...]` no início
- [ ] Arquivo `reports/<timestamp>_<occurrence_id>.json` existe para status="success"
- [ ] Uma linha correspondente existe em `reports/audit.jsonl`
- [ ] `total_latency_ms` está em range esperado (500–3500 ms)
- [ ] `llm_latency_ms` > 0 (exceto para rejected/error)
- [ ] `nodes_executed` lista todos os nós que deveriam ter executado
- [ ] Campos de correlação (`occurrence_id`, `reported_by`) são consistentes

---

## 🔗 Referências

- **Logs estruturados**: Úteis para investigação tática em tempo real
- **Auditoria append-only**: Essencial para conformidade, análise histórica e detecção de anomalias
- **Correlação por occurrence_id**: Permite rastreamento ponta-a-ponta de uma execução

Juntos, esses sinais fornecem **visibilidade completa** do agente — do evento até a persistência, com latência instrumentada e rastreabilidade garantida.

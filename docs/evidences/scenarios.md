# Cenários de Uso — Incident Classification Agent

> **Documento:** evidências formais dos dois cenários exigidos pelo Projeto Avaliativo M2.2
> **Criado em:** Card 01 — Revisar e documentar o estado atual
> **Branch:** `docs/project-review`

---

## Cenário 1 — Relato válido: classificação bem-sucedida e arquivo salvo

### Descrição

O porteiro registra a chegada de uma visitante à portaria. O agente valida a entrada, consulta o
cadastro de moradores, verifica o histórico de sessão, classifica o incidente e persiste o
registro em disco.

### Arquivo de entrada (`examples/input.json`)

```json
{
    "user_input": "Às 09h15 Ana Mendes chegou à portaria informando que iria visitar Carlos Mendes, do apartamento 101, bloco A.",
    "reported_by": "João Silva",
    "reported_at": "2026-07-14T09:15:00Z"
}
```

### Log de execução

```
2026-08-25 20:19:24,055 [INFO] graph — Graph compiled successfully with MemorySaver checkpointer.
2026-08-25 20:19:25,652 [INFO] validate_input — Multiple incidents detection result: SINGLE
2026-08-25 20:19:25,657 [INFO] validate_input — Input validated — occurrence_id: 65acbbde-af8d-426d-bb2f-739f7d1d7422 | multiple_incidents: False
2026-08-25 20:19:25,659 [INFO] prepare_context — Context prepared for occurrence_id: 65acbbde-af8d-426d-bb2f-739f7d1d7422
2026-08-25 20:19:45,672 [INFO] lookup_resident — Resident found for apartment 101 / building A
2026-08-25 20:19:47,875 [INFO] get_session_history — No session history for apartment 101 / building A
2026-08-25 20:20:01,726 [INFO] classify_incident — Severity reasoning — base: LOW | recurrence: false (0) | final: LOW
2026-08-25 20:20:01,726 [INFO] classify_incident — Incident classified — category: Category.ACCESS, severity: Severity.LOW, occurrence_id: 65acbbde-af8d-426d-bb2f-739f7d1d7422
2026-08-25 20:20:01,731 [INFO] save_occurrence — Occurrence saved to reports/20260825T232001Z_65acbbde-af8d-426d-bb2f-739f7d1d7422.json
2026-08-25 20:20:01,732 [INFO] session — Session updated — total records: 1
2026-08-25 20:20:01,736 [INFO] generate_response — Response generated for occurrence_id: 65acbbde-af8d-426d-bb2f-739f7d1d7422
```

### Fluxo executado

```
START
  → validate_input
      • campos obrigatórios presentes ✔
      • occurrence_id gerado: 65acbbde-af8d-426d-bb2f-739f7d1d7422
      • detecção de múltiplos incidentes: SINGLE → prossegue
  → prepare_context
      • template do classificador carregado
      • histórico de sessão: nenhuma ocorrência anterior para apt 101 / bloco A
      • prompt montado e adicionado ao conversation_history
  → classify_incident  (3 chamadas HTTP ao Ollama)
      • tool call: lookup_resident(apartment="101", building="A")
        → residente encontrado: Carlos Mendes
        → Ana Mendes consta na lista de visitantes autorizados
      • tool call: get_session_history(apartment="101", building="A")
        → nenhuma ocorrência anterior
      • reasoning: base=LOW | recurrence=false (0) | final=LOW
      • JSON de classificação extraído com sucesso
  → save_occurrence
      • arquivo JSON salvo em reports/20260825T232001Z_65acbbde-af8d-426d-bb2f-739f7d1d7422.json
      • session.json atualizado — total: 1 registro
      • severidade LOW → sem escalonamento
  → generate_response
      • resposta de sucesso formatada e exibida
END
```

### Saída no terminal

```
✅ Ocorrência registrada com sucesso.

🆔 ID: 65acbbde-af8d-426d-bb2f-739f7d1d7422
📁 Categoria: Category.ACCESS
⚠️  Severidade: Severity.LOW
🏠 Apartamento: 101
🏢 Bloco: A
👥 Envolvidos: Ana Mendes, Carlos Mendes
🔍 Morador cadastrado: Carlos Mendes
   Visitantes autorizados: Ana Mendes, Roberto Mendes

📝 Resumo: Visitante autorizado Ana Mendes visitando Carlos Mendes no apartamento 101, bloco A.

💾 Arquivo salvo em: reports/20260825T232001Z_65acbbde-af8d-426d-bb2f-739f7d1d7422.json
```

### Arquivo JSON gerado (`reports/20260825T232001Z_65acbbde-af8d-426d-bb2f-739f7d1d7422.json`)

```json
{
  "occurrence_id": "65acbbde-af8d-426d-bb2f-739f7d1d7422",
  "reported_by": "João Silva",
  "reported_at": "2026-07-14T09:15:00Z",
  "user_input": "Às 09h15 Ana Mendes chegou à portaria informando que iria visitar Carlos Mendes, do apartamento 101, bloco A.",
  "category": "ACCESS",
  "severity": "LOW",
  "involved_people": [
    "Ana Mendes",
    "Carlos Mendes"
  ],
  "apartment": "101",
  "building": "A",
  "summary": "Visitante autorizado Ana Mendes visitando Carlos Mendes no apartamento 101, bloco A.",
  "resident_info": {
    "found": true,
    "apartment": "101",
    "building": "A",
    "resident_name": "Carlos Mendes",
    "authorized_visitors": [
      "Ana Mendes",
      "Roberto Mendes"
    ],
    "vehicles": [
      "ABC-1234",
      "DEF-5678"
    ],
    "phone": "(11) 9****-1234"
  },
  "saved_at": "2026-08-25T23:20:01Z"
}
```

### Critérios de sucesso verificados

| Critério | Status |
|---|---|
| Entrada validada pelo schema Pydantic | ✅ |
| `occurrence_id` único gerado | ✅ |
| Detecção de múltiplos incidentes: SINGLE | ✅ |
| Tool `lookup_resident` consultada — morador encontrado | ✅ |
| Tool `get_session_history` consultada — sem histórico | ✅ |
| Reasoning de severidade registrado nos logs | ✅ |
| Classificação em JSON estruturado extraída | ✅ |
| Arquivo JSON salvo em `reports/` | ✅ |
| `session.json` atualizado | ✅ |
| Severidade LOW — sem escalonamento | ✅ |
| Resposta formatada exibida ao usuário | ✅ |

---

## Cenário 2 — Relato com múltiplos incidentes: rejeição antecipada

### Descrição

O porteiro submete um único relato descrevendo dois eventos independentes. O agente detecta a
ambiguidade via LLM na etapa de validação, rejeita a entrada antes de qualquer classificação e
orienta o usuário a submeter um relato por vez. Nenhum arquivo é salvo em `reports/`.

### Arquivo de entrada (`examples/input_multiple.json`)

```json
{
    "user_input": "Às 10h um entregador deixou uma encomenda na portaria para o apartamento 202. Também quero registrar que às 11h teve uma briga no estacionamento entre moradores do bloco A.",
    "reported_by": "Ana Lima",
    "reported_at": "2026-08-25T11:00:00Z"
}
```

### Log de execução

```
2026-08-25 20:21:28,509 [INFO] graph — Graph compiled successfully with MemorySaver checkpointer.
2026-08-25 20:21:29,278 [INFO] validate_input — Multiple incidents detection result: MULTIPLE
2026-08-25 20:21:29,279 [INFO] validate_input — Input validated — occurrence_id: bc041a95-380d-4614-bce6-3a94c2293d42 | multiple_incidents: True
2026-08-25 20:21:29,279 [WARNING] validate_input — Multiple incidents detected — short-circuiting to generate_response.
2026-08-25 20:21:29,280 [INFO] generate_response — Response generated for occurrence_id: bc041a95-380d-4614-bce6-3a94c2293d42
2026-08-25 20:21:28,509 [INFO] main — Agent finished — output_file: None
```

### Fluxo executado

```
START
  → validate_input
      • campos obrigatórios presentes ✔
      • occurrence_id gerado: bc041a95-380d-4614-bce6-3a94c2293d42
      • detecção de múltiplos incidentes via LLM: MULTIPLE → rejeição antecipada
      • multiple_incidents_detected = True
      • _route_after_validate → "generate_response"
  → generate_response
      • formato: _format_multiple_incidents
      • orientação exibida ao usuário
END
```

> Os nós `prepare_context`, `classify_incident` e `save_occurrence` **não foram executados**.
> Nenhum arquivo foi salvo em `reports/`. `output_file = None`.

### Saída no terminal

```
⚠️  Múltiplos incidentes detectados no relato.

Este sistema aceita apenas um incidente por vez para garantir
rastreabilidade e classificação precisa de cada ocorrência.

🆔 ID gerado: bc041a95-380d-4614-bce6-3a94c2293d42

Por favor, divida o relato e submeta cada incidente separadamente.
```

### Critérios de sucesso verificados

| Critério | Status |
|---|---|
| Entrada com múltiplos incidentes detectada pelo LLM | ✅ |
| Fluxo encerrado antes de `prepare_context` | ✅ |
| Nenhuma chamada ao LLM classificador | ✅ |
| Nenhum arquivo salvo em `reports/` (`output_file = None`) | ✅ |
| Usuário orientado a dividir o relato | ✅ |
| `occurrence_id` gerado para rastreabilidade da tentativa | ✅ |

### Relatos equivalentes para submissão separada

**Relato 1 — Entrega de encomenda:**
```json
{
    "user_input": "Às 10h um entregador deixou uma encomenda na portaria para o apartamento 202.",
    "reported_by": "Ana Lima",
    "reported_at": "2026-08-25T10:00:00Z"
}
```

**Relato 2 — Briga no estacionamento:**
```json
{
    "user_input": "Às 11h houve uma briga no estacionamento entre moradores do bloco A.",
    "reported_by": "Ana Lima",
    "reported_at": "2026-08-25T11:00:00Z"
}
```

---

## Resumo comparativo

| | Cenário 1 — Fluxo principal | Cenário 2 — Rejeição antecipada |
|---|---|---|
| **Entrada** | Relato válido, incidente único | Relato com dois eventos independentes |
| **Nós executados** | validate → prepare → classify → save → response | validate → response |
| **Chamadas HTTP ao Ollama** | 3 (validate + 2 tool calls + classify) | 1 (validate) |
| **Tools chamadas** | `lookup_resident`, `get_session_history` | Nenhuma |
| **Arquivo salvo** | `reports/20260825T232001Z_65acbbde...json` | Nenhum |
| **`output_file`** | Caminho do arquivo | `None` |
| **Comportamento** | Classificação + persistência | Rejeição + orientação |
| **Referência de código** | `classify_incident.py`, `save_occurrence.py` | `validate_input.py` (`_detect_multiple_incidents`) |

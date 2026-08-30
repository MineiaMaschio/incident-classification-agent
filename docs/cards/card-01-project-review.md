# 📋 Card 01 — Revisar e documentar o estado atual

> **Branch:** `docs/project-review`

## 🎯 Objetivo

Registrar formalmente o que já está implementado no projeto, criar a estrutura de pastas de documentação e documentar os dois cenários de uso exigidos pelo avaliativo.

---

## 📌 Escopo

### Revisão do checklist

* [x] Mapear cada item do checklist da Parte 2 contra o código existente
* [x] Atualizar o `plano_projeto_avaliativo_incidentes.md` marcando os itens já concluídos

### Estrutura de documentação

* [x] Criar as pastas: `docs/prompts`, `docs/qa`, `docs/evidences`, `docs/observability`, `docs/devops`, `docs/low-code`
* [x] Adicionar `.gitkeep` em cada pasta para garantir versionamento

### Cenários de uso

* [x] Documentar o cenário principal: relato válido → classificação → arquivo salvo
* [x] Documentar o cenário de risco: entrada maliciosa ou relato com múltiplos incidentes → rejeição

---

## 🏁 Resultado Esperado

* [x] Checklist atualizado refletindo o estado real do projeto
* [x] Estrutura de `docs/` criada e versionada
* [x] Dois cenários de uso documentados formalmente

---

## 📎 Referências

* `plano_projeto_avaliativo_incidentes.md`
* Análise do estado atual do projeto

---

## 📝 Detalhamento da execução

### Mapeamento do checklist — estado atual identificado

A análise do código base revelou o seguinte panorama antes de qualquer implementação da Parte 2:

#### ✅ Já implementado e atendendo aos requisitos

| Requisito | Evidência no código |
|---|---|
| Estado compartilhado e tipado | `AgentState` como `TypedDict` em `state.py` |
| Nós com responsabilidades claras | 6 nós em `nodes/` com docstrings completas |
| Edges explícitas e ramificação condicional | `_route_after_validate` e `_route_after_classify` em `graph.py` |
| Execução sequencial + condição de parada | Fluxo principal documentado; loop limitado a 5 iterações |
| Tools funcionais | `lookup_resident`, `get_session_history`, `save_occurrence` |
| Validação de payloads e tratamento de erros | `IncidentInput` (Pydantic), `handle_error`, retry no LLM |
| Memória e contexto | `MemorySaver` + `session.json` + injeção no prompt |
| Recuperação de histórico | `get_session_history` + `prepare_context` |
| Credenciais fora do repositório | `.gitignore` + `python-dotenv` + `.env.example` |
| Validação de entrada antes de tools | `validate_input` + `IncidentInput` |
| Logs estruturados | `logging` em todos os módulos |
| Retry limitado e fallback | `.with_retry(stop_after_attempt=3)` no LLM |
| Saída estruturada JSON + Pydantic | `reports/<uuid>.json` + `IncidentInput` |
| Separação LLM vs. regras determinísticas | LLM classifica; nós determinísticos validam, persistem, roteiam |

#### ❌ Pendente de implementação

| Requisito | Card responsável |
|---|---|
| Paralelização no grafo | Card 03 |
| Integração por API HTTP (lookup via FastAPI) | Card 02 |
| Detecção e bloqueio explícito de prompt injection | Card 04 |
| Limites de autonomia formalmente documentados | Card 04 |
| Garantia de não-exposição de dados sensíveis (phone) | Card 04 |
| Segundo sinal de observabilidade (audit.jsonl) | Card 05 |
| `occurrence_id` em todos os logs | Card 05 |
| Registro de latência | Card 05 |
| Code reviews com IA registrados | Cards 02–05 e Card 06 |
| Testes automatizados com IA | Card 06 |
| Teste de integração E2E | Card 06 |
| Pipeline CI (lint + test + validate-config) | Card 07 |
| Análise de anomalias com IA | Card 08 |
| Estimativa de risco de falha | Card 08 |
| Integração n8n (webhook HIGH) | Card 09 |
| README completo (seções faltantes) | Card 10 |

---

### Estrutura de documentação criada

```
docs/
├── prompts/          .gitkeep ✅
├── qa/               .gitkeep ✅
├── evidences/
│   ├── .gitkeep      ✅
│   └── scenarios.md  ✅ (criado neste card)
├── observability/    .gitkeep ✅
├── devops/           .gitkeep ✅
└── low-code/         .gitkeep ✅
```

---

### Cenários de uso documentados

Ambos os cenários foram documentados formalmente em `docs/evidences/scenarios.md`.

**Cenário 1 — Fluxo principal** (execução real — `examples/input.json`):
- Entrada: visita de Ana Mendes ao apartamento 101 / bloco A, reportada por João Silva
- `occurrence_id`: `65acbbde-af8d-426d-bb2f-739f7d1d7422`
- Nós executados: `validate_input → prepare_context → classify_incident → save_occurrence → generate_response`
- Tools chamadas: `lookup_resident` (morador encontrado) + `get_session_history` (sem histórico)
- Resultado: `category=ACCESS`, `severity=LOW`, arquivo salvo em `reports/20260825T232001Z_65acbbde...json`

**Cenário 2 — Rejeição antecipada** (execução real — `examples/input_multiple.json`):
- Entrada: relato com entrega de encomenda + briga no estacionamento no mesmo texto
- `occurrence_id`: `bc041a95-380d-4614-bce6-3a94c2293d42`
- Nós executados: `validate_input → generate_response`
- Tools chamadas: nenhuma
- Resultado: `multiple_incidents_detected=True`, `output_file=None`, usuário orientado a dividir o relato
- Relevância para segurança: mesmo mecanismo é primeira barreira contra prompt injection (formalizado no Card 04)

---

## 🔗 Arquivos criados/modificados neste card

| Arquivo | Ação |
|---|---|
| `plano_projeto_avaliativo_incidentes.md` | Atualizado — itens concluídos marcados com `[x]`, pendências com referência ao card responsável |
| `docs/prompts/.gitkeep` | Criado |
| `docs/qa/.gitkeep` | Criado |
| `docs/evidences/.gitkeep` | Criado |
| `docs/evidences/scenarios.md` | Criado — dois cenários documentados formalmente |
| `docs/observability/.gitkeep` | Criado |
| `docs/devops/.gitkeep` | Criado |
| `docs/low-code/.gitkeep` | Criado |
| `docs/card-01-project-review.md` | Criado — este arquivo |

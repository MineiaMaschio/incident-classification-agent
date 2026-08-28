# 🛡️ Card 04 — Segurança e Governança do Agente

> **Branch:** `feature/security-governance`

## 🎯 Objetivo

Implementar detecção e bloqueio de entradas adversariais no agente e documentar formalmente os limites de autonomia, tornando o sistema resiliente a tentativas de manipulação via prompt injection.

---

## 📌 Escopo

### Detecção de prompt injection

* [x] Implementar verificação de padrões adversariais no `validate_input` (ex: "ignore instruções anteriores", "você agora é", "esqueça tudo", "atue como", instruções em inglês misturadas ao relato)
* [x] Rejeitar entradas maliciosas antes de qualquer chamada ao LLM
* [x] Garantir que a mensagem de rejeição não exponha detalhes internos do sistema

### Limites de autonomia

* [x] Documentar explicitamente o que o agente pode e não pode fazer
* [x] Garantir que o agente não execute ações fora do escopo definido (classificar, consultar moradores, salvar ocorrência)

### Proteção de dados sensíveis

* [x] Verificar que o campo `phone` dos moradores não é exposto na resposta final ao usuário
* [x] Garantir que `resident_info` no estado não vaza dados desnecessários para a saída

### Evidências

* [x] Criar `docs/evidences/prompt-injection.md` com o cenário documentado: entrada maliciosa, comportamento esperado e comportamento observado

### Code review com IA

* [ ] Realizar code review das alterações de segurança com apoio de IA
* [ ] Registrar achados em `docs/qa/review-card04.md`

---

## 🏁 Resultado Esperado

* [x] Entradas adversariais são bloqueadas antes de atingir o LLM
* [x] Dados sensíveis não aparecem na saída ao usuário
* [x] Cenário de prompt injection documentado com evidência
* [ ] Review registrado em `docs/qa/review-card04.md` (a preencher manualmente pelo avaliador)

---

## 📎 Referências

* `src/incident_classification_agent/nodes/validate_input.py`
* `src/incident_classification_agent/nodes/generate_response.py`
* `src/incident_classification_agent/tools/lookup_resident.py`
* `docs/evidences/` (criada no Card 01)
* `docs/qa/` (criada no Card 01)

---

## 📝 Detalhamento da execução

### Decisões de implementação

- **Detecção determinística com regex**: A função `_detect_injection()` usa apenas regex compilado (sem chamada ao LLM) para bloquear padrões adversariais na camada de validação, antes de qualquer invocação de modelo.

- **Padrões detectáveis em 4 categorias**:
  - Reescrita de papel: "você agora é", "you are now", "act as", "atue como", "finja que é", "pretend you are"
  - Descarte de instruções: "ignore instruções anteriores", "ignore previous instructions", "esqueça tudo", "forget everything", "ignore as regras", "ignore your instructions"
  - Escape de contexto: "novo prompt", "new prompt", "system prompt", "ignore o sistema", "ignore the system"
  - Injeção direta: "### instrução", "### instruction", "[instrução]", "[system]", "<|im_start|>", "<|system|>"

- **Roteamento early-exit**: Quando `injection_detected=True`, o fluxo é encerrado imediatamente em `_route_after_validate()` sem chamar `_detect_multiple_incidents()`, economizando uma chamada ao LLM.

- **Mensagem genérica sem detalhes técnicos**: A resposta em `_format_injection_detected()` não menciona "injection", "adversarial", "regex", "padrão" ou qualquer detalhe de implementação.

- **Proteção de dados sensíveis**: O campo `phone` continua armazenado em `resident_info` no estado interno (necessário para futuros escalonamentos), mas é intencionalmente omitido na saída em `_format_success()`.

### Arquivos criados/modificados

| Arquivo | Ação |
|---|---|
| `src/incident_classification_agent/state.py` | Modificado — campo `injection_detected: bool \| None` adicionado com docstring |
| `src/incident_classification_agent/nodes/validate_input.py` | Modificado — `_INJECTION_PATTERNS` regex compilado, função `_detect_injection()` criada, `_route_after_validate()` atualizado, `validate_input()` chamando `_detect_injection()` antes de `_detect_multiple_incidents()` |
| `src/incident_classification_agent/nodes/generate_response.py` | Modificado — `_format_injection_detected()` criada, `generate_response()` checando `injection_detected` primeiro, comentário "phone intencionalmente omitido" adicionado em `_format_success()` |
| `src/incident_classification_agent/tools/lookup_resident.py` | Modificado — docstring atualizada explicando que `phone` está disponível internamente mas não é exposto ao usuário |
| `docs/evidences/autonomy-limits.md` | Criado — 5 ações permitidas e 6 ações bloqueadas documentadas |
| `docs/evidences/prompt-injection.md` | Criado — cenário documentado com evidência real de execução |
| `examples/input_injection.json` | Criado — entrada adversarial com dois padrões para teste direto |

### Evidências de execução

**Execução 1 — Entrada legítima** (`examples/input.json`):

```
2026-08-27 22:20:34,799 [INFO] incident_classification_agent.nodes.validate_input — Input validated — occurrence_id: b1707f65-2394-4fe6-891f-d5cfc36d6ae8 | injection: False | multiple_incidents: False
```

Resultado: `category=ACCESS`, `severity=LOW`, arquivo salvo em `reports/20260828T012123Z_b1707f65-2394-4fe6-891f-d5cfc36d6ae8.json`. Fluxo completo funciona normalmente.

**Execução 2 — Entrada adversarial** (`examples/input_injection.json`):

```
2026-08-27 22:21:43,432 [WARNING] incident_classification_agent.nodes.validate_input — Prompt injection pattern detected — padrão: Ignore instruções anteriores
2026-08-27 22:21:43,432 [WARNING] incident_classification_agent.nodes.validate_input — Prompt injection detected — occurrence_id: 298d8285-6b86-431c-8a15-f564ebcd37ee
2026-08-27 22:21:43,432 [INFO] incident_classification_agent.nodes.validate_input — Input validated — occurrence_id: 298d8285-6b86-431c-8a15-f564ebcd37ee | injection: True | multiple_incidents: False
2026-08-27 22:21:43,432 [WARNING] incident_classification_agent.nodes.validate_input — Injection detected — short-circuiting to generate_response.
```

Resultado: Mensagem genérica exibida, `output_file=None`, nenhum arquivo salvo. **Nenhuma chamada ao LLM foi realizada.**

### Achados do code review com IA

> _A preencher pelo avaliador._

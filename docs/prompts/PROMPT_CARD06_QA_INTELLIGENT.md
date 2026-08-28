# 🧪 PROMPT — Card 06: QA Inteligente & Consolidação de Reviews

**Objetivo:** Consolidar code reviews (Cards 02–05), aprofundar análise de um deles, gerar testes automatizados com IA e implementar ao menos um teste E2E.

---

## 📋 Tarefas

### Tarefa 1: Consolidar Achados de Reviews (Outputs)

**Deliverables:**
- `docs/qa/code-review-summary.md` — visão consolidada de todos os 4 reviews
- Justificativa de qual review aprofundar

**Instruções:**

1. **Ler os 4 reviews:**
   - `docs/qa/review-card02.md` (FastAPI integration)
   - `docs/qa/review-card03.md` (LangGraph parallelization)
   - `docs/qa/review-card04.md` (Prompt injection detection)
   - `docs/qa/review-card05.md` (Observability & state propagation)

2. **Criar matriz consolidada em `code-review-summary.md`:**
   ```
   | Card | PR | Status | Críticos | Maiores | Menores | Categoria | Foco |
   ```

3. **Identificar padrões recorrentes:**
   - Qual tipo de achado mais frequente? (ex: testes faltando, estado não propagando, validação faltando)
   - Qual módulo tem mais achados? (ex: `nodes/validate_input`, tools, roteamento)
   - Qual severidade predominante?

4. **Escolher 1 review para aprofundamento** baseado em critério:
   - Maior impacto em risco, segurança ou corretude
   - Justificativa clara

5. **Estrutura do `code-review-summary.md`:**
   ```markdown
   # Code Review Summary — Cards 02–05
   
   ## Visão Consolidada
   [Tabela com todos os achados, agrupados por card]
   
   ## Padrões Recorrentes
   - [tipo de problema mais frequente]
   - [módulo com mais achados]
   - [severidade predominante]
   
   ## Review Aprofundado: Card [X] — [Título]
   ### Justificativa
   [Por que este review foi escolhido]
   
   ### Achados Críticos — Análise Detalhada
   [Expandir cada achado crítico: contexto, evidência, raiz do problema]
   
   ### Plano de Remediação
   [Passos para corrigir]
   
   ### Testes Necessários
   [Quais testes precisam ser criados para validar as correções]
   ```

---

### Tarefa 2: Criar Testes Unitários (Outputs)

**Deliverables:**
- `tests/test_validate_input.py` — testes para `validate_input`
- `tests/test_classify_incident.py` — testes para `classify_incident` + `_extract_json`
- `tests/test_routing.py` — testes para roteamento (`_route_after_validate`, `_route_after_classify`)
- `tests/test_lookup_resident.py` — testes para tool `lookup_resident`

**Instrução Geral:**
Gerar testes com apoio de IA considerando:
- Cobertura de cenários críticos (sucesso, erro, edge cases)
- Use `pytest` + `mock` (compatível com projeto existente)
- Cada teste deve ter docstring explicando o cenário
- Seguir padrão do `tests/test_llm.py` já existente

---

#### Teste 2.1: `validate_input` — Casos Críticos

**Arquivo:** `tests/test_validate_input.py`

**Cenários:**
1. ✅ Entrada válida (user_input, reported_by obrigatórios)
2. ❌ Campo `user_input` vazio → ValidationError
3. ❌ Campo `reported_by` vazio → ValidationError
4. ❌ Campo `reported_by` com caracteres inválidos → ValidationError
5. ❌ Múltiplos incidentes detectados (keywords: "também", "além", ",") → router retorna "generate_response"
6. ❌ Prompt injection detectado (reescrita de papel, escape) → bloqueado com mensagem genérica
7. ✅ Entrada válida com occurrence_id propagado → estado contém occurrence_id ao final

**Especificações:**
- Mock do estado do LangGraph
- Assert de retorno do nó
- Assert de campos obrigatórios retornados
- Assert de occurrence_id no estado (bug do Card 05)

---

#### Teste 2.2: `classify_incident` — `_extract_json` & Roteamento

**Arquivo:** `tests/test_classify_incident.py`

**Cenários:**
1. ✅ JSON válido em resposta LLM → parsed corretamente
2. ❌ JSON inválido → fallback com categoria "UNKNOWN"
3. ✅ JSON embutido em texto ("...```json {...}```...") → extraído
4. ❌ Sem JSON na resposta → "UNKNOWN"
5. ✅ llm_start_time e llm_end_time propagados no estado (bug do Card 05)

**Especificações:**
- Mock do LLM (classe mock com `invoke()` que retorna string com JSON)
- Assert de parsing correto
- Assert de campos no estado retornado (inclusive llm_start_time, llm_end_time)

---

#### Teste 2.3: Roteamento Condicional

**Arquivo:** `tests/test_routing.py`

**Cenários:**
1. ✅ `_route_after_validate` com estado válido → "prepare_context"
2. ✅ `_route_after_validate` com múltiplos incidentes → "generate_response"
3. ✅ `_route_after_validate` com injection detectada → "generate_response"
4. ✅ `_route_after_classify` com severity="HIGH" → "save_occurrence"
5. ✅ `_route_after_classify` com severity="LOW" → "generate_response"

**Especificações:**
- Função direta de roteamento testada
- Estados de entrada bem definidos
- Assert do retorno (string com nome do nó)

---

#### Teste 2.4: `lookup_resident` — Tool HTTP

**Arquivo:** `tests/test_lookup_resident.py`

**Cenários:**
1. ✅ Resposta da API bem-sucedida (200 OK) → resident_info retornado
2. ❌ API retorna 404 → {"found": False}
3. ❌ Timeout de conexão (httpx.ConnectTimeout) → {"found": False, "error": "..."}
4. ❌ API indisponível (5xx) → {"found": False, "error": "..."}
5. ❌ Resposta malformada (ValidationError) → {"found": False, "error": "..."}

**Especificações:**
- Mock do `httpx.AsyncClient` ou use `responses` library
- Assert de retorno conforme schema esperado
- Assert de logging (warning em timeout, error em falhas)

---

### Tarefa 3: Teste de Integração E2E (Outputs)

**Deliverable:**
- `tests/test_e2e_incident_flow.py` — teste E2E completo

**Fluxo E2E:**
```
Entrada: {
  "user_input": "Houve um vazamento de água no apartamento 101.",
  "reported_by": "joao@email.com",
  "thread_id": "test-thread-001"
}
    ↓
Grafo executa:
  - validate_input (gera occurrence_id)
  - prefetch_resident (busca info se disponível)
  - prepare_context (prepara contexto para LLM)
  - classify_incident (chama LLM)
  - save_occurrence (salva arquivo JSON em reports/)
  - generate_response (produz resposta)
    ↓
Saída esperada:
  - Arquivo JSON em `reports/` com nome padrão
  - Response contém category, severity
  - Audit entry em `reports/audit.jsonl`
```

**Instruções:**

1. **Mock do LLM:**
   - Retorna JSON válido com category="MANUTENÇÃO", severity="MEDIUM"

2. **Setup de fixtures:**
   ```python
   @pytest.fixture
   def temp_reports_dir():
       """Diretório temporário para reports"""
       # Usar pytest tmp_path
   ```

3. **Asserções:**
   - [ ] Grafo completou sem exceção
   - [ ] Arquivo JSON criado em `reports/`
   - [ ] Conteúdo do arquivo válido (contém occurrence_id, category, severity)
   - [ ] Audit entry criado com occurrence_id propagado corretamente

4. **Documentação:**
   - Adicionar docstring explicando o fluxo
   - Comentar cada passo do grafo

---

### Tarefa 4: Documentar Estratégia de Testes (Output)

**Deliverable:**
- `docs/qa/test-strategy.md`

**Conteúdo:**

```markdown
# Test Strategy — Card 06

## Objetivo

Validar os comportamentos críticos do agente de classificação de incidentes:
- Validação de entrada e detecção de adversariais
- Extração e parsing de JSON do LLM
- Roteamento condicional correto
- Integração HTTP com API de moradores
- Fluxo completo E2E

## Cenários Prioritários

### P0 — Crítico (deve passar antes do merge)
1. Teste E2E entrada válida → arquivo salvo
2. Teste de injection bloqueada → resposta genérica
3. Teste de múltiplos incidentes → roteado para rejeição antecipada
4. Teste de estado propagado corretamente (occurrence_id, llm_start_time, llm_end_time)

### P1 — Importante (deve estar implementado)
1. Testes unitários para `_extract_json`
2. Testes para lookup_resident com timeout
3. Testes de roteamento `_route_after_validate` e `_route_after_classify`

### P2 — Futuro (próximas iterações)
1. Testes de performance (latência do LLM)
2. Testes de carga (múltiplas entradas paralelas)
3. Mutation testing para validação de lógica condicional

## Cobertura Esperada

| Módulo | Cobertura | Status |
|--------|-----------|--------|
| `validate_input` | 90%+ | Teste 2.1 |
| `classify_incident` | 85%+ | Teste 2.2 |
| `prefetch_resident` | 80%+ | Teste 2.4 |
| Roteamento | 100% | Teste 2.3 |
| E2E | Happy path + 2 edge cases | Teste 3 |

## Justificativa de Priorização

Card 05 identificou 4 bugs críticos em propagação de estado. P0 valida que:
1. O estado persiste corretamente entre nós
2. Entrada adversarial é rejeitada de forma segura
3. Fluxo inteiro funciona end-to-end

Sem esses testes, bugs como "occurrence_id não propagado" voltarão em futuras mudanças.
```

---

## 🎯 Checklist de Aceitação

### Consolidação
- [ ] `docs/qa/code-review-summary.md` criado
- [ ] Matriz de achados preenchida
- [ ] Padrões recorrentes identificados
- [ ] Review para aprofundamento escolhido e justificado

### Testes Unitários
- [ ] `tests/test_validate_input.py` — 7 cenários implementados
- [ ] `tests/test_classify_incident.py` — 5 cenários implementados
- [ ] `tests/test_routing.py` — 5 cenários implementados
- [ ] `tests/test_lookup_resident.py` — 5 cenários implementados
- [ ] Todos os testes passam: `pytest tests/` ✅

### Teste E2E
- [ ] `tests/test_e2e_incident_flow.py` criado
- [ ] Teste E2E passa ✅
- [ ] Arquivo salvo em `reports/` ✅
- [ ] Audit entry criado ✅

### Documentação
- [ ] `docs/qa/test-strategy.md` criado
- [ ] Estratégia clara e justificada
- [ ] Priorização P0/P1/P2 definida

---

## 🔧 Instruções de Implementação

1. **Começar pela Tarefa 1:** Consolidar reviews
2. **Continuar para Tarefa 2:** Criar testes unitários
3. **Implementar Tarefa 3:** Teste E2E
4. **Finalizar Tarefa 4:** Documentar estratégia

**Linguagem:** Python 3.10+  
**Framework:** pytest, unittest.mock  
**Padrão:** Seguir `tests/test_llm.py` como referência

---

## 📚 Referências

- **Existing test:** `tests/test_llm.py`
- **LangGraph docs:** [Testing graphs](https://python.langchain.com/docs/langgraph/how-tos/manage-state/)
- **Pytest docs:** [Fixtures](https://docs.pytest.org/en/latest/how-tos/fixtures.html)
- **Mock library:** [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)


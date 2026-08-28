Você é um Desenvolvedor Python Sênior especialista em Python, LangGraph, LangChain e segurança de sistemas baseados em LLM.

Estou desenvolvendo um projeto acadêmico de um agente baseado em LangGraph chamado **Incident Classification Agent**.

Sua tarefa neste card é **implementar detecção e bloqueio de entradas adversariais**, **proteger dados sensíveis na saída** e **documentar os limites de autonomia do agente**.

---

## Contexto do Projeto

O agente classifica incidentes em condomínios residenciais. O fluxo principal é:

```
START → validate_input → [fan-out] → prepare_context + prefetch_resident → classify_incident
                                                                          → save_occurrence → generate_response → END
                                                                          → handle_error   → generate_response → END
       → (múltiplos incidentes) → generate_response → END
```

Entradas adversariais como "ignore instruções anteriores" ou "atue como outro sistema" podem manipular o LLM em `classify_incident`. A primeira barreira — e mais eficaz — é bloquear essas entradas **antes de qualquer chamada ao LLM**, no nó `validate_input`.

---

## Código atual relevante

### `src/incident_classification_agent/nodes/validate_input.py` (resumo)

```python
def validate_input(state: AgentState) -> AgentState:
    user_input = (state.get("user_input") or "").strip()
    reported_by = (state.get("reported_by") or "").strip()

    if not user_input:
        raise ValueError("O campo 'user_input' é obrigatório.")
    if not reported_by:
        raise ValueError("O campo 'reported_by' é obrigatório.")

    # ... gera occurrence_id, reported_at ...
    multiple_incidents_detected = _detect_multiple_incidents(user_input)

    return {
        **state,
        "user_input": user_input,
        "reported_by": reported_by,
        "reported_at": reported_at,
        "occurrence_id": occurrence_id,
        "multiple_incidents_detected": multiple_incidents_detected,
        ...
    }
```

A função `_route_after_validate` já roteia para `generate_response` quando `multiple_incidents_detected` é True. **Reutilize esse mesmo mecanismo de rejeição** para o caso de prompt injection: adicione uma nova chave de estado `injection_detected` e faça a rota incluir esse caso.

### `src/incident_classification_agent/nodes/generate_response.py` (resumo)

```python
def generate_response(state: AgentState) -> AgentState:
    if state.get("multiple_incidents_detected"):
        response = _format_multiple_incidents(state)
    elif state.get("classification_error"):
        response = _format_error(state)
    else:
        response = _format_success(state)
    ...
```

A resposta de sucesso atual inclui `resident_info` parcialmente:

```python
resident = state.get("resident_info")
if resident and resident.get("found"):
    lines.append(f"🔍 Morador cadastrado: {resident.get('resident_name', 'N/A')}")
    visitors = resident.get("authorized_visitors") or []
    if visitors:
        lines.append(f"   Visitantes autorizados: {', '.join(visitors)}")
```

O campo `phone` presente em `resident_info` **não está sendo incluído na saída** — mas isso deve ser verificado e garantido explicitamente.

### `src/incident_classification_agent/state.py` (resumo)

```python
class AgentState(TypedDict):
    user_input: str
    reported_by: str
    reported_at: str
    occurrence_id: str | None
    category: Category | None
    severity: Severity | None
    involved_people: list[str]
    apartment: str | None
    building: str | None
    summary: str | None
    conversation_history: list[str]
    output_file: str | None
    escalated_file: str | None
    classification_error: str | None
    resident_info: dict | None
    multiple_incidents_detected: bool | None
    session_history: list[dict]
```

---

## Tarefa 1 — Adicionar `injection_detected` ao estado

Em `src/incident_classification_agent/state.py`, adicione a chave:

```python
injection_detected: bool | None
```

Adicione também sua docstring no bloco `Attributes` da classe, explicando que indica detecção de tentativa de prompt injection.

---

## Tarefa 2 — Implementar detecção de prompt injection em `validate_input`

Em `src/incident_classification_agent/nodes/validate_input.py`:

### 2a. Criar a função `_detect_injection(user_input: str) -> bool`

Use **somente regex determinístico** — sem chamada ao LLM. Isso garante que entradas adversariais são bloqueadas _antes_ de qualquer invocação de modelo.

A função deve detectar os seguintes padrões adversariais (case-insensitive, com variações de espaços/pontuação):

| Categoria | Exemplos de padrão |
|---|---|
| Reescrita de papel | "você agora é", "you are now", "act as", "atue como", "finja que é", "pretend you are" |
| Descarte de instruções | "ignore instruções anteriores", "ignore previous instructions", "esqueça tudo", "forget everything", "ignore as regras", "ignore your instructions" |
| Escape de contexto | "novo prompt", "new prompt", "system prompt", "ignore o sistema", "ignore the system" |
| Injeção direta | "### instrução", "### instruction", "[instrução]", "[system]", "<|im_start|>", "<|system|>" |

A função deve:
- Compilar os padrões uma única vez (variável de módulo `_INJECTION_PATTERNS`) para performance.
- Retornar `True` se qualquer padrão for encontrado em `user_input`.
- Logar em nível `WARNING` o padrão detectado (sem incluir o conteúdo do input do usuário no log — evite vazar o texto adversarial).

### 2b. Invocar `_detect_injection` em `validate_input`

Antes da chamada a `_detect_multiple_incidents`, adicione:

```python
injection_detected = _detect_injection(user_input)
```

Se `injection_detected` for True:
- Logar em nível `WARNING`: `"Prompt injection detected — occurrence_id: %s"` (sem incluir o input).
- **Não chamar `_detect_multiple_incidents`** (evita enviar texto adversarial ao LLM).
- Retornar o estado com `injection_detected=True` e `multiple_incidents_detected=False`.

### 2c. Atualizar `_route_after_validate`

Adicionar condição para `injection_detected` antes da verificação de múltiplos incidentes:

```python
def _route_after_validate(state: AgentState) -> str:
    if state.get("injection_detected"):
        logger.warning("Injection detected — short-circuiting to generate_response.")
        return "generate_response"
    if state.get("multiple_incidents_detected"):
        ...
```

---

## Tarefa 3 — Formatar resposta de rejeição por injection em `generate_response`

Em `src/incident_classification_agent/nodes/generate_response.py`:

### 3a. Criar `_format_injection_detected(state: AgentState) -> str`

A mensagem deve:
- Informar que a entrada não pôde ser processada.
- **Não mencionar** o motivo técnico ("prompt injection", "padrão adversarial", "instrução detectada").
- **Não expor** nenhum detalhe interno do sistema (nomes de nós, chaves de estado, regex).
- Ser breve e orientar o usuário a reformular o relato.

Exemplo de tom adequado:

```
⚠️ Não foi possível processar o relato informado.

Por favor, descreva o incidente de forma objetiva,
incluindo o que aconteceu, onde e quem estava envolvido.

🆔 ID gerado: <occurrence_id>
```

### 3b. Adicionar o caso `injection_detected` em `generate_response`

```python
def generate_response(state: AgentState) -> AgentState:
    if state.get("injection_detected"):
        response = _format_injection_detected(state)
    elif state.get("multiple_incidents_detected"):
        ...
```

---

## Tarefa 4 — Auditar e proteger `phone` na saída

### 4a. Verificar `generate_response`

Confirme que `_format_success` **não inclui** o campo `phone` de `resident_info` em nenhuma linha da resposta. O código atual não o inclui, mas a auditoria deve ser explícita:

- Adicione um comentário inline em `_format_success` na seção de `resident_info` indicando que `phone` é intencionalmente omitido:

```python
# phone intencionalmente omitido — dado sensível, não exposto ao usuário
```

### 4b. Verificar `lookup_resident`

A tool `lookup_resident` retorna `phone` no dict quando o morador é encontrado. Esse dado é necessário internamente (pode ser usado em escalonamentos futuros), então **não remova** o campo da tool. A proteção é na camada de saída (`generate_response`), não na tool.

Adicione um comentário na docstring de `lookup_resident`, no campo `phone`:

```
- ``phone``: telefone de contato — disponível no estado interno, não exposto na resposta ao usuário
```

---

## Tarefa 5 — Documentar limites de autonomia

Crie o arquivo `docs/evidences/autonomy-limits.md` com o seguinte conteúdo:

### Estrutura do arquivo

```markdown
# Limites de Autonomia — Incident Classification Agent

## O que o agente pode fazer

| Ação | Condição |
|---|---|
| Classificar um incidente (categoria + severidade) | Sempre que `user_input` e `reported_by` forem válidos |
| Consultar dados de moradores (`lookup_resident`) | Durante a classificação, quando `apartment` for identificado no relato |
| Salvar a ocorrência em arquivo JSON (`save_occurrence`) | Após classificação bem-sucedida |
| Escalar a ocorrência para `reports/escalated/` | Quando `severity=HIGH` |
| Recuperar histórico da sessão (`get_session_history`) | Durante a preparação de contexto |

## O que o agente não pode fazer

| Ação bloqueada | Motivo |
|---|---|
| Executar qualquer outra tool além das listadas acima | Apenas `lookup_resident`, `save_occurrence` e `get_session_history` estão vinculadas ao LLM |
| Processar mais de um incidente por chamada | Bloqueado por `_detect_multiple_incidents` em `validate_input` |
| Receber instruções via `user_input` para alterar seu comportamento | Bloqueado por `_detect_injection` antes de qualquer chamada ao LLM |
| Expor o telefone do morador ao usuário | `phone` é omitido em `_format_success` de `generate_response` |
| Modificar o grafo, o estado ou as configurações em tempo de execução | Não há tool ou mecanismo que permita isso |
| Acessar sistemas externos além da API de moradores | Nenhuma outra integração HTTP existe no código |

## Mecanismo de contenção

O agente opera em um grafo com arestas fixas compiladas em tempo de inicialização.
Não há mecanismo de auto-modificação, geração de código executável ou chamada
a ferramentas não declaradas em `bind_tools`. O escopo de ação é determinístico
e auditável pelo grafo definido em `src/incident_classification_agent/graph.py`.
```

---

## Tarefa 6 — Documentar cenário de prompt injection

Crie `docs/evidences/prompt-injection.md` com a seguinte estrutura:

```markdown
# Evidência — Detecção de Prompt Injection

## Cenário

**Entrada adversarial submetida:**
(cole aqui um exemplo real de entrada com padrão adversarial)

**Comportamento esperado:**
- `injection_detected=True` no estado
- Fluxo encerrado em `validate_input → generate_response` sem chamar o LLM
- Mensagem de rejeição genérica exibida ao usuário
- Nenhum detalhe interno exposto na saída

**Comportamento observado:**
(cole aqui o output real do agente após a implementação)

## Logs relevantes

(cole aqui os logs com nível WARNING gerados pelo `validate_input`)

## Conclusão

(preencher após execução real)
```

> **Instrução:** Após implementar, execute o agente com `examples/input_injection.json` e cole o output e os logs neste arquivo.

---

## Restrições

- A detecção de injection deve usar **apenas regex determinístico** — nunca chamar o LLM com o input suspeito.
- A mensagem de rejeição **não deve mencionar** termos como "injection", "adversarial", "regex", "padrão detectado" ou qualquer detalhe de implementação.
- Não remova o campo `phone` da tool `lookup_resident` nem do `AgentState` — a proteção é apenas na saída ao usuário.
- Não altere o contrato de retorno de nenhuma tool existente.
- Não adicione novas dependências ao `pyproject.toml` — `re` já está disponível na stdlib.
- O fluxo de múltiplos incidentes e o fluxo de erro devem continuar funcionando sem alteração.

---

## Entrega

Ao final, apresente:

1. `src/incident_classification_agent/state.py` — campo `injection_detected` adicionado
2. `src/incident_classification_agent/nodes/validate_input.py` — `_detect_injection`, lógica de bloqueio e roteamento atualizados
3. `src/incident_classification_agent/nodes/generate_response.py` — `_format_injection_detected` adicionado e chamado
4. `src/incident_classification_agent/tools/lookup_resident.py` — comentário sobre `phone` adicionado à docstring
5. `docs/evidences/autonomy-limits.md` — limites de autonomia documentados
6. `docs/evidences/prompt-injection.md` — cenário documentado (estrutura + evidência real após execução)

Verifique que o agente continua funcionando corretamente para entradas legítimas após as mudanças:

```bash
# Terminal 1 — API de moradores
uv run uvicorn api.main:app --reload

# Terminal 2 — Agente com entrada legítima
uv run python -m incident_classification_agent.main examples/input.json

# Terminal 2 — Agente com entrada adversarial (deve rejeitar sem chamar o LLM)
uv run python -m incident_classification_agent.main examples/input_injection.json
```

O arquivo `examples/input_injection.json` contém uma entrada adversarial com os padrões "ignore instruções anteriores" e "você agora é". O fluxo legítimo deve produzir o mesmo resultado de antes. O fluxo adversarial deve terminar com a mensagem de rejeição genérica e log `WARNING` em `validate_input`, sem nenhuma chamada ao LLM.

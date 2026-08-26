Você é um Desenvolvedor Python Sênior especialista em Python, FastAPI, LangGraph, LangChain e modelos de linguagem locais.

Estou desenvolvendo um projeto acadêmico de um agente baseado em LangGraph chamado **Incident Classification Agent**.

Sua tarefa neste card é **evoluir a tool `lookup_resident`** para consumir uma API HTTP local em vez de ler o arquivo `residents.json` diretamente do disco, e **criar o servidor FastAPI** que servirá esses dados.

---

## Contexto do Projeto

O agente classifica incidentes em condomínios residenciais. Durante a classificação, o nó `classify_incident` invoca a tool `lookup_resident` para consultar dados de moradores. Atualmente essa tool lê o arquivo `data/residents.json` diretamente do disco.

### Tool atual (`src/incident_classification_agent/tools/lookup_resident.py`)

```python
@tool
def lookup_resident(apartment: str, building: str | None = None) -> dict:
    """Consulta os dados cadastrais do morador de um apartamento específico."""
    residents = _load_residents()  # lê residents.json do disco

    for resident in residents:
        apt_match = resident.get("apartment", "").strip().lower() == apartment.strip().lower()
        building_match = (
            building is None
            or resident.get("building", "").strip().lower() == building.strip().lower()
        )
        if apt_match and building_match:
            return {
                "found": True,
                "apartment": resident.get("apartment"),
                "building": resident.get("building"),
                "resident_name": resident.get("resident_name"),
                "authorized_visitors": resident.get("authorized_visitors", []),
                "vehicles": resident.get("vehicles", []),
                "phone": resident.get("phone"),
            }

    return {"found": False, "apartment": apartment, "building": building}
```

### Contrato de retorno que deve ser mantido

```python
# Quando encontrado:
{
    "found": True,
    "apartment": str,
    "building": str | None,
    "resident_name": str,
    "authorized_visitors": list[str],
    "vehicles": list[str],
    "phone": str,
}

# Quando não encontrado:
{"found": False, "apartment": str, "building": str | None}

# Quando a API estiver indisponível:
{"found": False, "error": "API indisponível"}
```

### Dados disponíveis (`data/residents.json`)

O arquivo contém uma lista de moradores com os campos: `apartment`, `building`, `resident_name`, `authorized_visitors`, `vehicles`, `phone`. O servidor FastAPI deve ler esse arquivo como fonte de dados.

### Variáveis de ambiente relevantes

- `RESIDENTS_API_URL` — URL base da API. Default: `http://localhost:8000`
- Carregadas via `python-dotenv`. O módulo `llm.py` serve de referência para o padrão de carregamento.

---

## Tarefa 1 — Criar o servidor FastAPI

Crie o arquivo `api/main.py` com um servidor FastAPI que exponha o endpoint:

```
GET /residents?apartment={apartment}&building={building}
```

Requisitos:
- `apartment` é obrigatório. Retornar 422 se ausente ou vazio.
- `building` é opcional.
- Retornar o morador encontrado com os mesmos campos do `residents.json` quando localizado.
- Retornar `{"found": false}` quando não localizado.
- Validar os parâmetros de entrada com Pydantic (use `Query` do FastAPI).
- Ler os dados de `data/residents.json`. Use caminho relativo à raiz do projeto, não hardcoded.
- Incluir tratamento de erro para falha na leitura do arquivo (retornar 500 com mensagem clara).
- Adicionar docstring na função do endpoint descrevendo o contrato.

---

## Tarefa 2 — Evoluir a tool `lookup_resident`

Substitua a leitura direta do arquivo pela chamada HTTP ao servidor FastAPI.

Requisitos:
- Usar `httpx` para a chamada HTTP (já disponível no ambiente via dependências transitivas; se não estiver, adicionar ao `pyproject.toml`).
- Implementar timeout de 5 segundos na chamada HTTP.
- Tratar os seguintes erros sem lançar exceção:
  - `httpx.ConnectError` — API indisponível
  - `httpx.TimeoutException` — timeout na chamada
  - Qualquer outro erro de rede ou HTTP inesperado
  - Em todos os casos retornar `{"found": False, "error": "API indisponível"}`
- Ler `RESIDENTS_API_URL` do ambiente com fallback para `http://localhost:8000`.
- Manter o contrato de retorno inalterado (estrutura dos dicts de sucesso e não-encontrado).
- Manter as mesmas docstrings e assinatura da função — apenas a implementação interna muda.
- Logar a URL consultada e o resultado (encontrado / não encontrado / erro) em nível INFO.

---

## Tarefa 3 — Atualizar as dependências

No `pyproject.toml`:
- Adicionar `fastapi` e `uvicorn` como dependências principais.
- Adicionar `httpx` como dependência principal se não estiver presente.

No `.env.example`:
- Adicionar a variável `RESIDENTS_API_URL` com valor padrão `http://localhost:8000` e um comentário explicativo.

---

## Tarefa 4 — Documentar

### README.md

Na seção "Como Executar o Projeto", adicione uma etapa antes da execução do agente instruindo como iniciar o servidor FastAPI:

```bash
uv run uvicorn api.main:app --reload
```

Mencione que o servidor deve estar em execução antes de rodar o agente.

### `docs/evidences/api-integration.md`

Crie esse arquivo documentando:
- Descrição do endpoint
- Exemplos de request e response (morador encontrado, não encontrado, parâmetro inválido)
- Como testar manualmente (curl ou browser)
- Evidência de execução real: rode o servidor, faça uma chamada e cole o output

---

## Restrições

- Não modifique nenhum outro arquivo de código além dos listados nas tarefas acima.
- Não altere o contrato de retorno da tool — o restante do agente não deve precisar de nenhuma alteração.
- Não adicione autenticação ou lógica de negócio ao servidor FastAPI além do necessário para servir os dados.
- A falha na API deve ser silenciosa para o agente: o fluxo continua com `found=False`, sem exceção propagada.

---

## Entrega

Ao final, apresente:

1. `api/main.py` — servidor FastAPI completo e funcional
2. `src/incident_classification_agent/tools/lookup_resident.py` — tool evoluída
3. `pyproject.toml` — dependências atualizadas
4. `.env.example` — variável `RESIDENTS_API_URL` adicionada
5. `README.md` — instrução de execução do servidor adicionada
6. `docs/evidences/api-integration.md` — endpoint documentado com evidência real

Verifique que o agente continua funcionando corretamente após a mudança executando:

```bash
uv run uvicorn api.main:app --reload
# em outro terminal:
uv run python -m incident_classification_agent.main examples/input.json
```

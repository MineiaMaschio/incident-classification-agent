# 🌐 Card 02 — API de moradores com FastAPI

> **Branch:** `feature/tool-integration`

## 🎯 Objetivo

Evoluir a tool `lookup_resident` para consumir uma API HTTP local em vez de ler o arquivo `residents.json` diretamente do disco, atendendo ao requisito de integração por API/backend com validação de entradas e tratamento de erros.

---

## 📌 Escopo

### Servidor FastAPI

* [x] Criar `api/main.py` com um servidor FastAPI expondo o endpoint `GET /residents` com parâmetros `apartment` e `building`
* [x] Validar os parâmetros de entrada com Pydantic (ex: `apartment` obrigatório, não pode ser vazio)
* [x] Retornar o morador encontrado ou `{"found": false}` quando não localizado
* [x] Retornar erros HTTP adequados para entradas inválidas (422 para parâmetros ausentes/malformados)
* [x] Adicionar `uvicorn` e `fastapi` ao `pyproject.toml`
* [x] Adicionar `RESIDENTS_API_URL` ao `.env.example` com valor padrão `http://localhost:8000`

### Evolução da tool `lookup_resident`

* [x] Substituir a leitura direta do arquivo por chamada HTTP `GET /residents?apartment=...&building=...`
* [x] Implementar tratamento de erros de conexão: se a API estiver indisponível, retornar `{"found": false, "error": "API indisponível"}` sem lançar exceção
* [x] Implementar timeout na chamada HTTP (ex: 5 segundos)
* [x] Manter o contrato de retorno da tool inalterado para não quebrar o restante do agente

### Documentação

* [x] Atualizar as instruções de execução no README: mencionar que o servidor FastAPI deve ser iniciado antes do agente
* [x] Documentar o endpoint em `docs/evidences/api-integration.md` com exemplo de request e response

### Code review com IA

* [x] Realizar code review da implementação do servidor FastAPI e da tool evoluída com apoio de IA
* [x] Registrar achados (problemas identificados, melhorias aplicadas ou descartadas) em `docs/qa/review-card02.md`

---

## 🏁 Resultado Esperado

* [x] Servidor FastAPI funcional servindo os dados de moradores via HTTP
* [x] Tool `lookup_resident` consumindo a API com tratamento de erro de conexão e timeout
* [x] Agente continua funcionando corretamente com a nova integração
* [x] Integração documentada
* [x] Review registrado em `docs/qa/review-card02.md`

---

## 📎 Referências

* `src/incident_classification_agent/tools/lookup_resident.py`
* `data/residents.json`
* `.env.example`
* `docs/evidences/` (criada no Card 01)
* `docs/qa/` (criada no Card 01)

---

## 📝 Detalhamento da execução

### Decisões de implementação

- **httpx** escolhido para a chamada HTTP por já estar disponível no ecossistema LangChain/httpx e oferecer API síncrona limpa com suporte a timeout e tratamento de exceções tipadas.
- **Falha silenciosa na tool**: erros de conexão, timeout e HTTP inesperado retornam `{"found": False, "error": "API indisponível"}` sem propagar exceção, garantindo que o fluxo do agente continue mesmo com a API fora do ar.
- **Busca case-insensitive** aplicada tanto na API quanto na tool para tolerância a variações de entrada do LLM.
- **Caminho do `residents.json`** resolvido via `Path(__file__).parent.parent` no servidor, relativo à raiz do projeto, sem hardcode de caminho absoluto.
- **`RESIDENTS_API_URL`** lida no carregamento do módulo com fallback para `http://localhost:8000`, consistente com o padrão `os.getenv` + `load_dotenv` já usado em `llm.py`.

### Arquivos criados/modificados

| Arquivo | Ação |
|---|---|
| `api/__init__.py` | Criado — marca o pacote `api` |
| `api/main.py` | Criado — servidor FastAPI com `GET /residents` |
| `src/incident_classification_agent/tools/lookup_resident.py` | Modificado — substituída leitura de arquivo por chamada HTTP |
| `pyproject.toml` | Modificado — adicionados `fastapi>=0.115.0`, `httpx>=0.27.0`, `uvicorn>=0.30.0` |
| `.env.example` | Modificado — adicionado `RESIDENTS_API_URL=http://localhost:8000` |
| `README.md` | Modificado — passo 5 inserido com instrução de iniciar o servidor FastAPI |
| `docs/evidences/api-integration.md` | Criado — endpoint documentado com exemplos e evidência de execução real |
| `docs/qa/review-card02.md` | Criado — achados documentados, aplicações e descartes justificados |

### Evidências de execução

Execução real do agente com o servidor FastAPI ativo em `2026-08-25`:

```
[INFO] tools.lookup_resident — Consultando API de moradores: http://localhost:8000/residents params={'apartment': '101', 'building': 'A'}
[INFO] httpx — HTTP Request: GET http://localhost:8000/residents?apartment=101&building=A "HTTP/1.1 200 OK"
[INFO] tools.lookup_resident — Morador encontrado: apartamento=101 bloco=A → Carlos Mendes
```

Resultado: `category=ACCESS`, `severity=LOW`, arquivo salvo em `reports/20260826T000842Z_f74a5994-78e4-4586-93c1-6deb8f75a180.json`.

### Achados do code review com IA

Dois achados levantados pelo agente `senai-pr-reviewer` (Gemini 3.6 Flash) no PR #21.

**Achado 1 — Testes do endpoint:** descartado neste card. O Card 06 tem item explícito para cobrir testes da tool e do endpoint da API.

**Achado 2 — Validação tipada da resposta HTTP:** aplicado. Criado modelo Pydantic `_ResidentResponse` na tool para validar a resposta antes de consumi-la. Detalhes em `docs/qa/review-card02.md`.

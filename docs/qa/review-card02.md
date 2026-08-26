# Code Review — Card 02: API de moradores com FastAPI

**PR:** [feat: replace lookup_resident file read with FastAPI HTTP integration](https://github.com/MineiaMaschio/incident-classification-agent/pull/21)
**Review publicado:** https://github.com/MineiaMaschio/incident-classification-agent/pull/21#pullrequestreview-5025613718
**Ferramenta:** senai-pr-reviewer (LangGraph + Gemini 3.6 Flash)
**Modelo:** `gemini-3.6-flash`
**Arquivos analisados:** 9
**Achados gerados:** 2 | **Publicados:** 2 | **Descartados:** 0
**Data:** 2026-08-25

---

## Resumo geral

A integração HTTP da tool de moradores com FastAPI e httpx foi implementada adequadamente, mantendo o contrato de retorno e o tratamento gracioso de falhas de rede. Dois achados foram levantados: ausência de testes para o endpoint e ausência de validação tipada da resposta HTTP.

---

## Achados

### Achado 1 — Falta de testes para o endpoint `GET /residents`

| Campo | Valor |
|---|---|
| **Arquivo** | `api/main.py` |
| **Linhas** | 52–53 |
| **Categoria** | teste |
| **Severidade** | major |
| **Confiança** | 95% |

**Problema:** A introdução do endpoint `GET /residents` exige testes cobrindo o caminho feliz (200 OK), parâmetro ausente (422) e falha de leitura de arquivo (500).

**Decisão:** **Descartado neste card — coberto pelo Card 06.**
O Card 06 tem item explícito para testes da tool `lookup_resident` (resposta da API, timeout e indisponibilidade) e do endpoint da API. Criar os testes aqui fragmentaria o esforço de QA que será consolidado naquele card.

---

### Achado 2 — Ausência de validação/tipagem no retorno da chamada HTTP

| Campo | Valor |
|---|---|
| **Arquivo** | `src/incident_classification_agent/tools/lookup_resident.py` |
| **Linha** | 41 |
| **Categoria** | manutenibilidade |
| **Severidade** | minor |
| **Confiança** | 90% |

**Problema:** A resposta HTTP era consumida como `dict` sem validação de schema. Se o contrato da API mudar, o erro só seria percebido em tempo de execução como `KeyError` ou `None` silencioso.

**Decisão:** **Aplicado neste card.**

Foi criado o modelo Pydantic `_ResidentResponse` na tool para validar a resposta antes de utilizá-la:

```python
class _ResidentResponse(BaseModel):
    found: bool
    apartment: str | None = None
    building: str | None = None
    resident_name: str | None = None
    authorized_visitors: list[str] = []
    vehicles: list[str] = []
    phone: str | None = None
```

A deserialização passa a ser `_ResidentResponse.model_validate(response.json())`. Um `ValidationError` é tratado com `logger.error` e retorna `{"found": False, "error": "API indisponível"}`, mantendo o comportamento de falha silenciosa para o agente.

Aproveitando a passagem, foram corrigidos também três problemas identificados em review interno anterior:

| Problema | Correção |
|---|---|
| Caminho absoluto exposto no `detail` das HTTPExceptions 500 em `api/main.py` | `detail` alterado para `"Erro interno ao carregar dados."` |
| `httpx.HTTPStatusError` caindo no `except Exception` genérico | Branch `except httpx.HTTPStatusError` adicionado antes do genérico |
| Falhas de rede logadas em `INFO` | `ConnectError`/`TimeoutException` → `logger.warning`; `Exception` genérico → `logger.error` |

---

## Pontos positivos observados

- Tratamento gracioso de falhas de rede com `httpx` e `try/except` estruturado
- Contrato de retorno mantido fielmente em relação à versão anterior com leitura de arquivo
- Integração com FastAPI bem estruturada com validação de parâmetros via `Query`

---

## Arquivos modificados neste review

| Arquivo | Alteração |
|---|---|
| `src/incident_classification_agent/tools/lookup_resident.py` | Adicionado `_ResidentResponse` (Pydantic), `except httpx.HTTPStatusError`, `except ValidationError`; níveis de log corrigidos |
| `api/main.py` | `detail` das HTTPExceptions 500 generalizado para não expor path interno |

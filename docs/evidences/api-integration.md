# API Integration — Residents API

## Descrição

O servidor **Residents API** é uma aplicação FastAPI criada no card 02 para desacoplar a consulta de moradores do sistema de arquivos local. A tool `lookup_resident` do agente deixou de ler o `residents.json` diretamente e passou a consumir este servidor via HTTP.

---

## Endpoint

### `GET /residents`

Consulta os dados cadastrais do morador de um apartamento específico.

| Parâmetro   | Tipo     | Obrigatório | Descrição                                      |
|-------------|----------|-------------|------------------------------------------------|
| `apartment` | `string` | ✅ sim      | Número do apartamento (ex: `101`, `402`)       |
| `building`  | `string` | ❌ não      | Bloco ou torre (ex: `A`, `B`). Default: `null` |

A busca é **case-insensitive** em ambos os parâmetros.

---

## Exemplos de Request e Response

### 1. Morador encontrado

**Request:**
```
GET http://localhost:8000/residents?apartment=101&building=A
```

**Response — HTTP 200:**
```json
{
  "found": true,
  "apartment": "101",
  "building": "A",
  "resident_name": "Carlos Mendes",
  "authorized_visitors": ["Ana Mendes", "Roberto Mendes"],
  "vehicles": ["ABC-1234", "DEF-5678"],
  "phone": "(11) 9****-1234"
}
```

---

### 2. Morador não encontrado

**Request:**
```
GET http://localhost:8000/residents?apartment=999&building=Z
```

**Response — HTTP 200:**
```json
{
  "found": false
}
```

---

### 3. Parâmetro obrigatório ausente (422)

**Request:**
```
GET http://localhost:8000/residents
```

**Response — HTTP 422:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "apartment"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## Como Testar Manualmente

### Via browser

Acesse diretamente no navegador após iniciar o servidor:

```
http://localhost:8000/residents?apartment=101&building=A
http://localhost:8000/residents?apartment=501&building=B
http://localhost:8000/residents?apartment=999
```

A documentação interativa Swagger também está disponível em:

```
http://localhost:8000/docs
```

### Via curl

```bash
# Morador encontrado
curl "http://localhost:8000/residents?apartment=101&building=A"

# Morador não encontrado
curl "http://localhost:8000/residents?apartment=999&building=Z"

# Sem apartment — 422
curl "http://localhost:8000/residents"
```

### Via PowerShell

```powershell
# Morador encontrado
Invoke-WebRequest -Uri "http://localhost:8000/residents?apartment=101&building=A" -UseBasicParsing | Select-Object -ExpandProperty Content

# Morador não encontrado
Invoke-WebRequest -Uri "http://localhost:8000/residents?apartment=999&building=Z" -UseBasicParsing | Select-Object -ExpandProperty Content
```

---

## Iniciar o servidor

```bash
uv run uvicorn api.main:app --reload
```

O servidor sobe em `http://localhost:8000` por padrão. A URL base é configurável via variável de ambiente `RESIDENTS_API_URL` no `.env`.

---

## Evidência de Execução Real

Servidor iniciado em `2026-08-25` com o comando:

```
.venv\Scripts\uvicorn.exe api.main:app --port 8000
```

### Output do servidor (uvicorn)

```
INFO:     Started server process [28940]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:50576 - "GET /residents?apartment=101&building=A HTTP/1.1" 200 OK
INFO:     127.0.0.1:60243 - "GET /residents?apartment=999&building=Z HTTP/1.1" 200 OK
```

### Chamada 1 — morador encontrado (`apartment=101`, `building=A`)

```
GET http://localhost:8000/residents?apartment=101&building=A
→ HTTP 200
```

```json
{"found":true,"apartment":"101","building":"A","resident_name":"Carlos Mendes","authorized_visitors":["Ana Mendes","Roberto Mendes"],"vehicles":["ABC-1234","DEF-5678"],"phone":"(11) 9****-1234"}
```

### Chamada 2 — morador não encontrado (`apartment=999`, `building=Z`)

```
GET http://localhost:8000/residents?apartment=999&building=Z
→ HTTP 200
```

```json
{"found":false}
```

### Chamada 3 — parâmetro ausente (sem `apartment`)

```
GET http://localhost:8000/residents
→ HTTP 422
```

```json
{"detail":[{"type":"missing","loc":["query","apartment"],"msg":"Field required","input":null}]}
```

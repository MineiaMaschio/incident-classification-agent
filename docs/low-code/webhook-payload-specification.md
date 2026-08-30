# 📋 Especificação do Payload Webhook para n8n

## 🎯 Objetivo

Este documento descreve a estrutura do JSON que será enviado ao n8n quando um incidente com severidade **HIGH** for classificado pela LLM.

---

## 📦 Estrutura do Payload

O webhook será disparado automaticamente após a classificação e persistência da ocorrência com `severity: HIGH`. O payload contém todos os dados de contexto e classificação:

```json
{
  "occurrence_id": "string (uuid)",
  "reported_by": "string",
  "reported_at": "string (ISO 8601)",
  "user_input": "string (relatório original do porteiro/segurança)",
  "category": "string (ACCESS | PACKAGE | NOISE | MAINTENANCE | SECURITY | OTHER)",
  "severity": "string (LOW | MEDIUM | HIGH)",
  "involved_people": [
    "string",
    "..."
  ],
  "apartment": "string (número do apartamento)",
  "building": "string (bloco/torre, ex: A, B, C)",
  "summary": "string (resumo da classificação em português/inglês)",
  "resident_info": "object | null",
  "saved_at": "string (ISO 8601, timestamp de quando foi salvo)",
  "escalated": true,
  "escalated_at": "string (ISO 8601, timestamp de escalonamento)"
}
```

---

## 🔍 Descrição dos Campos

| Campo | Tipo | Exemplo | Descrição |
|-------|------|---------|-----------|
| `occurrence_id` | UUID | `1ad5d695-3ef1-4bf2-9fae-140629ea6da1` | Identificador único da ocorrência |
| `reported_by` | string | `João Silva` | Nome de quem reportou (porteiro/segurança) |
| `reported_at` | ISO 8601 | `2026-07-14T09:15:00Z` | Data/hora do relato original |
| `user_input` | string | `Indivíduo suspeito tentando forçar a fechadura do apartamento 302` | Descrição original do incidente |
| `category` | enum | `SECURITY` | Categoria classificada pela LLM |
| `severity` | enum | `HIGH` | Severidade classificada (sempre HIGH para webhooks) |
| `involved_people` | array | `["João Silva", "Invasor desconhecido"]` | Pessoas envolvidas no incidente |
| `apartment` | string | `302` | Número do apartamento afetado |
| `building` | string | `A` | Bloco/torre do condomínio |
| `summary` | string | `Tentativa de invasão em apartamento — pessoa desconhecida tentando forçar fechadura` | Resumo da análise |
| `resident_info` | object/null | Ver seção abaixo | Dados do morador (se disponível) |
| `saved_at` | ISO 8601 | `2026-08-28T22:35:15Z` | Quando foi persistido |
| `escalated` | boolean | `true` | Flag indicando escalonamento |
| `escalated_at` | ISO 8601 | `2026-08-28T22:35:15Z` | Quando foi escalonado |

---

## 👤 Campo `resident_info` (quando disponível)

Quando a aplicação consegue localizar os dados do morador via API, o campo conterá:

```json
{
  "found": true,
  "apartment": "302",
  "building": "A",
  "resident_name": "Maria Silva",
  "authorized_visitors": ["João Silva"],
  "vehicles": ["ABC-1234", "DEF-5678"],
  "phone": "(11) 9****-1234"
}
```

**Quando não disponível:** `resident_info` será `null`.

---

## 📝 Exemplos de Payload Completo

### Exemplo 1: Tentativa de Invasão (SECURITY - HIGH)

```json
{
  "occurrence_id": "3c7a9f2e-1b4d-4c8e-9a3b-5f6d7e8c9d0a",
  "reported_by": "Carlos Santos",
  "reported_at": "2026-08-29T14:30:00Z",
  "user_input": "Indivíduo suspeito tentando forçar a fechadura do apartamento 302, bloco A, por volta de 14h30",
  "category": "SECURITY",
  "severity": "HIGH",
  "involved_people": [
    "Indivíduo desconhecido",
    "Carlos Santos"
  ],
  "apartment": "302",
  "building": "A",
  "summary": "Tentativa de invasão detectada — indivíduo não-autorizado tentou forçar acesso ao apartamento 302",
  "resident_info": {
    "found": true,
    "apartment": "302",
    "building": "A",
    "resident_name": "Maria Silva",
    "authorized_visitors": ["João Silva", "Ana Costa"],
    "vehicles": ["ABC-1234"],
    "phone": "(11) 98765-4321"
  },
  "saved_at": "2026-08-29T14:31:22Z",
  "escalated": true,
  "escalated_at": "2026-08-29T14:31:22Z"
}
```

### Exemplo 2: Roubo de Pacote (PACKAGE - HIGH)

```json
{
  "occurrence_id": "8f5e2a9b-3c1d-4e7f-9b2c-6d8a9e0f1a2b",
  "reported_by": "Porteiro Silva",
  "reported_at": "2026-08-29T10:15:00Z",
  "user_input": "Morador do 405 relata roubo de pacote que estava na portaria — pacote foi deixado às 09h00 e desapareceu",
  "category": "PACKAGE",
  "severity": "HIGH",
  "involved_people": [
    "Morador 405",
    "Possível ladrão desconhecido"
  ],
  "apartment": "405",
  "building": "B",
  "summary": "Roubo de pacote em portaria — pacote desapareceu em menos de 2 horas",
  "resident_info": {
    "found": true,
    "apartment": "405",
    "building": "B",
    "resident_name": "Roberto Alves",
    "authorized_visitors": [],
    "vehicles": ["XYZ-9876"],
    "phone": "(11) 99999-8888"
  },
  "saved_at": "2026-08-29T10:16:45Z",
  "escalated": true,
  "escalated_at": "2026-08-29T10:16:45Z"
}
```

---

## 🔌 Configuração no n8n

### Gatilho Webhook (Webhook Trigger Node)

- **URL**: `http://localhost:3000/webhook/incidents` (exemplo — configurável)
- **Método**: `POST`
- **Dados esperados**: JSON conforme estrutura acima
- **Autenticação**: Opcional (pode ser adicionada via header `X-API-Key`)

### Referência na Aplicação

A URL será configurada via variável de ambiente:
```env
WEBHOOK_URL=http://localhost:3000/webhook/incidents
```

---

## ⚠️ Notas Importantes

1. **Apenas HIGH**: O webhook é disparado **exclusivamente** para ocorrências com `severity == "HIGH"`

2. **Não-bloqueante**: Se o webhook falhar, a ocorrência ainda será salva localmente. O fluxo principal não é afetado.

3. **Timestamp ISO 8601**: Todos os timestamps seguem o padrão ISO 8601 com timezone UTC (`Z`)

4. **Encoding UTF-8**: O JSON é serializado com `ensure_ascii=False` para suportar caracteres acentuados em português

5. **Retry Logic**: Recomenda-se implementar retry no n8n com exponential backoff em caso de falha

---

## 🧪 Teste Local

Para testar localmente sem configurar a aplicação completa:

```bash
# 1. Crie um webhook local usando ngrok ou similar
ngrok http 8080

# 2. Configure WEBHOOK_URL com a URL pública
export WEBHOOK_URL=https://<ngrok-url>/webhook/incidents

# 3. Simule um payload POST
curl -X POST http://localhost:8080/webhook/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "occurrence_id": "test-123",
    "reported_by": "João",
    "reported_at": "2026-08-29T14:30:00Z",
    "user_input": "Teste de incidente",
    "category": "SECURITY",
    "severity": "HIGH",
    "involved_people": ["Teste"],
    "apartment": "101",
    "building": "A",
    "summary": "Incidente de teste",
    "resident_info": null,
    "saved_at": "2026-08-29T14:31:22Z",
    "escalated": true,
    "escalated_at": "2026-08-29T14:31:22Z"
  }'
```

---

## 📚 Referências

- [n8n Webhook Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base-webhook/)
- [ISO 8601 DateTime Format](https://en.wikipedia.org/wiki/ISO_8601)
- [JSON Payload Best Practices](https://restfulapi.net/http-request-body/)

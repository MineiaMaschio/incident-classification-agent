# 🎯 PROMPT: Card 09 - Low-Code Integration com n8n

> **Status**: Pronto para Implementação  
> **Fluxo n8n**: ✅ Criado em `http://localhost:5678/webhook/incidents`  
> **Payload Spec**: ✅ Documentado em `docs/low-code/webhook-payload-specification.md`

---

## 📋 Contexto da Tarefa

A aplicação classifica incidentes usando LLM. Quando um incidente é classificado com `severity == HIGH`, deve dispara um webhook para um fluxo n8n pré-configurado que produz uma saída observável (ex: alerta, e-mail, Slack, etc.).

**O que já está pronto**:
- ✅ Fluxo n8n criado e testado
- ✅ Especificação do payload documentada
- ❌ Integração da aplicação (a implementar)

---

## 🎯 Objetivo da Tarefa

Implementar a chamada de webhook na aplicação para notificar o n8n quando um incidente HIGH é classificado, de forma **não-bloqueante** e **segura**.

---

## 📝 Especificação da Implementação

### 1. Modificar `.env.example`

**Adicione a variável de ambiente**:

```env
# URL do webhook n8n para notificação de incidentes HIGH.
# Formato: http://localhost:5678/webhook/<path>
# A chamada será feita apenas quando severity == HIGH.
# Falhas no webhook NÃO interrompem o fluxo principal.
WEBHOOK_URL=http://localhost:5678/webhook/incidents
```

---

### 2. Modificar `src/incident_classification_agent/nodes/save_occurrence.py`

**Adicionar a seguinte funcionalidade**:

#### A) Importações necessárias

Adicione no topo do arquivo:

```python
import os
import asyncio
from typing import Optional
import httpx
```

#### B) Função auxiliar para disparo do webhook

Adicione uma função **não-bloqueante** para chamar o webhook:

```python
async def _send_webhook_async(webhook_url: str, payload: dict, occurrence_id: str) -> bool:
    """Envia payload via webhook para o n8n de forma não-bloqueante.
    
    Args:
        webhook_url: URL do webhook (ex: http://localhost:5678/webhook/incidents)
        payload: Dicionário com os dados da ocorrência
        occurrence_id: ID da ocorrência para logging
    
    Returns:
        True se sucesso, False se falha (não lança exceção)
    """
    prefix = f"[occurrence_id={occurrence_id}]"
    
    if not webhook_url or not webhook_url.strip():
        logger.debug(f"{prefix} WEBHOOK_URL not configured, skipping webhook call")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code in (200, 201, 202, 204):
                logger.info(
                    f"{prefix} Webhook sent successfully "
                    f"[status={response.status_code}]"
                )
                return True
            else:
                logger.warning(
                    f"{prefix} Webhook failed [status={response.status_code}] "
                    f"[response={response.text[:200]}]"
                )
                return False
                
    except asyncio.TimeoutError:
        logger.warning(f"{prefix} Webhook timeout after 10s")
        return False
    except httpx.RequestError as exc:
        logger.warning(f"{prefix} Webhook error: {exc}")
        return False
    except Exception as exc:
        logger.error(f"{prefix} Unexpected error sending webhook: {exc}", exc_info=True)
        return False


def _dispatch_webhook(webhook_url: str, payload: dict, occurrence_id: str) -> None:
    """Dispara o webhook de forma não-bloqueante usando threading.
    
    Args:
        webhook_url: URL do webhook
        payload: Dicionário com os dados
        occurrence_id: ID da ocorrência
    """
    try:
        asyncio.run(_send_webhook_async(webhook_url, payload, occurrence_id))
    except Exception as exc:
        logger.error(f"[occurrence_id={occurrence_id}] Failed to dispatch webhook: {exc}")
```

#### C) Modificar a função `save_occurrence()`

Na função `save_occurrence()`, após salvar o arquivo escalonado (linha ~89 onde está `if severity_value == "HIGH"`), **adicione a chamada do webhook**:

**Encontre este bloco** (aproximadamente linha 80-95):

```python
    severity_value = severity.value if severity is not None else None
    if severity_value == "HIGH":
        ESCALATED_DIR.mkdir(parents=True, exist_ok=True)
        escalated_path = ESCALATED_DIR / filename
        escalated_payload = {
            **payload,
            "escalated": True,
            "escalated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        escalated_path.write_text(
            json.dumps(escalated_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.warning(f"{prefix} HIGH severity — occurrence escalated to {escalated_path}")
        result["escalated_file"] = str(escalated_path)
```

**E modifique para**:

```python
    severity_value = severity.value if severity is not None else None
    if severity_value == "HIGH":
        ESCALATED_DIR.mkdir(parents=True, exist_ok=True)
        escalated_path = ESCALATED_DIR / filename
        escalated_payload = {
            **payload,
            "escalated": True,
            "escalated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        escalated_path.write_text(
            json.dumps(escalated_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.warning(f"{prefix} HIGH severity — occurrence escalated to {escalated_path}")
        result["escalated_file"] = str(escalated_path)
        
        # Dispara webhook para n8n de forma não-bloqueante
        webhook_url = os.getenv("WEBHOOK_URL", "").strip()
        if webhook_url:
            logger.info(f"{prefix} Dispatching webhook to {webhook_url}")
            _dispatch_webhook(webhook_url, escalated_payload, occurrence_id)
        else:
            logger.debug(f"{prefix} WEBHOOK_URL not configured")
```

---

### 3. Payload Enviado para o n8n

O payload enviado será idêntico ao salvo em disco, com campos adicionais:

```json
{
  "occurrence_id": "uuid",
  "reported_by": "string",
  "reported_at": "ISO 8601",
  "user_input": "string",
  "category": "string",
  "severity": "HIGH",
  "involved_people": ["string"],
  "apartment": "string",
  "building": "string",
  "summary": "string",
  "resident_info": "object | null",
  "saved_at": "ISO 8601",
  "escalated": true,
  "escalated_at": "ISO 8601"
}
```

---

## ✅ Requisitos de Implementação

### Comportamento

- [x] Webhook é disparado **apenas** quando `severity == "HIGH"`
- [x] Falha no webhook **NÃO** interrompe o fluxo principal
- [x] Timeout configurado em **10 segundos**
- [x] Logging detalhado de sucesso/falha
- [x] `WEBHOOK_URL` é **obrigatória** apenas se webhook for usar; se vazia, é ignorada
- [x] Payload é enviado como `application/json` com UTF-8

### Segurança

- [x] URL validada antes de enviar (não vazia)
- [x] Timeout para prevenir hang indefinido
- [x] Tratamento de exceções (sem crash)
- [x] Headers `Content-Type: application/json`

### Performance

- [x] Chamada **não-bloqueante** (async/await ou threading)
- [x] Classificação continua mesmo se webhook falhar
- [x] Logging eficiente sem impacto de performance

---

## 🧪 Testes a Executar

### Teste 1: Webhook Configurado e n8n Rodando

```bash
# 1. Configure em .env
WEBHOOK_URL=http://localhost:5678/webhook/incidents

# 2. Certifique-se que n8n está rodando
# 3. Envie um incidente HIGH
# 4. Verifique logs da aplicação
# 5. Confirme que n8n recebeu o payload
```

**Resultado esperado**:
- Log: `Webhook sent successfully [status=200]`
- n8n: Webhook disparado com payload correto

### Teste 2: Webhook Não Configurado

```bash
# 1. WEBHOOK_URL vazio ou não configurado em .env
# 2. Envie um incidente HIGH
# 3. Verifique que classificação continua normalmente
```

**Resultado esperado**:
- Incidente salvo normalmente
- Log: `WEBHOOK_URL not configured`
- Nenhum erro

### Teste 3: n8n Indisponível

```bash
# 1. Pare o n8n
# 2. Configure WEBHOOK_URL em .env
# 3. Envie um incidente HIGH
# 4. Verifique que classificação continua
```

**Resultado esperado**:
- Incidente salvo normalmente
- Log: `Webhook error: [ConnectionError message]`
- Nenhum crash, fluxo continua

### Teste 4: Timeout

```bash
# 1. Configure um webhook que demora > 10s para responder
# 2. Envie um incidente HIGH
# 3. Verifique que não trava
```

**Resultado esperado**:
- Log: `Webhook timeout after 10s`
- Classificação continua

---

## 📊 Logging Esperado

```
[occurrence_id=abc-123] Iniciando save_occurrence...
[occurrence_id=abc-123] Occurrence saved to /path/to/reports/timestamp_abc-123.json
[occurrence_id=abc-123] HIGH severity — occurrence escalated to /path/to/reports/escalated/timestamp_abc-123.json
[occurrence_id=abc-123] Dispatching webhook to http://localhost:5678/webhook/incidents
[occurrence_id=abc-123] Webhook sent successfully [status=200]
[occurrence_id=abc-123] save_occurrence concluído.
```

---

## 📚 Referências

- Spec do payload: `docs/low-code/webhook-payload-specification.md`
- Nó atual: `src/incident_classification_agent/nodes/save_occurrence.py`
- `.env.example`: Configuração de variáveis
- [httpx async docs](https://www.python-httpx.org/async/)
- [asyncio docs](https://docs.python.org/3/library/asyncio.html)

---

## 🔄 Pós-Implementação

Após implementar, você deve:

1. ✅ Testar todos os 4 cenários acima
2. ✅ Verificar logs para mensagens de erro
3. ✅ Fazer code review
4. ✅ Documentar no `docs/qa/review-card09.md`
5. ✅ Atualizar `docs/low-code/README.md` com instruções
6. ✅ Criar arquivo de evidência (screenshot do n8n recebendo webhook)

---

## 📋 Checklist Final

- [ ] `.env.example` atualizado com `WEBHOOK_URL`
- [ ] Importações adicionadas ao `save_occurrence.py`
- [ ] Funções `_send_webhook_async()` e `_dispatch_webhook()` implementadas
- [ ] Chamada do webhook adicionada ao bloco `if severity_value == "HIGH"`
- [ ] Todos os 4 testes passando
- [ ] Logs verificados e corretos
- [ ] Code review concluído e documentado
- [ ] Documentação atualizada em `docs/low-code/README.md`
- [ ] Screenshots de evidência salvas
- [ ] PR pronto para merge

---

**Pronto para começar!** 🚀

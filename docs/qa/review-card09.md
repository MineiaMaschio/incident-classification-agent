# Code Review — Card 09: Low-Code Integration com n8n

**Data**: 2026-08-29  
**Ferramenta**: senai-pr-reviewer (LangGraph + Gemini 3.6 Flash)  
**Status**: ✅ COMPLETO (Correções Aplicadas)

---

## 📋 Resumo

A revisão automatizada identificou 2 problemas na implementação do webhook em `save_occurrence.py`. Ambos foram **CORRIGIDOS** e testados.

---

## 🔍 Achados & Correções

### 1. ❌→✅ `asyncio.run()` Bloqueante (CORRIGIDO)

**Problema Identificado:**
- Arquivo: `src/incident_classification_agent/nodes/save_occurrence.py`
- Linha: ~81 (função `_dispatch_webhook`)
- Categoria: Performance
- Severidade: Major
- Confiança: 95%

**Detalhes:**
```python
# ❌ ANTES (bloqueante)
def _dispatch_webhook(webhook_url, payload, occurrence_id):
    asyncio.run(_send_webhook_async(webhook_url, payload, occurrence_id))
```

A função `asyncio.run()` bloqueia a thread atual até que a requisição HTTP seja finalizada ou atinja timeout. Além disso, se o código estiver em um loop asyncio ativo (FastAPI, LangGraph assíncrono), lançará:
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Solução Aplicada:**
```python
# ✅ DEPOIS (não-bloqueante com threading)
import threading

def _dispatch_webhook(webhook_url, payload, occurrence_id):
    """Dispara o webhook de forma não-bloqueante usando threading.
    
    Executa a chamada assíncrona em uma thread separada (daemon) para não bloquear
    a thread principal. Isso previne RuntimeError caso o código esteja dentro de
    um loop asyncio em execução (FastAPI, LangGraph assíncrono, etc.).
    """
    def run_async():
        try:
            asyncio.run(_send_webhook_async(webhook_url, payload, occurrence_id))
        except Exception as exc:
            logger.error(f"[occurrence_id={occurrence_id}] Failed to dispatch webhook: {exc}")
    
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()
```

**Benefícios:**
- ✅ Não bloqueia a thread principal
- ✅ Funciona dentro de loops asyncio ativos
- ✅ Thread daemon garante limpeza automática
- ✅ Mantém logging de erros

---

### 2. ❌→✅ Timeout Não Capturado (CORRIGIDO)

**Problema Identificado:**
- Arquivo: `src/incident_classification_agent/nodes/save_occurrence.py`
- Linhas: ~61-63 (função `_send_webhook_async`)
- Categoria: Bug
- Severidade: Minor
- Confiança: 90%

**Detalhes:**
```python
# ❌ ANTES (captura incorreta)
except asyncio.TimeoutError:
    logger.warning(f"{prefix} Webhook timeout after 10s")
    return False
```

O cliente HTTP `httpx.AsyncClient` lança exceções derivadas de `httpx.TimeoutException` (como `httpx.ReadTimeout`, `httpx.ConnectTimeout`), **não** `asyncio.TimeoutError`. O bloco de captura nunca era alcançado em caso de timeout do httpx.

**Solução Aplicada:**
```python
# ✅ DEPOIS (captura correta)
except httpx.TimeoutException:
    logger.warning(f"{prefix} Webhook timeout after 10s")
    return False
except httpx.RequestError as exc:
    logger.warning(f"{prefix} Webhook error: {exc}")
    return False
```

**Benefícios:**
- ✅ Captura corretamente timeouts do httpx
- ✅ Trata todas as exceções de requisição HTTP
- ✅ Logging apropriado de cada erro

---

## 📊 Impacto das Correções

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Bloqueante?** | ❌ Sim (bloqueia por até 10s) | ✅ Não (thread separada) |
| **Funciona em AsyncIO?** | ❌ Não (RuntimeError) | ✅ Sim |
| **Captura Timeout?** | ❌ Não (exceção incorreta) | ✅ Sim (httpx.TimeoutException) |
| **Logging de Erro** | ✅ Sim | ✅ Sim (melhorado) |

---

## ✅ Verificação Final

- [x] Correção 1 aplicada e testada
- [x] Correção 2 aplicada e testada
- [x] Testes unitários passando
- [x] Testes E2E passando
- [x] Linting (ruff) passando
- [x] Logging funcional
- [x] Documentação atualizada

---

## 📝 Decisões de Design

1. **Threading vs Async Task Scheduling**
   - Escolhido: Threading (simples, seguro, sem overhead)
   - Alternativa: `asyncio.create_task()` (requer loop ativo)
   - Por quê: Funciona sempre, mesmo sem loop asyncio

2. **Timeout Exception Class**
   - Escolhido: `httpx.TimeoutException` (base class)
   - Alternativa: Capturar `httpx.ReadTimeout` e `httpx.ConnectTimeout` separadamente
   - Por quê: Mais DRY, cobre todos os casos de timeout

3. **Daemon Thread**
   - Escolhido: `daemon=True`
   - Por quê: Não bloqueia shutdown da aplicação

---

## 🔗 Referências

- [Python asyncio.run() docs](https://docs.python.org/3/library/asyncio.html#asyncio.run)
- [httpx exceptions](https://www.python-httpx.org/exceptions/)
- [Threading in Python](https://docs.python.org/3/library/threading.html)
- [OWASP Webhook Security](https://owasp.org/www-community/attacks/OWASP_Webhook_Failure_Points)

---

**Status Final**: ✅ APROVADO - Pronto para Deploy

# 🎯 Card 09: Low-Code Integration com n8n

**Status**: Em Desenvolvimento  
**Branch**: `feature/low-code`  
**Data de Criação**: 2026-08-29

---

## 📌 Objetivo

Criar uma integração low-code/no-code com n8n que receba notificação da aplicação quando um incidente **HIGH** for classificado e produza uma saída observável (alerta, registro ou notificação).

---

## 📋 Escopo

### 1️⃣ Ponto de Saída na Aplicação

- [x] Adicionar chamada de webhook no nó `save_occurrence` quando `severity == HIGH`
- [x] Enviar payload para URL configurada via variável de ambiente `WEBHOOK_URL`
- [x] Tornar a chamada opcional e não-bloqueante (falha não interrompe fluxo)
- [x] Adicionar `WEBHOOK_URL` ao `.env.example`

### 2️⃣ Fluxo n8n

- [x] Criar fluxo com gatilho webhook
- [x] Integrar com a aplicação recebendo payload de ocorrência HIGH
- [x] Produzir saída observável (sugestões: e-mail, Slack, Google Sheets, Notion)

### 3️⃣ Documentação

- [x] Documentar reprodução do fluxo em `docs/low-code/README.md`
- [x] Salvar export do fluxo n8n (JSON) em `docs/low-code/`
- [x] Incluir screenshot do fluxo executando

### 4️⃣ Code Review com IA

- [ ] Realizar code review da alteração em `save_occurrence`
- [ ] Registrar achados em `docs/qa/review-card09.md`

---

## 🏁 Resultado Esperado

✅ Ocorrências HIGH disparam webhook para o n8n  
✅ Fluxo n8n produz saída observável  
✅ Fluxo documentado e reproduzível  
✅ Export e evidências salvos em `docs/low-code/`  
✅ Review registrado em `docs/qa/review-card09.md`

---

## 📦 Especificação do Payload

O webhook enviará o seguinte JSON quando `severity == HIGH`:

```json
{
  "occurrence_id": "uuid",
  "reported_by": "string",
  "reported_at": "ISO 8601",
  "user_input": "string",
  "category": "SECURITY | ACCESS | PACKAGE | MAINTENANCE | NOISE | OTHER",
  "severity": "HIGH",
  "involved_people": ["string"],
  "apartment": "string",
  "building": "string",
  "summary": "string",
  "resident_info": {
    "found": boolean,
    "apartment": "string",
    "building": "string",
    "resident_name": "string",
    "authorized_visitors": ["string"],
    "vehicles": ["string"],
    "phone": "string"
  },
  "saved_at": "ISO 8601",
  "escalated": true,
  "escalated_at": "ISO 8601"
}
```

**Detalhes completos**: Veja `docs/low-code/webhook-payload-specification.md`

---

## 📎 Arquivos de Referência

- `src/incident_classification_agent/nodes/save_occurrence.py` — Nó onde será adicionado webhook
- `.env.example` — Onde adicionar `WEBHOOK_URL`
- `docs/low-code/webhook-payload-specification.md` — Especificação do payload ✅ **PRONTO**
- `docs/low-code/README.md` — Documentação do fluxo (a criar)
- `docs/qa/review-card09.md` — Code review (a criar)
- [n8n.io](https://n8n.io) — Plataforma low-code

---

## 🔄 Fluxo de Trabalho

1. **Criação do Fluxo n8n** (manual no n8n)
   - Configurar webhook trigger
   - Integrar com serviço de saída (e-mail, Slack, sheets, etc.)
   - Testar e exportar

2. **Implementação da Chamada de Webhook**
   - Modificar `save_occurrence.py` para chamar webhook quando `severity == HIGH`
   - Implementar retry com timeout
   - Adicionar logging e tratamento de erro

3. **Testes End-to-End**
   - Simular incidente HIGH
   - Verificar se webhook é disparado
   - Validar saída no n8n

4. **Code Review**
   - Revisar segurança, performance e tratamento de erro
   - Documentar decisões

5. **Documentação Final**
   - Screenshot do fluxo n8n
   - Guia de reprodução
   - Export do fluxo

---

## 📝 Notas Importantes

- ⚠️ **Não-bloqueante**: Falha no webhook NÃO deve parar a classificação
- 🔐 **Segurança**: Validar URL do webhook antes de enviar
- 🕐 **Timeout**: Configurar timeout razoável (ex: 5-10 segundos)
- 📊 **Logging**: Log de success/failure para troubleshooting
- 🔄 **Retry**: Considerar retry com exponential backoff no n8n

---

## ✅ Checklist de Implementação

- [x] Especificação do payload criada ✅ PRONTO
- [x] Fluxo n8n criado e testado
- [x] Webhook adicionado a `save_occurrence.py`
- [x] `WEBHOOK_URL` adicionado a `.env.example`
- [x] Testes end-to-end passando
- [x] Documentação completa
- [x] Screenshots anexados
- [x] Export do n8n salvo
- [ ] Code review concluído
- [ ] PR pronto para review

---

## 📚 Links Úteis

- [n8n Webhook Trigger Docs](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base-webhook/)
- [n8n Email Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base-emailsend/)
- [n8n Slack Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base-slack/)
- [Webhook Best Practices](https://docs.microsoft.com/en-us/azure/architecture/best-practices/app-configuration)
- [ISO 8601 DateTime](https://en.wikipedia.org/wiki/ISO_8601)

---

**Próximas Ações**:
1. Criar fluxo no n8n com gatilho webhook
2. Testar com payload de exemplo
3. Exportar fluxo como JSON
4. Implementar chamada de webhook na aplicação
5. Executar testes e-2-e

# 🔌 Low-Code Integration: n8n Webhook Setup

This guide provides step-by-step instructions to integrate the incident classification agent with n8n via webhooks.

---

## 📋 Overview

When the incident classification agent detects a HIGH severity incident, it automatically sends a webhook to n8n. This allows you to:

- 📧 Send email alerts to stakeholders
- 💬 Post notifications to Slack, Teams, Discord
- 📝 Create tickets in Jira, Linear, or other issue trackers
- 🔔 Trigger custom workflows and integrations
- 📊 Log incidents to external databases

**Key Features**:
- ✅ Non-blocking: Webhook failures don't interrupt classification
- ✅ Configurable: Enable/disable via environment variable
- ✅ Reliable: Incidents always saved to disk, even if webhook fails
- ✅ Fast: 10-second timeout prevents hanging
- ✅ Detailed: Comprehensive incident data in payload

---

## 🚀 Quick Start

### 1. Configure n8n Webhook URL

Edit your `.env` file:

```bash
# .env
WEBHOOK_URL=http://localhost:5678/webhook/incidents
```

Or if n8n is running on a different host:

```bash
WEBHOOK_URL=http://n8n.example.com:5678/webhook/incidents
```

### 2. Start n8n

```bash
# Terminal 1: Start n8n (adjust command based on your setup)
npm run n8n  # or docker-compose up n8n
```

Verify n8n is accessible:
```bash
curl http://localhost:5678/
```

### 3. Create Webhook Trigger in n8n

1. Open n8n UI: `http://localhost:5678`
2. Create a new workflow
3. Add a **Webhook** trigger node:
   - **Method**: POST
   - **Path**: `/webhook/incidents`
   - **Response code**: 200
   - **Response data**: `$("binary_data")`

4. Add your desired action nodes (email, Slack, etc.)
5. **Save and activate** the workflow

### 4. Start the Incident Classification Agent

```bash
# Terminal 2
cd incident-classification-agent
python -m incident_classification_agent.main
```

### 5. Test with a HIGH Severity Incident

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d @examples/input_05_security_break_in.json
```

Check n8n workflow executions to see the webhook trigger fire!

---

## 📦 Webhook Payload Format

The webhook sends the following JSON payload:

```json
{
  "occurrence_id": "3c7a9f2e-1b4d-4c8e-9a3b-5f6d7e8c9d0a",
  "reported_by": "Carlos Santos",
  "reported_at": "2026-08-29T14:30:00Z",
  "user_input": "Indivíduo suspeito tentando forçar a fechadura do apartamento 302...",
  "category": "SECURITY",
  "severity": "HIGH",
  "involved_people": ["Indivíduo desconhecido", "Carlos Santos"],
  "apartment": "302",
  "building": "A",
  "summary": "Tentativa de invasão detectada...",
  "resident_info": {
    "found": true,
    "apartment": "302",
    "building": "A",
    "resident_name": "Maria Silva",
    "authorized_visitors": ["João Silva"],
    "vehicles": ["ABC-1234"],
    "phone": "(11) 98765-4321"
  },
  "saved_at": "2026-08-29T14:31:22Z",
  "escalated": true,
  "escalated_at": "2026-08-29T14:31:22Z"
}
```

See [Payload Specification](./webhook-payload-specification.md) for details.

---

## 📝 Example n8n Workflows

### Example 1: Email Alert

```
Webhook Trigger
    ↓
[Email Node]
    - To: {{ $json.resident_info.phone }} (or your admin email)
    - Subject: "🚨 HIGH Severity Incident: {{ $json.category }}"
    - Body: "{{ $json.summary }}"
    ↓
Response: Send 200 OK
```

### Example 2: Slack Notification

```
Webhook Trigger
    ↓
[Slack Node]
    - Channel: #security-alerts
    - Message: "🚨 {{ $json.category }} incident in {{ $json.apartment }}"
    - Details: "{{ $json.summary }}"
    - Mention: @channel (for critical)
    ↓
Response: Send 200 OK
```

### Example 3: Jira Ticket Creation

```
Webhook Trigger
    ↓
[Jira Node - Create Issue]
    - Project: SECURITY
    - Issue Type: Incident
    - Summary: "{{ $json.category }}: {{ $json.apartment }}"
    - Description: "{{ $json.summary }}"
    - Priority: Highest (for HIGH severity)
    ↓
Response: Send 200 OK
```

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Example | Required | Notes |
|----------|---------|----------|-------|
| `WEBHOOK_URL` | `http://localhost:5678/webhook/incidents` | No | If not set, webhooks are skipped silently |

### Webhook Behavior

- **Triggered on**: `severity == "HIGH"` only
- **HTTP Method**: POST
- **Content-Type**: `application/json; charset=utf-8`
- **Timeout**: 10 seconds
- **Retry**: No (implement in n8n if needed)
- **Blocking**: No (async, doesn't block classification)

---

## 🧪 Testing

### Test 1: Verify Webhook Configuration

```bash
# Check if WEBHOOK_URL is set
grep WEBHOOK_URL .env

# Test webhook endpoint with curl
curl -X POST http://localhost:5678/webhook/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "occurrence_id": "test-123",
    "reported_by": "Test User",
    "reported_at": "2026-08-29T14:30:00Z",
    "user_input": "Test incident",
    "category": "SECURITY",
    "severity": "HIGH",
    "involved_people": ["Test"],
    "apartment": "101",
    "building": "A",
    "summary": "Test incident summary",
    "resident_info": null,
    "saved_at": "2026-08-29T14:31:22Z",
    "escalated": true,
    "escalated_at": "2026-08-29T14:31:22Z"
  }'
```

### Test 2: End-to-End with Classification

```bash
# 1. Ensure n8n is running and webhook is active
# 2. Send a HIGH severity incident
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d @examples/input_05_security_break_in.json

# 3. Check application logs for webhook dispatch
tail -f logs/app.log | grep "Dispatching webhook"

# 4. Check n8n execution history
# Open: http://localhost:5678 → Workflow → Executions
```

### Test 3: Failure Scenarios

```bash
# Test with n8n down (to verify non-blocking)
# 1. Stop n8n
# 2. Send HIGH severity incident
# 3. Verify incident is still saved (check reports/ folder)
# 4. Check logs for error message

# Test with webhook timeout
# 1. Configure WEBHOOK_URL to a slow endpoint
# 2. Send HIGH severity incident
# 3. Verify timeout message in logs after 10s
# 4. Verify incident is still saved
```

---

## 📊 Monitoring & Logs

### Application Logs

**Success case**:
```
[occurrence_id=abc-123] Dispatching webhook to http://localhost:5678/webhook/incidents
[occurrence_id=abc-123] Webhook sent successfully [status=200]
```

**Webhook not configured**:
```
[occurrence_id=abc-123] WEBHOOK_URL not configured
```

**Connection error**:
```
[occurrence_id=abc-123] Webhook error: [Errno 111] Connection refused
```

**Timeout**:
```
[occurrence_id=abc-123] Webhook timeout after 10s
```

### n8n Logs

Check n8n execution history for detailed webhook reception logs:
1. Open n8n UI at `http://localhost:5678`
2. Navigate to your workflow
3. Click "Executions" tab
4. Review execution details and node output

---

## ⚠️ Troubleshooting

### Problem: Webhook not being triggered

**Solution**:
1. Verify incident has `severity: HIGH` (check logs)
2. Check `WEBHOOK_URL` is set in `.env`: `echo $WEBHOOK_URL`
3. Verify n8n is running: `curl http://localhost:5678/`
4. Check application logs: `tail -f logs/app.log | grep webhook`

### Problem: Webhook triggered but n8n not responding

**Solution**:
1. Verify webhook URL is correct: `WEBHOOK_URL=http://localhost:5678/webhook/incidents`
2. Verify webhook is active in n8n (blue "Listen" indicator)
3. Check n8n logs for errors
4. Test manually with curl (see Testing section)

### Problem: n8n receiving payload but workflow not triggering

**Solution**:
1. Verify webhook trigger node is properly configured
2. Check webhook path matches: `/webhook/incidents`
3. Check HTTP method is POST
4. Review webhook trigger node settings in n8n
5. Add a manual test trigger to verify workflow logic works

### Problem: Incident not saved to disk

**Solution**:
1. Check application logs for errors in `save_occurrence`
2. Verify `reports/` directory exists and is writable
3. Check disk space: `df -h`
4. Check file permissions on `reports/` folder

### Problem: Timeout errors in logs

**Solution**:
1. Verify n8n webhook is responsive: `time curl http://localhost:5678/webhook/incidents`
2. If webhook logic is slow, increase payload processing in n8n
3. Or configure a longer timeout (see below)

### Adjusting Timeout

To change the 10-second timeout:
1. Edit `src/incident_classification_agent/nodes/save_occurrence.py`
2. Find: `async with httpx.AsyncClient(timeout=10.0) as client:`
3. Change `10.0` to desired seconds (e.g., `30.0` for 30 seconds)
4. Restart application

---

## 🔒 Security Considerations

### Webhook Authentication

Currently webhooks are unauthenticated. For production, add authentication:

**Option 1: API Key Header**
1. Update `.env`:
   ```bash
   WEBHOOK_URL=http://localhost:5678/webhook/incidents
   WEBHOOK_API_KEY=your-secret-key
   ```

2. Update `save_occurrence.py`:
   ```python
   headers = {
       "Content-Type": "application/json",
       "X-API-Key": os.getenv("WEBHOOK_API_KEY", "")
   }
   ```

3. Configure n8n to validate header

**Option 2: Webhook Secret**
1. Use n8n's built-in webhook authentication
2. n8n generates a secret token
3. Add to `WEBHOOK_URL` query parameter

### Network Security

- 🔒 Use HTTPS in production: `WEBHOOK_URL=https://...`
- 🔑 Use API keys or authentication tokens
- 🛡️ Restrict webhook access via firewall rules
- ✅ Monitor webhook access logs

---

## 📚 Related Documentation

- [Webhook Payload Specification](./webhook-payload-specification.md)
- [Test Scenarios](../qa/test-scenarios-card09.md)
- [Implementation Review](../qa/review-card09.md)
- [n8n Official Documentation](https://docs.n8n.io/)

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: Review application logs for detailed error messages
2. **Check n8n**: Verify webhook is active and test manually
3. **Review specs**: See [Payload Specification](./webhook-payload-specification.md)
4. **See examples**: Check `examples/` folder for sample incidents
5. **Contact support**: Reference the test scenarios and logs when reporting

---

## ✅ Quick Checklist

- [ ] n8n is installed and running
- [ ] WEBHOOK_URL is configured in `.env`
- [ ] Webhook trigger is created in n8n
- [ ] Webhook is active (blue indicator)
- [ ] Workflow action nodes are configured
- [ ] Application is running
- [ ] Test incident sent and webhook triggered
- [ ] n8n workflow execution successful

---

**Last Updated**: August 29, 2026  
**Status**: ✅ Complete

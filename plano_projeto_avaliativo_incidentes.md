# Projeto Avaliativo M2.2 — Plano de Implementação

## Projeto base
**Incident Classification Agent**

Aproveitar o projeto já desenvolvido para classificação de incidentes em condomínios e evoluí-lo para atender aos requisitos do Projeto Avaliativo do Módulo 2.

## Objetivo desta segunda etapa

Manter o núcleo atual da aplicação e adicionar principalmente:

- segurança e governança;
- observabilidade e resiliência;
- QA com apoio de IA;
- DevOps inteligente;
- automação low-code/no-code;
- documentação e evidências.

---

# Checklist resumido

## 1. Aplicação e domínio

- [x] Manter e documentar o problema que a aplicação resolve.
  > `README.md` — seção "Descrição do Problema" e "Objetivo do Agente"
- [x] Descrever público, entradas, saídas, riscos e critérios de sucesso.
  > `README.md` — seções "Exemplo de Entrada", "Exemplo de Saída", "Limitações da Solução"
- [ ] Demonstrar pelo menos 2 cenários:
  - [x] cenário principal de classificação.
    > `docs/evidences/scenarios.md` — Cenário 1
  - [x] cenário de risco, falha, exceção ou comportamento anômalo.
    > `docs/evidences/scenarios.md` — Cenário 2
- [x] Garantir uma saída estruturada, como JSON ou modelo Pydantic.
  > `schemas.py` (`IncidentInput`), `state.py` (`AgentState`), arquivos JSON em `reports/`

## 2. LangGraph

- [x] Utilizar estado compartilhado e tipado.
  > `state.py` — `AgentState` como `TypedDict`
- [x] Organizar nodes com responsabilidades claras.
  > `nodes/` — 6 nós com responsabilidades únicas e bem documentadas
- [x] Utilizar edges explícitas.
  > `graph.py` — `add_edge` e `add_conditional_edges` explícitos
- [x] Demonstrar execução sequencial.
  > Fluxo principal: `validate_input → prepare_context → classify_incident → save_occurrence → generate_response`
- [x] Implementar ramificação condicional.
  > `_route_after_validate` e `_route_after_classify` em `graph.py`
- [ ] Implementar pelo menos uma paralelização simples.
  > **Pendente** — Card 03
- [x] Definir condição de parada e evitar loops indefinidos.
  > Loop agentic em `classify_incident` limitado a 5 iterações
- [x] Separar claramente decisões do LLM das regras determinísticas.
  > LLM decide classificação e tool calls; nós determinísticos validam, persistem e roteiam

## 3. Tool e integração

- [x] Manter ou evoluir uma tool funcional.
  > `lookup_resident`, `get_session_history`, `save_occurrence` — todas operacionais
- [ ] Integrar por API, serviço, backend, MCP ou webhook.
  > **Pendente** — Card 02: `lookup_resident` ainda lê `residents.json` local; evoluir para FastAPI HTTP
- [x] Validar payloads, parâmetros e schemas.
  > `schemas.py` valida entrada via Pydantic; tools validam tipos via type hints
- [x] Implementar tratamento de erros.
  > `handle_error`, retry no LLM (`with_retry`), fallback em `load_session` e `_load_residents`
- [x] Documentar a finalidade da tool no fluxo.
  > `README.md` — tabela "Ferramentas Utilizadas"; docstrings em cada tool

## 4. Memória e contexto

- [x] Implementar ou manter uma estratégia de memória/contexto.
  > `MemorySaver` (em processo) + `session.json` (persistência durável)
- [x] Utilizar state, checkpointer, persistência ou RAG.
  > `graph.py` — `MemorySaver` como checkpointer; `session.py` — persistência em disco
- [x] Demonstrar recuperação de informações relevantes de interações anteriores ou da execução.
  > `get_session_history` retorna ocorrências anteriores; `prepare_context` injeta histórico no prompt
- [x] Documentar como a memória é utilizada.
  > `README.md` — seção "Loop Agentic em classify_incident"; comentário em `build_graph()`

## 5. Segurança e governança

- [x] Manter credenciais fora do repositório.
  > `.gitignore` ignora `.env`; chaves carregadas via `python-dotenv`
- [x] Criar `.env.example`.
  > `.env.example` presente com `OLLAMA_MODEL`
- [x] Validar entradas antes de executar tools.
  > `validate_input` verifica campos obrigatórios; `IncidentInput` rejeita strings vazias
- [x] Definir limites de autonomia.
  > Loop agentic limitado a 5 iterações; agente apenas classifica, consulta e persiste
- [ ] Bloquear ou exigir aprovação humana para ações sensíveis, quando aplicável.
  > **Parcial** — escalonamento HIGH registrado em pasta dedicada; aprovação humana não implementada
- [ ] Criar um cenário de prompt injection ou entrada maliciosa.
  > **Pendente** — Card 04
- [ ] Demonstrar que regras da aplicação não podem ser sobrescritas.
  > **Pendente** — Card 04
- [ ] Demonstrar que ações não autorizadas são bloqueadas.
  > **Pendente** — Card 04
- [ ] Garantir que informações sensíveis não sejam expostas.
  > **Parcial** — campo `phone` é retornado pela tool mas não exibido na resposta final; revisão formal pendente (Card 04)

## 6. Observabilidade e resiliência

- [x] Implementar logs estruturados.
  > `logging` configurado em `main.py`; todos os nós e tools emitem logs com `logger`
- [ ] Implementar um segundo sinal: métrica, trace ou auditoria.
  > **Pendente** — Card 05: implementar `reports/audit.jsonl`
- [ ] Correlacionar os sinais por uma execução ou identificador.
  > **Parcial** — `occurrence_id` gerado em `validate_input` mas não presente em todos os logs
- [ ] Registrar decisões, erros e latência quando disponível.
  > **Parcial** — decisões e erros logados; latência não registrada
- [x] Implementar timeout, retry limitado ou fallback para integrações externas.
  > `.with_retry(stop_after_attempt=3)` no LLM; fallback em `load_session` e `_load_residents`
- [ ] Usar os dados para investigar pelo menos uma execução.
  > **Pendente** — Card 05 e Card 08

## 7. QA com IA

- [ ] Escolher uma alteração real do projeto.
  > **Pendente** — Card 06
- [ ] Fazer code review dessa alteração com apoio de IA.
  > **Pendente** — Cards 02–05 (cada um realiza seu review) e Card 06 (consolida)
- [ ] Registrar os problemas ou melhorias identificados.
  > **Pendente** — `docs/qa/`
- [ ] Gerar ou refinar testes automatizados com apoio de IA.
  > **Pendente** — Card 06
- [ ] Criar pelo menos um teste de integração, aceitação ou E2E.
  > **Pendente** — Card 06
- [ ] Escolher um cenário prioritário baseado em risco, impacto ou criticidade.
  > **Pendente** — Card 06
- [ ] Documentar a justificativa.
  > **Pendente** — `docs/qa/test-strategy.md`

## 8. DevOps inteligente

- [ ] Criar pipeline com lint, testes e build ou validação equivalente.
  > **Pendente** — Card 07: `.github/workflows/ci.yml`
- [ ] Utilizar IA para analisar logs de pelo menos 2 etapas.
  > **Pendente** — Card 08
- [ ] Detectar pelo menos uma anomalia.
  > **Pendente** — Card 08
- [ ] Explicar a possível causa da anomalia.
  > **Pendente** — Card 08
- [ ] Produzir uma estimativa simples de tendência ou risco de falha.
  > **Pendente** — Card 08
- [ ] Utilizar dados reais ou simulados e documentados.
  > **Pendente** — Card 08
- [ ] Guardar as evidências da análise.
  > **Pendente** — `docs/devops/`

## 9. Low-code / No-code

Sugestão: utilizar **n8n** como integração complementar.

- [ ] Criar um fluxo com gatilho.
  > **Pendente** — Card 09
- [ ] Integrar o fluxo com a aplicação ou um serviço dela.
  > **Pendente** — Card 09: webhook no `save_occurrence` para incidentes HIGH
- [ ] Produzir uma saída observável.
  > **Pendente** — Card 09
- [ ] Possíveis saídas: alerta, relatório, registro ou notificação.
  > **Pendente** — Card 09
- [ ] Manter a lógica principal dentro da aplicação.
  > **Pendente** — Card 09 (lógica permanece no agente; n8n apenas reage ao webhook)
- [ ] Documentar como reproduzir o fluxo.
  > **Pendente** — `docs/low-code/README.md`

### Possível ideia para o Incident Classification Agent

Quando um incidente for classificado com severidade alta, ou quando uma anomalia for detectada:

`Aplicação → Webhook/API → n8n → alerta/registro/notificação`

---

# Organização no GitHub

## Quadro Kanban

Criar as colunas:

- Backlog
- A Fazer
- Em Andamento
- Bloqueado
- Em Revisão
- Concluído

Os cards devem representar o desenvolvimento real.

### Sugestão de cards

- [x] Definir escopo e arquitetura
- [ ] Evoluir fluxo LangGraph
- [ ] Implementar/evoluir tool
- [x] Implementar memória e contexto
- [ ] Implementar segurança e prompt injection
- [ ] Implementar observabilidade
- [x] Implementar resiliência
- [ ] Realizar code review com IA
- [ ] Criar/refinar testes com IA
- [ ] Configurar pipeline CI
- [ ] Analisar logs e detectar anomalia
- [ ] Criar estimativa de risco de falha
- [ ] Integrar automação n8n
- [ ] Organizar documentação e evidências
- [ ] Gravar vídeo
- [ ] Preparar entrega

## Fluxo de branches

Utilizar:

`main ← develop ← feature/*`

Sugestão de branches:

- `feature/langgraph-agent` ✅ (base do projeto)
- `feature/tool-integration`
- `feature/memory` ✅ (base do projeto)
- `feature/security-governance`
- `feature/observability`
- `feature/qa-intelligent`
- `feature/devops-anomalies`
- `feature/low-code`
- `docs/readme-video`

---

# Estrutura de documentação

```text
/docs
  /prompts       ✅ criado (Card 01)
  /qa            ✅ criado (Card 01)
  /evidences     ✅ criado (Card 01)
  /observability ✅ criado (Card 01)
  /devops        ✅ criado (Card 01)
  /low-code      ✅ criado (Card 01)
```

## README.md deve incluir

- [x] Descrição do projeto.
- [x] Problema, público e objetivo.
- [x] Arquitetura e classificação da solução.
- [x] Diagrama do fluxo LangGraph.
- [x] Descrição da tool e integração.
- [x] Estratégia de memória/contexto.
- [ ] Segurança e limites de autonomia. *(Card 04)*
- [ ] Cenário de prompt injection. *(Card 04)*
- [x] Instruções de instalação e execução.
- [x] `.env.example`.
- [ ] Testes e QA com IA. *(Card 06)*
- [ ] Observabilidade. *(Card 05)*
- [ ] Pipeline e DevOps. *(Card 07)*
- [ ] Anomalia e risco de falha. *(Card 08)*
- [ ] Automação n8n. *(Card 09)*
- [x] Dois cenários de uso. *(Card 01 — `docs/evidences/scenarios.md`)*
- [ ] Refinamento realizado durante o desenvolvimento. *(Card 10)*
- [x] Limitações e melhorias futuras.
- [ ] Link do vídeo. *(Card 11)*

---

# Refinamento obrigatório

Documentar pelo menos um ciclo:

1. Problema observado.
2. Alteração realizada.
3. Justificativa da alteração.
4. Resultado obtido.
5. Evidência.

> **Pendente** — será registrado ao longo dos cards de implementação (Cards 02–09) e consolidado no Card 10.

---

# Vídeo de demonstração

Duração recomendada: até 10 minutos.
Limite máximo: 12 minutos.

## Sugestão de roteiro

- **0:00–1:00** — Problema, objetivo e classificação da solução.
- **1:00–2:00** — Arquitetura e integrações.
- **2:00–4:00** — Dois cenários de uso.
- **4:00–5:00** — Segurança e bloqueio de entrada adversarial.
- **5:00–6:00** — QA e testes com apoio de IA.
- **6:00–8:00** — Pipeline, logs, anomalia e risco de falha.
- **8:00–9:00** — Automação low-code com n8n.
- **9:00–10:00** — Limitações e melhorias futuras.

---

# Ordem sugerida de implementação

Para aproveitar o projeto atual sem refazer o que já existe:

1. [x] Revisar o projeto atual e identificar o que já atende aos requisitos. *(Card 01 — concluído)*
2. [ ] Ajustar o fluxo LangGraph para garantir ramificação, paralelização e parada. *(Card 03)*
3. [ ] Consolidar tool e memória — evoluir `lookup_resident` para API HTTP. *(Card 02)*
4. [ ] Implementar segurança e cenário de prompt injection. *(Card 04)*
5. [ ] Adicionar logs estruturados e métrica/trace/auditoria. *(Card 05)*
6. [ ] Implementar tratamento de falhas complementar. *(Card 05)*
7. [ ] Criar/refinar testes e fazer code review com IA. *(Card 06)*
8. [ ] Configurar pipeline CI. *(Card 07)*
9. [ ] Criar dados/logs para demonstrar uma anomalia e estimar risco. *(Card 08)*
10. [ ] Criar integração com n8n. *(Card 09)*
11. [ ] Organizar evidências em `/docs`. *(Card 10)*
12. [ ] Finalizar README. *(Card 10)*
13. [ ] Gravar vídeo. *(Card 11)*
14. [ ] Conferir repositório, Kanban, vídeo e links antes da entrega. *(Card 11)*

---

# Entrega final

- [ ] Repositório GitHub funcional.
- [ ] Professor adicionado como colaborador, conforme orientação.
- [ ] GitHub Project/Kanban atualizado durante o desenvolvimento.
- [ ] Código final na `main`.
- [x] Nenhuma credencial ou arquivo `.env` versionado.
- [x] `.env.example` incluído.
- [ ] README completo.
- [ ] Documentação e evidências organizadas.
- [ ] Vídeo no YouTube como não listado.
- [ ] Links do repositório, Kanban e vídeo enviados no AVA.

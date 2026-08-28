# Review — Card 04 (PR #23)

**Repositório:** [MineiaMaschio/incident-classification-agent](https://github.com/MineiaMaschio/incident-classification-agent)  
**PR:** [feat: implement prompt injection detection and autonomy limits](https://github.com/MineiaMaschio/incident-classification-agent/pull/23)  
**Ferramenta:** senai-pr-reviewer (LangGraph + Gemini 3.6 Flash)  
**Modelo:** `gemini-3.6-flash`  
**Commit analisado:** `568dfca136444c7b258eef99c730791ed4de11a5`  
**Arquivos analisados:** 9  
**Data da revisão:** 2026-08-27

---

## Resumo geral

Revisão concluída. As alterações implementam a detecção determinística de prompt injection via regex no nó de validação, evitam chamadas desnecessárias ao LLM em entradas adversariais, tratam a formatação de resposta genérica e documentam adequadamente os limites de autonomia e evidências.

**Decisão do review:** ✅ **APROVADO** (sem ressalvas)

---

## Achados

**Nenhum problema foi encontrado.**

> Silêncio é um resultado válido e esperado — significa que a implementação está alinhada com as convenções do projeto e sem problemas identificáveis na diff.

---

## Pontos positivos observados

| Ponto | Observação |
|---|---|
| **Detecção determinística** | Regex é compilado uma única vez e não depende do LLM, evitando custos e latência desnecessários em entradas maliciosas |
| **Limites de autonomia** | Documentados de forma clara em `autonomy-limits.md` com 5 ações permitidas e 6 bloqueadas |
| **Resposta genérica** | Tratamento de resposta consistente com o padrão do restante do grafo, sem exposição de detalhes técnicos |
| **Evidência real** | Arquivo `prompt-injection.md` inclui logs reais e output do agente, facilitando auditoria |
| **Proteção de dados** | Campo `phone` auditado e intencionalmente omitido da saída com comentário explicativo |
| **Roteamento early-exit** | Quando injection detectada, fluxo termina antes de `_detect_multiple_incidents()`, economizando uma chamada ao LLM |

---

## Decisões de design confirmadas

| Decisão | Justificativa | Status |
|---|---|---|
| Regex determinístico (sem LLM) | Bloqueia antes de qualquer invocação de modelo, garantindo segurança em camada de validação | ✅ Aprovado |
| 4 categorias de padrões | Reescrita de papel, descarte de instruções, escape de contexto, injeção direta | ✅ Aprovado |
| Mensagem genérica | Não menciona "injection", "adversarial", "regex" ou detalhes técnicos | ✅ Aprovado |
| Phone em estado interno | Mantido para futuros escalonamentos, omitido apenas na saída | ✅ Aprovado |
| Grafo fixo e auditável | Arestas compiladas em tempo de inicialização, sem auto-modificação | ✅ Aprovado |

---

## Testes realizados

| Cenário | Resultado | Evidence |
|---|---|---|
| Entrada legítima | Processada normalmente, arquivo salvo | `20260828T012123Z_b1707f65-2394-4fe6-891f-d5cfc36d6ae8.json` |
| Entrada adversarial | Bloqueada em `validate_input`, msg genérica, nenhuma chamada ao LLM | Logs em `docs/evidences/prompt-injection.md` |

---

## Recomendações futuras (Card 05+)

- [ ] Considerar expandir detecção com patterns ML se volume de bypass crescer
- [ ] Auditar logs de injection detectadas periodicamente para novos padrões
- [ ] Integrar rate limiting por thread_id para prevenir force-brute de padrões

---

*Revisão aprovada sem ressalvas. Card 04 pronto para merge.*

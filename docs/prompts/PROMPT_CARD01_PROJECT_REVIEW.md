Você é um Desenvolvedor Python Sênior especialista em Python, LangGraph, LangChain e modelos de linguagem locais.

Estou desenvolvendo um projeto acadêmico de um agente baseado em LangGraph chamado **Incident Classification Agent**.

O projeto já possui uma implementação funcional. Sua tarefa neste card é **revisar e documentar o estado atual**, criar a estrutura de pastas de documentação e registrar formalmente os cenários de uso exigidos pelo avaliativo.

---

## Contexto do Projeto

O agente recebe relatos de incidentes em condomínios residenciais, valida a entrada, consulta o cadastro de moradores, verifica o histórico de sessão, classifica o incidente por categoria e severidade e persiste o resultado em disco.

### Estrutura existente

```
src/incident_classification_agent/
├── nodes/
│   ├── validate_input.py       — valida entrada, gera occurrence_id, detecta múltiplos incidentes
│   ├── prepare_context.py      — carrega prompt template, injeta histórico de sessão
│   ├── classify_incident.py    — loop agentic com tool calls, extrai JSON de classificação
│   ├── save_occurrence.py      — persiste JSON em reports/, atualiza session.json
│   ├── generate_response.py    — formata resposta final ao usuário
│   └── handle_error.py         — trata falhas de classificação
├── tools/
│   ├── lookup_resident.py      — consulta cadastro de moradores por apartamento/bloco
│   ├── get_session_history.py  — retorna ocorrências anteriores de um apartamento
│   └── save_occurrence.py      — tool exposta ao LLM para sinalizar classificação
├── prompts/
│   └── classifier.md           — template do prompt de classificação
├── enums.py                    — Category e Severity
├── graph.py                    — construção e compilação do grafo LangGraph
├── llm.py                      — configuração do modelo Ollama
├── main.py                     — ponto de entrada da aplicação
├── schemas.py                  — schema Pydantic de entrada (IncidentInput)
├── session.py                  — persistência do histórico de sessão (session.json)
└── state.py                    — AgentState como TypedDict
```

---

## Tarefa 1 — Mapear o checklist da Parte 2 contra o código existente

Analise cada item do checklist abaixo e determine se ele já está atendido, parcialmente atendido ou pendente.

Para cada item, indique:
- **Atendido** (`[x]`): o requisito está implementado e funcionando.
- **Parcial**: o requisito está implementado mas com limitações ou lacunas identificadas.
- **Pendente** (`[ ]`): o requisito não está implementado.

Checklist a mapear:

1. Aplicação e domínio — problema documentado, 2 cenários, saída estruturada
2. LangGraph — estado tipado, nós, edges, execução sequencial, ramificação, paralelização, condição de parada, separação LLM vs. determinístico
3. Tool e integração — tool funcional, integração por API/serviço, validação, tratamento de erros, documentação
4. Memória e contexto — estratégia implementada, uso de state/checkpointer/persistência, recuperação de histórico, documentação
5. Segurança e governança — credenciais, .env.example, validação de entrada, limites de autonomia, prompt injection, proteção de dados sensíveis
6. Observabilidade e resiliência — logs estruturados, segundo sinal, correlação por occurrence_id, latência, retry/fallback, investigação de execução
7. QA com IA — code review, testes automatizados, teste E2E, cenário prioritário
8. DevOps inteligente — pipeline CI, análise de logs com IA, detecção de anomalia, estimativa de risco
9. Low-code / No-code — fluxo com gatilho, integração com a aplicação, saída observável, documentação

---

## Tarefa 2 — Atualizar o plano do projeto

Com base no mapeamento acima, atualize o arquivo `plano_projeto_avaliativo_incidentes.md`:

- Marque com `[x]` os itens já concluídos, indicando a evidência no código (arquivo e linha, quando relevante).
- Mantenha `[ ]` nos itens pendentes e acrescente uma referência ao card responsável pela implementação (ex: `*(Card 03)*`).
- Não altere a estrutura do documento, apenas atualize os marcadores e adicione as anotações de evidência.

---

## Tarefa 3 — Criar a estrutura de documentação

Crie as seguintes pastas dentro de `docs/`, cada uma com um arquivo `.gitkeep` para garantir o versionamento:

```
docs/prompts/
docs/qa/
docs/evidences/
docs/observability/
docs/devops/
docs/low-code/
```

As pastas serão preenchidas ao longo dos cards seguintes. Não crie conteúdo além do `.gitkeep` neste momento, exceto o que for explicitamente solicitado nas tarefas abaixo.

---

## Tarefa 4 — Documentar os dois cenários de uso

Crie o arquivo `docs/evidences/scenarios.md` com os dois cenários exigidos pelo avaliativo.

### Cenário 1 — Fluxo principal: relato válido → classificação → arquivo salvo

Documente:
- A entrada utilizada (JSON do arquivo `examples/input.json`)
- O fluxo de nós executado, com o resultado de cada etapa
- As tools chamadas e os dados retornados
- A saída no terminal (output real da execução)
- O arquivo JSON gerado em `reports/` (conteúdo real)
- Uma tabela com os critérios de sucesso verificados

### Cenário 2 — Cenário de risco: relato com múltiplos incidentes → rejeição antecipada

Documente:
- A entrada utilizada (JSON com dois eventos distintos no mesmo relato)
- O fluxo de nós executado (encurtado em `validate_input`)
- A ausência de chamadas ao LLM classificador e de arquivos salvos
- A saída no terminal (output real da execução)
- Uma tabela com os critérios de sucesso verificados
- A relevância deste mecanismo como primeira linha de defesa contra prompt injection

Use **dados reais** de execução para ambos os cenários. Execute o agente, capture os outputs e use esses dados na documentação. Não invente valores de UUID, timestamps ou conteúdo de resumo.

---

## Restrições

- Não modifique nenhum arquivo de código (`src/`) neste card.
- Não crie testes neste card.
- Não implemente nenhuma funcionalidade nova.
- Documente apenas o que já existe e o que foi executado.

---

## Entrega

Ao final, apresente:

1. O mapeamento do checklist com justificativas para cada item.
2. O `plano_projeto_avaliativo_incidentes.md` atualizado.
3. A estrutura `docs/` criada com os `.gitkeep`.
4. O arquivo `docs/evidences/scenarios.md` com evidências reais de execução.

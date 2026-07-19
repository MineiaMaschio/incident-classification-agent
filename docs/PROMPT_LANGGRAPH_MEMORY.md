Você é um engenheiro de software sênior especialista em **Python, LangGraph, LangChain e arquitetura de agentes de IA**.

Sua tarefa é evoluir um agente já existente, implementando mecanismos de memória e reutilização de contexto entre interações.

A implementação deve preservar a arquitetura atual do projeto, manter o código organizado e seguir as boas práticas recomendadas para aplicações desenvolvidas com LangGraph.

---

# Objetivo

Implemente um mecanismo de memória capaz de manter o histórico de ocorrências processadas durante uma sessão do agente.

O histórico deverá permitir que o agente reutilize informações de interações anteriores para enriquecer o processo de classificação e aplicar regras de negócio baseadas em reincidência.

A solução deve permanecer preparada para futuras evoluções e manter baixo acoplamento entre seus componentes.

---

# Estado Compartilhado

Atualize o estado compartilhado do agente para incluir uma estrutura responsável por armazenar o histórico da sessão.

Cada item do histórico deve conter as informações relevantes da ocorrência já processada, permitindo sua reutilização pelos demais componentes do agente.

O histórico deve permanecer consistente durante toda a execução da sessão.

---

# Memória da Sessão

Utilize o mecanismo nativo de persistência de estado disponibilizado pelo LangGraph.

A memória deve ser organizada por sessão, garantindo que execuções pertencentes a contextos diferentes permaneçam isoladas entre si.

O identificador da sessão deve ser derivado das informações de entrada já disponíveis no agente.

---

# Consulta ao Histórico

Implemente uma ferramenta responsável por recuperar ocorrências anteriores relacionadas ao contexto atual.

Essa ferramenta deverá:

* consultar o histórico da sessão;
* retornar os registros encontrados de forma estruturada;
* informar claramente quando não existir histórico disponível;
* ser reutilizável pelos nós do fluxo.

A consulta deverá ser integrada ao processo de classificação juntamente com as demais ferramentas já existentes.

---

# Persistência para Auditoria

Além da memória utilizada durante a execução do agente, mantenha um histórico acumulativo em disco.

Esse histórico deverá:

* armazenar todas as ocorrências processadas com sucesso;
* preservar o formato atual dos registros;
* ser atualizado automaticamente após cada processamento;
* servir como artefato de auditoria da sessão.

---

# Processo de Classificação

Atualize o processo de classificação para utilizar o histórico recuperado antes da chamada ao modelo de linguagem.

O contexto das ocorrências anteriores deverá ser disponibilizado ao LLM juntamente com o relato atual.

Inclua explicitamente a seguinte regra de negócio:

* quando houver reincidência da mesma categoria para o mesmo apartamento, a severidade deverá ser elevada em um nível.

Essa regra deverá fazer parte do prompt utilizado pelo classificador.

---

# Atualização da Memória

Após cada ocorrência processada com sucesso, atualize automaticamente o histórico armazenado na memória da sessão.

O estado compartilhado deverá refletir todas as ocorrências já processadas durante aquela execução.

---

# Compatibilidade

A implementação deve preservar completamente o comportamento atual do agente.

Em especial:

* não altere o contrato de entrada;
* não altere o formato dos arquivos de ocorrência já gerados;
* mantenha compatibilidade com os fluxos de erro existentes;
* preserve o tratamento para rejeição de múltiplos incidentes;
* reutilize a arquitetura já existente sempre que possível.

---

# Limitações

Documente claramente que a memória em execução é volátil por natureza.

Explique que seu conteúdo permanece disponível apenas durante a sessão do agente, enquanto o histórico em disco possui finalidade exclusivamente de auditoria.

---

# Resultado Esperado

Ao processar duas ocorrências consecutivas da mesma categoria para um mesmo apartamento durante a mesma sessão, o agente deverá utilizar o histórico recuperado para identificar a reincidência e classificar a segunda ocorrência com severidade superior àquela que seria atribuída caso o relato fosse analisado isoladamente.

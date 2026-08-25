Você é um engenheiro de software sênior especialista em **Python, LangGraph e arquitetura de agentes de IA**.

Sua tarefa é evoluir um agente de classificação de incidentes já existente, adicionando novas capacidades de tomada de decisão, uso autônomo de ferramentas e tratamento de situações especiais.

A implementação deve preservar a arquitetura atual do projeto, manter o código organizado e seguir as boas práticas recomendadas para aplicações desenvolvidas com LangGraph.

---

# Contexto do Projeto

O agente recebe relatos em linguagem natural sobre incidentes ocorridos em um condomínio residencial.

A partir desse relato, ele deve compreender o ocorrido, identificar a categoria do incidente, avaliar sua severidade, registrar a ocorrência e fornecer uma resposta clara ao usuário.

O projeto é desenvolvido em Python utilizando LangGraph e executa um modelo de linguagem local por meio do Ollama. Toda a comunicação com o usuário deve permanecer em português.

---

# Objetivo

Evolua o agente para torná-lo mais autônomo, resiliente e preparado para cenários reais de utilização.

A solução deve incorporar mecanismos de decisão durante a execução, utilização inteligente de ferramentas e tratamento diferenciado para ocorrências críticas, preservando a organização e a extensibilidade do projeto.

---

# Fluxo do Agente

Revise o fluxo atual para permitir decisões condicionais durante a execução.

O agente não deve seguir obrigatoriamente um único caminho de processamento.

Sempre que uma etapa não puder ser concluída com segurança, o fluxo deverá direcionar a execução para o tratamento mais apropriado, evitando falhas, respostas inconsistentes ou estados inválidos.

Quando necessário, utilize os recursos do LangGraph para implementar decisões baseadas no estado da execução.

---

# Utilização de Ferramentas

Implemente o uso de ferramentas de forma autônoma.

O modelo de linguagem deve ser capaz de decidir quando utilizar cada ferramenta disponível, de acordo com o contexto da conversa, sem depender de uma sequência fixa de chamadas.

As ferramentas disponíveis são:

* consulta de dados cadastrais de moradores;
* registro de ocorrências.

A consulta aos dados de moradores deverá ser utilizada para enriquecer o contexto da classificação, permitindo ao agente validar informações relevantes, como autorizações de acesso ou dados cadastrais mencionados no relato.

A ferramenta de registro deverá ser utilizada apenas quando houver informações suficientes para registrar a ocorrência.

---

# Tratamento de Incidentes Críticos

Implemente um fluxo específico para incidentes classificados como graves.

Além do registro convencional, esses incidentes deverão receber um tratamento diferenciado para facilitar sua identificação posterior.

O agente também deverá informar claramente ao usuário quando uma ocorrência for considerada crítica e exigir atenção prioritária.

---

# Segurança do Projeto

Garanta que o projeto siga boas práticas de segurança.

Nenhuma informação sensível deverá permanecer versionada no repositório.

Inclua a estrutura necessária para configuração segura do ambiente de execução, fornecendo exemplos e orientações para novos desenvolvedores configurarem o projeto corretamente.

Sempre que aplicável, utilize arquivos de exemplo e mecanismos apropriados para gerenciamento de configurações.

---

# Arquitetura

Preserve a organização atual do projeto.

As novas funcionalidades devem ser incorporadas de forma modular, respeitando os princípios de responsabilidade única, baixo acoplamento e alta coesão.

Sempre que uma funcionalidade puder ser reutilizada em diferentes partes do fluxo, organize-a como um componente independente.


# Resultado Esperado

Ao final da implementação, o agente deverá:

* tomar decisões durante a execução do fluxo;
* utilizar ferramentas de forma autônoma quando necessário;
* enriquecer a classificação utilizando informações cadastrais dos moradores;
* tratar incidentes críticos de forma diferenciada;
* responder adequadamente quando não houver informações suficientes para concluir uma classificação;
* manter o projeto organizado, seguro e preparado para futuras evoluções.
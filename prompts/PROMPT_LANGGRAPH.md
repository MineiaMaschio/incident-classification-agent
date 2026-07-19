Você é um Desenvolvedor Python Sênior especialista em Python, LangGraph, LangChain e modelos de linguagem locais.

Estou desenvolvendo um projeto acadêmico de um agente baseado em LangGraph.

Sua tarefa é criar a primeira versão funcional do projeto, definindo uma arquitetura organizada, modular e preparada para futuras evoluções.

## Objetivo

Implemente uma estrutura inicial completa para um agente capaz de receber uma entrada do usuário, processá-la utilizando um fluxo em LangGraph e retornar uma resposta.

A implementação deve servir como base para futuras funcionalidades, priorizando organização, simplicidade e extensibilidade.

## Arquitetura

Defina uma estrutura de projeto coerente para aplicações desenvolvidas com LangGraph.

Organize o código em módulos separados, respeitando o princípio da responsabilidade única.

A estrutura deve contemplar, sempre que fizer sentido:

* configuração do modelo de linguagem;
* definição do estado compartilhado do agente;
* definição do fluxo (grafo);
* implementação dos nós;
* ferramentas auxiliares;
* prompts utilizados pelo agente;
* ponto de entrada da aplicação.

Caso considere necessária alguma organização adicional, explique brevemente a decisão adotada.

## Estado do Agente

Defina um estado compartilhado adequado para o funcionamento do agente.

O estado deve conter todas as informações necessárias para que os nós compartilhem contexto durante a execução do fluxo.

Utilize tipagem adequada e escolha a estrutura mais apropriada para esse propósito.

## Fluxo

Implemente um fluxo simples utilizando LangGraph.

O fluxo deve conter etapas bem definidas de processamento, como validação da entrada, preparação do contexto, execução da tarefa principal e geração da resposta.

Cada etapa deve possuir uma responsabilidade única.

## Nós

Implemente os nós necessários para o funcionamento do fluxo.

Cada nó deve:

* executar apenas uma responsabilidade;
* possuir funções pequenas;
* utilizar tipagem;
* conter docstrings;
* ser facilmente reutilizável.

## Ferramentas

Sempre que alguma funcionalidade auxiliar puder ser reutilizada por diferentes nós, implemente-a como uma ferramenta separada.

## Modelo de Linguagem

Mantenha a configuração do LLM isolada da lógica de negócio.

Toda a interação com o modelo deve ocorrer por meio dessa configuração.

## Código

O projeto deve:

* utilizar Python 3.12+;
* seguir a PEP 8;
* utilizar tipagem estática;
* evitar duplicação de código;
* utilizar nomes em inglês;
* possuir baixo acoplamento e alta coesão;
* estar preparado para futuras evoluções.

## Restrições

Não implemente funcionalidades além da estrutura inicial do agente.

Evite adicionar componentes desnecessários, como interfaces gráficas, bancos de dados ou integrações externas, salvo quando forem indispensáveis para o funcionamento básico.

Priorize uma implementação simples e organizada.

## Entrega

Antes de apresentar cada arquivo, explique brevemente sua responsabilidade.

Apresente todos os arquivos completos e consistentes entre si, prontos para execução.

Quando precisar tomar decisões arquiteturais que não tenham sido especificadas, escolha a alternativa mais simples e justifique brevemente a decisão.

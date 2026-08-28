"""Definição e compilação do grafo LangGraph do agente."""

import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from incident_classification_agent.nodes.classify_incident import (
    _route_after_classify,
    classify_incident,
)
from incident_classification_agent.nodes.generate_response import generate_response
from incident_classification_agent.nodes.handle_error import handle_error
from incident_classification_agent.nodes.prepare_context import prepare_context
from incident_classification_agent.nodes.prefetch_resident import prefetch_resident
from incident_classification_agent.nodes.save_occurrence import save_occurrence
from incident_classification_agent.nodes.validate_input import (
    _route_after_validate,
    validate_input,
)
from incident_classification_agent.state import AgentState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Constrói e compila o grafo de processamento de incidentes.

    Utiliza MemorySaver como checkpointer para preservar o estado completo
    do agente entre execuções do mesmo thread_id. Isso permite que variáveis
    de estado — incluindo session_history — sejam mantidas em memória durante
    toda a vida do processo, sem depender apenas do session.json em disco.

    Nota: MemorySaver é volátil — o estado é perdido quando o processo encerra.
    Para persistência entre processos distintos, o session.json (atualizado
    pelo nó save_occurrence) serve como fonte de verdade durável.

    Fluxo principal (com paralelização):
        START → validate_input → [prepare_context ∥ prefetch_resident]
               → classify_incident → (condicional) → save_occurrence
               → generate_response → END

    Fluxo de múltiplos incidentes (rejeição antecipada):
        validate_input → generate_response → END

    Fluxo de erro de classificação:
        classify_incident → handle_error → generate_response → END

    Returns:
        Grafo compilado pronto para execução.
    """
    graph = StateGraph(AgentState)

    graph.add_node("validate_input", validate_input)
    graph.add_node("prepare_context", prepare_context)
    graph.add_node("prefetch_resident", prefetch_resident)
    graph.add_node("classify_incident", classify_incident)
    graph.add_node("handle_error", handle_error)
    graph.add_node("save_occurrence", save_occurrence)
    graph.add_node("generate_response", generate_response)

    graph.add_edge(START, "validate_input")

    # _route_after_validate retorna "prepare_context" para o caminho normal
    # ou "generate_response" quando múltiplos incidentes são detectados.
    # O mapa abaixo mantém "generate_response" inalterado e redireciona
    # "prepare_context" para um nó intermediário fan_out que dispara os dois
    # ramos paralelos. Como add_conditional_edges exige um mapa 1-para-1,
    # usamos a string "prepare_context" como chave de rota e apontamos para
    # o próprio nó prepare_context; o segundo ramo (prefetch_resident) é
    # conectado via add_edge separado, fazendo o LangGraph agendar ambos no
    # mesmo super-step após validate_input.
    graph.add_conditional_edges(
        "validate_input",
        _route_after_validate,
        {
            "prepare_context": "prepare_context",
            "generate_response": "generate_response",
        },
    )

    # ---------------------------------------------------------------------------
    # Fan-out / Fan-in — paralelização de prepare_context e prefetch_resident
    # ---------------------------------------------------------------------------
    # Por que esses dois nós foram escolhidos para rodar em paralelo:
    #
    #   • prepare_context  — operação puramente local (leitura de arquivo Markdown
    #     + consulta ao session.json em memória). Sem I/O de rede.
    #
    #   • prefetch_resident — faz uma chamada HTTP à API FastAPI de moradores.
    #     É a única operação de I/O de rede no caminho quente antes do LLM.
    #
    # Os dois nós não têm dependência entre si: um escreve em
    # ``conversation_history`` e o outro em ``resident_info`` — chaves distintas
    # do AgentState, sem risco de conflito de reducer.
    #
    # Como o fan-in funciona:
    #   O LangGraph agenda em paralelo todos os nós cujas dependências já estão
    #   satisfeitas no mesmo super-step. Ao adicionar uma aresta de prepare_context
    #   → classify_incident E uma aresta de prefetch_resident → classify_incident,
    #   o runtime garante que classify_incident só será executado após AMBOS
    #   completarem, fazendo o merge automático dos campos atualizados no estado.
    # ---------------------------------------------------------------------------

    # Segundo ramo do fan-out: validate_input também dispara prefetch_resident
    # em paralelo com prepare_context (ambas as arestas saem de validate_input
    # através do conditional_edges acima + esta aresta direta abaixo).
    graph.add_edge("validate_input", "prefetch_resident")

    # Fan-in: classify_incident só executa após ambos os ramos concluírem.
    graph.add_edge("prepare_context", "classify_incident")
    graph.add_edge("prefetch_resident", "classify_incident")

    graph.add_conditional_edges(
        "classify_incident",
        _route_after_classify,
        {
            "save_occurrence": "save_occurrence",
            "handle_error": "handle_error",
        },
    )

    graph.add_edge("handle_error", "generate_response")
    graph.add_edge("save_occurrence", "generate_response")
    graph.add_edge("generate_response", END)

    checkpointer = MemorySaver()
    compiled = graph.compile(checkpointer=checkpointer)

    logger.info("Graph compiled successfully with MemorySaver checkpointer.")

    return compiled

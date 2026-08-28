"""Definição e compilação do grafo LangGraph do agente."""

import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing import Annotated

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


def _track_node_execution(node_func, node_name):
    """Cria um wrapper que rastreia a execução de um nó.

    Args:
        node_func: Função do nó a ser envolvida.
        node_name: Nome do nó (para logging e rastreamento).

    Returns:
        Função wrapper que atualiza nodes_executed no estado.
    """
    def wrapper(state: AgentState) -> dict:
        result = node_func(state)
        
        # Retorna o resultado do nó junto com nodes_executed atualizado
        # O reducer _append_to_list do LangGraph irá mesclar a lista
        if isinstance(result, dict):
            return {**result, "nodes_executed": [node_name]}
        return result
    
    return wrapper


def _fan_out(state: AgentState) -> dict:
    """Nó intermediário de fan-out — não modifica o estado.

    Serve exclusivamente como ponto de convergência após ``validate_input``
    no caminho principal, permitindo que ``prepare_context`` e
    ``prefetch_resident`` sejam disparados em paralelo a partir de duas
    arestas simples. Sem esse nó intermediário, seria necessário uma aresta
    incondicional direta de ``validate_input`` para ``prefetch_resident``,
    o que faria o ramo paralelo executar também no fluxo de rejeição por
    múltiplos incidentes — um bug crítico identificado em code review.

    Args:
        state: Estado atual do agente (passado sem modificação).

    Returns:
        Dicionário com nodes_executed atualizado.
    """
    occurrence_id = state.get("occurrence_id", "unknown")
    prefix = f"[occurrence_id={occurrence_id}]"
    
    logger.debug(f"{prefix} Executing fan_out node.")
    
    return {"nodes_executed": ["fan_out"]}


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
        START → validate_input → fan_out → [prepare_context ∥ prefetch_resident]
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

    # Envolve cada nó com rastreamento de nodes_executed
    wrapped_validate_input = _track_node_execution(validate_input, "validate_input")
    wrapped_prepare_context = _track_node_execution(prepare_context, "prepare_context")
    wrapped_prefetch_resident = _track_node_execution(prefetch_resident, "prefetch_resident")
    wrapped_classify_incident = _track_node_execution(classify_incident, "classify_incident")
    wrapped_handle_error = _track_node_execution(handle_error, "handle_error")
    wrapped_save_occurrence = _track_node_execution(save_occurrence, "save_occurrence")
    wrapped_generate_response = _track_node_execution(generate_response, "generate_response")

    graph.add_node("validate_input", wrapped_validate_input)
    graph.add_node("fan_out", _fan_out)
    graph.add_node("prepare_context", wrapped_prepare_context)
    graph.add_node("prefetch_resident", wrapped_prefetch_resident)
    graph.add_node("classify_incident", wrapped_classify_incident)
    graph.add_node("handle_error", wrapped_handle_error)
    graph.add_node("save_occurrence", wrapped_save_occurrence)
    graph.add_node("generate_response", wrapped_generate_response)

    graph.add_edge(START, "validate_input")

    # ---------------------------------------------------------------------------
    # Roteamento condicional após validate_input
    # ---------------------------------------------------------------------------
    # _route_after_validate retorna "fan_out" para o caminho principal ou
    # "generate_response" quando múltiplos incidentes são detectados.
    # O nó intermediário fan_out garante que prefetch_resident só seja
    # executado no caminho principal — nunca no fluxo de rejeição antecipada.
    # (Correção do bug crítico identificado em code review: a aresta estática
    # add_edge("validate_input", "prefetch_resident") executava o ramo paralelo
    # também no fluxo de rejeição, causando classificações e gravações indevidas.)
    # ---------------------------------------------------------------------------
    graph.add_conditional_edges(
        "validate_input",
        _route_after_validate,
        {
            "prepare_context": "fan_out",
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

    # Fan-out: fan_out dispara prepare_context e prefetch_resident em paralelo.
    graph.add_edge("fan_out", "prepare_context")
    graph.add_edge("fan_out", "prefetch_resident")

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

"""Nó responsável por pré-carregar dados do morador em paralelo com prepare_context."""

import logging

from incident_classification_agent.state import AgentState
from incident_classification_agent.tools.lookup_resident import lookup_resident

logger = logging.getLogger(__name__)


def prefetch_resident(state: AgentState) -> AgentState:
    """Pré-carrega os dados do morador invocando a tool lookup_resident diretamente.

    Executa em paralelo com ``prepare_context`` no grafo, antecipando a chamada
    HTTP à API de moradores antes do loop agentic em ``classify_incident``.
    Isso reduz a latência total do fluxo principal, pois a operação de I/O de
    rede ocorre ao mesmo tempo em que o template do prompt é preparado.

    Se ``resident_info`` já estiver preenchido no estado (idempotência), a chamada
    à API é ignorada. Se ``apartment`` não estiver presente no estado, o nó retorna
    sem modificações — a tool não pode ser invocada sem o identificador do apartamento.

    Args:
        state: Estado atual do agente. Requer ``apartment`` para realizar a consulta.

    Returns:
        Estado atualizado com ``resident_info`` preenchido quando o morador é
        encontrado, ou inalterado nos demais casos.
    """
    # Idempotência: se já foi preenchido (ex: por execução anterior no mesmo thread),
    # não faz nova chamada à API.
    if state.get("resident_info") is not None:
        logger.info(
            "prefetch_resident — resident_info já presente no estado, ignorando chamada à API."
        )
        return {}

    apartment = state.get("apartment")
    building = state.get("building")

    if not apartment:
        logger.info(
            "prefetch_resident — 'apartment' ausente no estado; nenhuma consulta realizada."
        )
        return {}

    logger.info(
        "prefetch_resident — consultando morador: apartamento=%s bloco=%s",
        apartment,
        building,
    )

    result: dict = {}
    try:
        result = lookup_resident.invoke({"apartment": apartment, "building": building})
    except Exception as exc:
        logger.error(
            "prefetch_resident — erro de rede ao consultar API: %s; resident_info permanece None.",
            exc,
        )
        return {}

    if result.get("found"):
        logger.info(
            "prefetch_resident — morador encontrado: %s (apto %s bloco %s)",
            result.get("resident_name"),
            apartment,
            building,
        )
        return {"resident_info": result}

    if result.get("error"):
        logger.warning(
            "prefetch_resident — falha ao consultar API: %s; resident_info permanece None.",
            result.get("error"),
        )
        return {}

    logger.info(
        "prefetch_resident — morador não encontrado: apartamento=%s bloco=%s",
        apartment,
        building,
    )
    return {}

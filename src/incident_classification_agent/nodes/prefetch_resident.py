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
    occurrence_id = state.get("occurrence_id", "unknown")
    prefix = f"[occurrence_id={occurrence_id}]"

    logger.info(f"{prefix} Iniciando prefetch_resident...")

    # Idempotência: se já foi preenchido (ex: por execução anterior no mesmo thread),
    # não faz nova chamada à API.
    if state.get("resident_info") is not None:
        logger.info(
            f"{prefix} resident_info já presente no estado, ignorando chamada à API."
        )
        return {}

    apartment = state.get("apartment")
    building = state.get("building")

    if not apartment:
        logger.info(
            f"{prefix} 'apartment' ausente no estado; nenhuma consulta realizada."
        )
        return {}

    logger.debug(
        f"{prefix} Consultando morador: apartamento={apartment} bloco={building}"
    )

    result: dict = {}
    try:
        result = lookup_resident.invoke({"apartment": apartment, "building": building})
    except Exception as exc:
        logger.error(
            f"{prefix} Erro de rede ao consultar API: {exc}; resident_info permanece None.",
        )
        return {}

    if result.get("found"):
        logger.info(
            f"{prefix} Morador encontrado: {result.get('resident_name')} (apto {apartment} bloco {building})",
        )
        return {"resident_info": result}

    if result.get("error"):
        logger.warning(
            f"{prefix} Falha ao consultar API: {result.get('error')}; resident_info permanece None.",
        )
        return {}

    logger.info(
        f"{prefix} Morador não encontrado: apartamento={apartment} bloco={building}",
    )
    return {}

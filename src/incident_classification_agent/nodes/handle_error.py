"""Nó responsável por tratar falhas na classificação do incidente."""

import logging

from incident_classification_agent.state import AgentState

logger = logging.getLogger(__name__)


def handle_error(state: AgentState) -> AgentState:
    """Registra e prepara o estado para exibição de erro ao usuário.

    Executado quando ``classify_incident`` não consegue extrair uma
    classificação válida da resposta do LLM. Garante que o fluxo chegue
    ao ``generate_response`` com informações suficientes para uma
    resposta de falha clara.

    Args:
        state: Estado atual com ``classification_error`` preenchido.

    Returns:
        Estado inalterado (o erro já está registrado em ``classification_error``).
    """
    occurrence_id = state.get("occurrence_id", "unknown")
    prefix = f"[occurrence_id={occurrence_id}]"

    error = state.get("classification_error", "Erro desconhecido na classificação.")
    logger.error(
        f"{prefix} Handling classification error: {error}",
    )
    return state

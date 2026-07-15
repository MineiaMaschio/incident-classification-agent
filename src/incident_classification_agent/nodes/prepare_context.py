"""Nó responsável por preparar o contexto antes da classificação."""

import logging
from pathlib import Path

from incident_classification_agent.state import AgentState

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "classifier.md"


def _load_prompt_template() -> str:
    """Carrega o template do prompt a partir do arquivo Markdown.

    Returns:
        Conteúdo do arquivo de prompt como string.

    Raises:
        FileNotFoundError: Se o arquivo de prompt não for encontrado.
    """
    return _PROMPT_PATH.read_text(encoding="utf-8")


def prepare_context(state: AgentState) -> AgentState:
    """Monta a mensagem de entrada para o LLM e atualiza o histórico.

    Carrega o template do classificador, substitui as variáveis pelo
    conteúdo do estado e adiciona a mensagem ao ``conversation_history``.

    Args:
        state: Estado atual do agente.

    Returns:
        Estado atualizado com o histórico de conversa preenchido.
    """
    template = _load_prompt_template()

    prompt = template.replace("{user_input}", state["user_input"])
    prompt = prompt.replace("{reported_by}", state["reported_by"])
    prompt = prompt.replace("{reported_at}", state["reported_at"])

    history = list(state.get("conversation_history") or [])
    history.append(prompt)

    logger.info("Context prepared for occurrence_id: %s", state.get("occurrence_id"))

    return {**state, "conversation_history": history}

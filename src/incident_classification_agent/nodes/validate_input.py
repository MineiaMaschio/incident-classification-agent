"""Nó responsável por validar os dados de entrada do agente."""

import logging
import re
import uuid
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage

from incident_classification_agent.llm import get_llm
from incident_classification_agent.state import AgentState

logger = logging.getLogger(__name__)

_DETECTION_PROMPT = """\
Você é um analisador de texto objetivo. Leia o relato abaixo e determine se ele descreve \
UM único incidente ou MÚLTIPLOS incidentes distintos (eventos independentes, envolvendo \
pessoas, locais ou situações diferentes).

Responda APENAS com uma das palavras: SINGLE ou MULTIPLE

Relato:
{user_input}
"""

# Padrões regex para detecção de prompt injection (compilados uma única vez por performance)
# Detecta: reescrita de papel, descarte de instruções, escape de contexto e injeção direta
_INJECTION_PATTERNS = re.compile(
    r"(você\s+agora\s+é|you\s+are\s+now|act\s+as|atue\s+como|finja\s+que\s+é|pretend\s+you\s+are|"
    r"ignore\s+instruções\s+anteriores|ignore\s+previous\s+instructions|esqueça\s+tudo|"
    r"forget\s+everything|ignore\s+as\s+regras|ignore\s+your\s+instructions|"
    r"novo\s+prompt|new\s+prompt|system\s+prompt|ignore\s+o\s+sistema|ignore\s+the\s+system|"
    r"#{2,}\s+instru|#{2,}\s+instruction|\[instru|\[system\]|<\|im_start\|>|<\|system\|>)",
    re.IGNORECASE,
)


def _detect_injection(user_input: str) -> bool:
    """Detecta padrões adversariais de prompt injection usando regex determinístico.

    Verifica a presença de padrões conhecidos de tentativa de manipulação do LLM,
    como "ignore instruções anteriores", "você agora é", tokens especiais de modelos,
    etc. A detecção é feita **sem enviar o input ao LLM**, garantindo que entradas
    maliciosas sejam bloqueadas na camada de validação.

    Args:
        user_input: Texto do relato a ser analisado.

    Returns:
        True se um padrão adversarial foi detectado, False caso contrário.
    """
    match = _INJECTION_PATTERNS.search(user_input)
    if match:
        logger.warning(
            "Prompt injection pattern detected — padrão: %s",
            match.group(0)[:50],  # Log apenas os primeiros 50 chars do padrão para brevidade
        )
        return True
    return False


def _detect_multiple_incidents(user_input: str) -> bool:
    """Consulta o LLM para verificar se o relato contém múltiplos incidentes.

    Args:
        user_input: Texto do relato a ser analisado.

    Returns:
        True se múltiplos incidentes forem detectados, False caso contrário.
    """
    llm = get_llm()
    prompt = _DETECTION_PROMPT.format(user_input=user_input)
    response = llm.invoke([HumanMessage(content=prompt)])
    answer = response.content.strip().upper()

    logger.info("Multiple incidents detection result: %s", answer)

    return "MULTIPLE" in answer


def _route_after_validate(state: AgentState) -> str:
    """Decide o próximo nó após a validação da entrada.

    Se uma entrada adversarial foi detectada, encerra o fluxo antecipadamente
    em ``generate_response`` para informar o usuário. Se múltiplos incidentes
    foram detectados, faz o mesmo. Caso contrário, segue o fluxo normal para
    ``prepare_context``.

    Args:
        state: Estado atual após a execução de ``validate_input``.

    Returns:
        Nome do próximo nó: ``"prepare_context"`` ou ``"generate_response"``.
    """
    if state.get("injection_detected"):
        logger.warning("Injection detected — short-circuiting to generate_response.")
        return "generate_response"
    if state.get("multiple_incidents_detected"):
        logger.warning("Multiple incidents detected — short-circuiting to generate_response.")
        return "generate_response"
    return "prepare_context"


def validate_input(state: AgentState) -> AgentState:
    """Valida e normaliza os campos obrigatórios do estado de entrada.

    Garante que ``user_input`` e ``reported_by`` estejam presentes.
    Preenche ``reported_at`` com o instante atual quando ausente.
    Gera um ``occurrence_id`` único para rastrear a ocorrência.
    Detecta se o relato contém padrões adversariais de prompt injection via regex —
    nesse caso, ``injection_detected`` é marcado como True e o fluxo é encerrado
    antes da classificação, sem qualquer chamada ao LLM.
    Se a entrada não for adversarial, detecta se o relato contém múltiplos
    incidentes distintos via LLM — nesse caso, ``multiple_incidents_detected``
    é marcado como True e o fluxo é encerrado.

    Args:
        state: Estado atual do agente.

    Returns:
        Estado atualizado com os campos validados e normalizados.

    Raises:
        ValueError: Se ``user_input`` ou ``reported_by`` estiverem vazios.
    """
    user_input = (state.get("user_input") or "").strip()
    reported_by = (state.get("reported_by") or "").strip()

    if not user_input:
        raise ValueError("O campo 'user_input' é obrigatório.")

    if not reported_by:
        raise ValueError("O campo 'reported_by' é obrigatório.")

    reported_at = state.get("reported_at") or datetime.now(tz=timezone.utc).isoformat()
    occurrence_id = state.get("occurrence_id") or str(uuid.uuid4())

    # Detecta prompt injection ANTES de enviar qualquer coisa ao LLM
    injection_detected = _detect_injection(user_input)

    # Se foi detectado injection, não chama o LLM
    if injection_detected:
        logger.warning(
            "Prompt injection detected — occurrence_id: %s",
            occurrence_id,
        )
        multiple_incidents_detected = False
    else:
        # Caso contrário, verifica múltiplos incidentes normalmente
        multiple_incidents_detected = _detect_multiple_incidents(user_input)

    logger.info(
        "Input validated — occurrence_id: %s | injection: %s | multiple_incidents: %s",
        occurrence_id,
        injection_detected,
        multiple_incidents_detected,
    )

    return {
        **state,
        "user_input": user_input,
        "reported_by": reported_by,
        "reported_at": reported_at,
        "occurrence_id": occurrence_id,
        "involved_people": state.get("involved_people") or [],
        "conversation_history": state.get("conversation_history") or [],
        "injection_detected": injection_detected,
        "multiple_incidents_detected": multiple_incidents_detected,
    }

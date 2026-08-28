"""Nó responsável por classificar o incidente via LLM com uso de tools."""

import json
import logging
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from incident_classification_agent.enums import Category, Severity
from incident_classification_agent.llm import get_llm
from incident_classification_agent.state import AgentState
from incident_classification_agent.tools.get_session_history import get_session_history
from incident_classification_agent.tools.lookup_resident import lookup_resident

logger = logging.getLogger(__name__)

TOOLS = [lookup_resident, get_session_history]
tool_node = ToolNode(TOOLS)


def _extract_json(text: str) -> dict:
    """Extrai o primeiro bloco JSON encontrado na resposta do LLM.

    Tenta parsear a partir de cada '{' encontrado no texto usando
    JSONDecoder.raw_decode, evitando capturas incorretas por regex greedy.

    Args:
        text: Texto retornado pelo modelo.

    Returns:
        Dicionário com os dados extraídos.

    Raises:
        ValueError: Se nenhum JSON válido for encontrado.
    """
    decoder = json.JSONDecoder()
    for i, char in enumerate(text):
        if char == "{":
            try:
                obj, _ = decoder.raw_decode(text, i)
                return obj
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Nenhum JSON válido encontrado na resposta do LLM: {text!r}")


def _route_after_classify(state: AgentState) -> str:
    """Decide o próximo nó após a classificação.

    Roteia para ``handle_error`` se a classificação falhou (campos
    obrigatórios ausentes ou inválidos). Caso contrário, segue para
    ``save_occurrence``.

    Args:
        state: Estado atual após a execução de ``classify_incident``.

    Returns:
        Nome do próximo nó: ``"save_occurrence"`` ou ``"handle_error"``.
    """
    if state.get("classification_error"):
        logger.warning("Routing to handle_error — reason: %s", state["classification_error"])
        return "handle_error"
    return "save_occurrence"


def classify_incident(state: AgentState) -> AgentState:
    """Envia o prompt ao LLM com tools disponíveis e extrai a classificação.

    O LLM recebe as tools ``lookup_resident`` e ``save_occurrence`` via
    ``bind_tools``. Quando o modelo emite tool calls, elas são executadas
    pelo ``ToolNode`` e o resultado é repassado de volta ao LLM para que
    ele incorpore as informações antes de produzir a classificação final.

    Campos atualizados no estado: ``category``, ``severity``,
    ``involved_people``, ``apartment``, ``building``, ``summary``,
    ``resident_info``, ``output_file``, ``escalated_file``,
    ``conversation_history`` e ``classification_error``.

    Args:
        state: Estado atual do agente (requer ``conversation_history`` preenchido).

    Returns:
        Estado atualizado com os campos de classificação preenchidos.
    """
    occurrence_id = state.get("occurrence_id", "unknown")
    prefix = f"[occurrence_id={occurrence_id}]"

    logger.info(f"{prefix} Iniciando classify_incident...")

    import time

    history = state.get("conversation_history") or []
    prompt_text = history[-1] if history else state["user_input"]

    llm = get_llm()
    llm_with_tools = llm.bind_tools(TOOLS).with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,
    )

    messages = [HumanMessage(content=prompt_text)]

    # Se prefetch_resident já consultou a API em paralelo e encontrou o morador,
    # injeta o resultado como ToolMessage sintética antes do primeiro invoke do LLM.
    # Isso evita uma chamada HTTP redundante dentro do loop agentic: o LLM recebe
    # os dados do morador como se tivesse chamado a tool, e pode pular direto para
    # a classificação. A tool lookup_resident permanece no bind como fallback —
    # caso resident_info esteja ausente (apartment não informado ou API indisponível
    # durante o prefetch), o LLM pode chamar a tool normalmente.
    prefetched_resident: dict | None = state.get("resident_info")
    resident_info: dict | None = prefetched_resident if (prefetched_resident and prefetched_resident.get("found")) else None

    if prefetched_resident and prefetched_resident.get("found"):
        # Simula o par AIMessage (tool_call) + ToolMessage (resultado) para que
        # o histórico de mensagens seja válido segundo o protocolo do LangChain.
        synthetic_tool_call_id = f"prefetch_{uuid.uuid4().hex[:8]}"
        synthetic_ai = AIMessage(
            content="",
            tool_calls=[
                {
                    "id": synthetic_tool_call_id,
                    "name": "lookup_resident",
                    "args": {
                        "apartment": prefetched_resident.get("apartment", ""),
                        "building": prefetched_resident.get("building"),
                    },
                }
            ],
        )
        synthetic_tool_msg = ToolMessage(
            content=json.dumps(prefetched_resident),
            tool_call_id=synthetic_tool_call_id,
            name="lookup_resident",
        )
        messages.extend([synthetic_ai, synthetic_tool_msg])
        logger.debug(
            f"{prefix} resident_info pré-carregado injetado no contexto "
            f"(apto {prefetched_resident.get('apartment')} bloco {prefetched_resident.get('building')} → {prefetched_resident.get('resident_name')}); tool call evitada.",
        )

    # ANTES DO LLM — registra o tempo de início
    state["llm_start_time"] = time.time()
    logger.debug(f"{prefix} LLM invocation started.")

    # Agentic loop: continua enquanto o LLM emitir tool calls
    for _ in range(5):  # limite de segurança para evitar loop infinito
        ai_message: AIMessage = llm_with_tools.invoke(messages)
        messages.append(ai_message)

        if not ai_message.tool_calls:
            break

        # Executa cada tool call emitida pelo LLM
        tool_results = tool_node.invoke({"messages": messages})
        tool_messages: list[ToolMessage] = tool_results["messages"]

        for tm in tool_messages:
            messages.append(tm)
            try:
                result = json.loads(tm.content) if isinstance(tm.content, str) else tm.content
            except (json.JSONDecodeError, TypeError):
                result = {}

            tool_name = tm.name if hasattr(tm, "name") else ""
            if tool_name == "lookup_resident":
                result_found = result.get("found")
                # Só sobrescreve resident_info se ainda não foi preenchido pelo
                # prefetch_resident (prioridade: dado mais recente do loop agentic).
                if result_found:
                    resident_info = result

    # APÓS O LLM — registra o tempo de fim
    state["llm_end_time"] = time.time()
    logger.debug(
        f"{prefix} LLM invocation ended — latency: {(state['llm_end_time'] - state['llm_start_time']) * 1000:.2f}ms"
    )

    raw = ai_message.content
    logger.debug(f"{prefix} LLM final response: {raw[:200]}...")

    # Atualiza histórico com a resposta final do LLM
    history = list(history)
    history.append(raw)

    # Valida e extrai a classificação do JSON retornado pelo LLM
    classification_error: str | None = None
    category: Category | None = None
    severity: Severity | None = None
    data: dict = {}

    try:
        data = _extract_json(raw)

        raw_category = data.get("category")
        raw_severity = data.get("severity")

        if not raw_category:
            raise ValueError("Campo 'category' ausente na resposta do LLM.")
        if not raw_severity:
            raise ValueError("Campo 'severity' ausente na resposta do LLM.")

        category = Category(raw_category)
        severity = Severity(raw_severity)

        # Loga o raciocínio de severidade quando disponível
        reasoning = data.get("reasoning")
        if reasoning:
            logger.info(
                f"{prefix} Severity reasoning — base: {reasoning.get('base_severity')} | recurrence: {reasoning.get('recurrence_detected')} ({reasoning.get('recurrence_count')}) | final: {reasoning.get('final_severity')}",
            )

    except (ValueError, KeyError) as exc:
        classification_error = str(exc)
        logger.error(f"{prefix} Classification failed — {classification_error}")

    if not classification_error:
        logger.info(
            f"{prefix} Incident classified — category: {category}, severity: {severity}",
        )

    return {
        **state,
        "llm_start_time": state.get("llm_start_time"),
        "llm_end_time": state.get("llm_end_time"),
        "category": category,
        "severity": severity,
        "involved_people": data.get("involved_people") or [],
        "apartment": data.get("apartment"),
        "building": data.get("building"),
        "summary": data.get("summary"),
        "resident_info": resident_info,
        "conversation_history": history,
        "classification_error": classification_error,
    }

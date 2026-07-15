"""Nó responsável por persistir a ocorrência em disco."""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from incident_classification_agent.state import AgentState

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent.parent.parent
REPORTS_DIR = _BASE_DIR / "reports"
ESCALATED_DIR = REPORTS_DIR / "escalated"


def save_occurrence(state: AgentState) -> AgentState:
    """Persiste a ocorrência em disco injetando os campos de contexto do estado.

    A classificação (category, severity, summary, etc.) foi extraída pelo LLM
    via tool call e já está no estado. Este nó combina esses dados com os
    campos de contexto imutáveis (occurrence_id, user_input, reported_by,
    reported_at, resident_info) e grava o arquivo JSON final.

    Incidentes com severidade HIGH são adicionalmente copiados para
    reports/escalated/ com flag de escalonamento.

    Args:
        state: Estado atual do agente com todos os campos preenchidos.

    Returns:
        Estado atualizado com ``output_file`` e, se aplicável, ``escalated_file``.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    occurrence_id = state.get("occurrence_id") or str(uuid.uuid4())
    category = state.get("category")
    severity = state.get("severity")

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{timestamp}_{occurrence_id}.json"

    payload = {
        "occurrence_id": occurrence_id,
        "reported_by": state.get("reported_by"),
        "reported_at": state.get("reported_at"),
        "user_input": state.get("user_input"),
        "category": category.value if category is not None else None,
        "severity": severity.value if severity is not None else None,
        "involved_people": state.get("involved_people") or [],
        "apartment": state.get("apartment"),
        "building": state.get("building"),
        "summary": state.get("summary"),
        "resident_info": state.get("resident_info"),
        "saved_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    output_path = REPORTS_DIR / filename
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Occurrence saved to %s", output_path)

    result: dict = {"output_file": str(output_path), "escalated_file": None}

    severity_value = severity.value if severity is not None else None
    if severity_value == "HIGH":
        ESCALATED_DIR.mkdir(parents=True, exist_ok=True)
        escalated_path = ESCALATED_DIR / filename
        escalated_payload = {
            **payload,
            "escalated": True,
            "escalated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        escalated_path.write_text(
            json.dumps(escalated_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.warning("HIGH severity — occurrence escalated to %s", escalated_path)
        result["escalated_file"] = str(escalated_path)

    return {**state, "output_file": result["output_file"], "escalated_file": result["escalated_file"]}

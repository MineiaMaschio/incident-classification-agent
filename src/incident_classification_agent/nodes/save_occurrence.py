"""Nó responsável por persistir a ocorrência em disco."""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

from incident_classification_agent.session import append_to_session
from incident_classification_agent.state import AgentState

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent.parent.parent
REPORTS_DIR = _BASE_DIR / "reports"
ESCALATED_DIR = REPORTS_DIR / "escalated"


async def _send_webhook_async(webhook_url: str, payload: dict, occurrence_id: str) -> bool:
    """Envia payload via webhook para o n8n de forma não-bloqueante.

    Args:
        webhook_url: URL do webhook (ex: http://localhost:5678/webhook/incidents)
        payload: Dicionário com os dados da ocorrência
        occurrence_id: ID da ocorrência para logging

    Returns:
        True se sucesso, False se falha (não lança exceção)
    """
    prefix = f"[occurrence_id={occurrence_id}]"

    if not webhook_url or not webhook_url.strip():
        logger.debug(f"{prefix} WEBHOOK_URL not configured, skipping webhook call")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code in (200, 201, 202, 204):
                logger.info(
                    f"{prefix} Webhook sent successfully "
                    f"[status={response.status_code}]"
                )
                return True
            else:
                logger.warning(
                    f"{prefix} Webhook failed [status={response.status_code}] "
                    f"[response={response.text[:200]}]"
                )
                return False

    except asyncio.TimeoutError:
        logger.warning(f"{prefix} Webhook timeout after 10s")
        return False
    except httpx.RequestError as exc:
        logger.warning(f"{prefix} Webhook error: {exc}")
        return False
    except Exception as exc:
        logger.error(f"{prefix} Unexpected error sending webhook: {exc}", exc_info=True)
        return False


def _dispatch_webhook(webhook_url: str, payload: dict, occurrence_id: str) -> None:
    """Dispara o webhook de forma não-bloqueante usando asyncio.

    Args:
        webhook_url: URL do webhook
        payload: Dicionário com os dados
        occurrence_id: ID da ocorrência
    """
    try:
        asyncio.run(_send_webhook_async(webhook_url, payload, occurrence_id))
    except Exception as exc:
        logger.error(f"[occurrence_id={occurrence_id}] Failed to dispatch webhook: {exc}")


def save_occurrence(state: AgentState) -> AgentState:
    """Persiste a ocorrência em disco injetando os campos de contexto do estado.

    A classificação (category, severity, summary, etc.) foi extraída pelo LLM
    via tool call e já está no estado. Este nó combina esses dados com os
    campos de contexto imutáveis (occurrence_id, user_input, reported_by,
    reported_at, resident_info) e grava o arquivo JSON final.

    Além do arquivo individual, atualiza o ``session.json`` acumulativo com
    uma entrada resumida da ocorrência, usada pela tool ``get_session_history``
    para consulta de reincidência em interações futuras.

    Incidentes com severidade HIGH são adicionalmente copiados para
    reports/escalated/ com flag de escalonamento.

    Args:
        state: Estado atual do agente com todos os campos preenchidos.

    Returns:
        Estado atualizado com ``output_file``, ``escalated_file`` e
        ``session_history`` refletindo o acumulado da sessão corrente.
    """
    occurrence_id = state.get("occurrence_id") or str(uuid.uuid4())
    prefix = f"[occurrence_id={occurrence_id}]"

    logger.info(f"{prefix} Iniciando save_occurrence...")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

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
    logger.info(f"{prefix} Occurrence saved to {output_path}")

    # Entrada resumida para o histórico de sessão — usada por get_session_history
    session_entry = {
        "occurrence_id": occurrence_id,
        "reported_at": state.get("reported_at"),
        "reported_by": state.get("reported_by"),
        "category": category.value if category is not None else None,
        "severity": severity.value if severity is not None else None,
        "summary": state.get("summary"),
        "apartment": state.get("apartment"),
        "building": state.get("building"),
    }
    logger.debug(f"{prefix} Appending to session history...")
    append_to_session(session_entry)

    # Atualiza o session_history em memória no estado do agente
    session_history = list(state.get("session_history") or [])
    session_history.append(session_entry)

    result: dict = {
        "output_file": str(output_path),
        "escalated_file": None,
        "session_history": session_history,
    }

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
        logger.warning(f"{prefix} HIGH severity — occurrence escalated to {escalated_path}")
        result["escalated_file"] = str(escalated_path)

        # Dispara webhook para n8n de forma não-bloqueante
        webhook_url = os.getenv("WEBHOOK_URL", "").strip()
        if webhook_url:
            logger.info(f"{prefix} Dispatching webhook to {webhook_url}")
            _dispatch_webhook(webhook_url, escalated_payload, occurrence_id)
        else:
            logger.debug(f"{prefix} WEBHOOK_URL not configured")

    logger.info(f"{prefix} save_occurrence concluído.")

    return {**state, **result}

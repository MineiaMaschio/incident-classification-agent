"""Módulo de auditoria estruturada e append-only para rastreamento de ocorrências."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from incident_classification_agent.state import AgentState


class AuditEntry(TypedDict):
    """Entrada de auditoria estruturada para uma execução do agente.

    Attributes:
        occurrence_id: Identificador único da ocorrência.
        started_at: Timestamp ISO 8601 com timezone UTC do início da execução.
        ended_at: Timestamp ISO 8601 com timezone UTC do fim da execução.
        total_latency_ms: Latência total em milissegundos com até 3 casas decimais.
        llm_latency_ms: Latência do LLM em milissegundos, ou None se não disponível.
        nodes_executed: Lista de nós executados durante a processamento.
        status: Status da execução ("success", "error", ou "rejected").
        category: Categoria classificada do incidente ou None.
        severity: Severidade classificada do incidente ou None.
        multiple_incidents_detected: True se múltiplos incidentes foram detectados.
        classification_error: Mensagem de erro de classificação, ou None.
        reported_by: Nome de quem reportou o incidente.
        apartment: Apartamento relacionado ou None.
        building: Bloco/torre relacionado ou None.
    """

    occurrence_id: str
    started_at: str
    ended_at: str
    total_latency_ms: float
    llm_latency_ms: float | None
    nodes_executed: list[str]
    status: str
    category: str | None
    severity: str | None
    multiple_incidents_detected: bool
    classification_error: str | None
    reported_by: str
    apartment: str | None
    building: str | None


def save_audit_entry(
    entry: AuditEntry, audit_path: str = "reports/audit.jsonl"
) -> None:
    """Salva a entrada de auditoria em arquivo append-only.

    O arquivo é criado se não existir. Cada execução gera uma linha JSON,
    permitindo leitura incremental e análise de histórico.

    Args:
        entry: Dicionário com os dados de auditoria.
        audit_path: Caminho para o arquivo de auditoria (padrão: reports/audit.jsonl).

    Returns:
        None
    """
    os.makedirs(os.path.dirname(audit_path) or ".", exist_ok=True)
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def build_audit_entry(state: AgentState) -> AuditEntry:
    """Constrói uma entrada de auditoria a partir do estado final.

    Extrai os campos relevantes do estado e calcula as latências.

    Args:
        state: Estado final do agente após execução completa.

    Returns:
        Dicionário AuditEntry pronto para persistência.

    Raises:
        ValueError: Se execution_start_time ou execution_end_time não estiverem
            preenchidos no estado (esperado que o grafo os preencha).
    """
    if state.get("execution_start_time") is None:
        raise ValueError("execution_start_time não preenchido no estado.")
    if state.get("execution_end_time") is None:
        raise ValueError("execution_end_time não preenchido no estado.")

    started_at = datetime.fromtimestamp(
        state["execution_start_time"], tz=timezone.utc
    ).isoformat()

    ended_at = datetime.fromtimestamp(
        state["execution_end_time"], tz=timezone.utc
    ).isoformat()

    total_latency_ms = (
        state["execution_end_time"] - state["execution_start_time"]
    ) * 1000

    llm_latency_ms = None
    if state.get("llm_start_time") and state.get("llm_end_time"):
        llm_latency_ms = (state["llm_end_time"] - state["llm_start_time"]) * 1000

    # Determina o status com base no estado final
    if state.get("classification_error"):
        status = "error"
    elif state.get("multiple_incidents_detected"):
        status = "rejected"
    else:
        status = "success"

    # Converte enums para strings (se forem enums, caso contrário já são strings)
    category_val = state.get("category")
    category_str = category_val.value if hasattr(category_val, "value") else category_val

    severity_val = state.get("severity")
    severity_str = severity_val.value if hasattr(severity_val, "value") else severity_val

    return AuditEntry(
        occurrence_id=state.get("occurrence_id", "unknown"),
        started_at=started_at,
        ended_at=ended_at,
        total_latency_ms=total_latency_ms,
        llm_latency_ms=llm_latency_ms,
        nodes_executed=state.get("nodes_executed") or [],
        status=status,
        category=category_str,
        severity=severity_str,
        multiple_incidents_detected=state.get("multiple_incidents_detected", False),
        classification_error=state.get("classification_error"),
        reported_by=state["reported_by"],
        apartment=state.get("apartment"),
        building=state.get("building"),
    )

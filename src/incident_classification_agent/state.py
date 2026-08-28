"""Definição do estado compartilhado entre os nós do grafo."""

from typing import Annotated, TypedDict

from incident_classification_agent.enums import Category, Severity


def _append_to_list(left, right):
    """Reducer para concatenar listas sem duplicatas.

    Usado para o campo nodes_executed que pode ser atualizado por múltiplos
    nós em paralelo (prepare_context e prefetch_resident).
    """
    if left is None:
        return right or []
    if right is None:
        return left or []
    # Concatena e remove duplicatas mantendo ordem
    result = list(left)
    for item in right:
        if item not in result:
            result.append(item)
    return result


class AgentState(TypedDict):
    """Estado completo do agente durante o processamento de um incidente.

    Attributes:
        user_input: Texto bruto informado pelo usuário.
        reported_by: Nome de quem reportou o incidente.
        reported_at: Data/hora do reporte (ISO 8601).
        occurrence_id: Identificador único gerado para a ocorrência.
        category: Categoria classificada do incidente.
        severity: Severidade classificada do incidente.
        involved_people: Lista de pessoas envolvidas no incidente.
        apartment: Apartamento relacionado ao incidente.
        building: Bloco/torre relacionado ao incidente.
        summary: Resumo gerado pelo agente em português.
        conversation_history: Histórico de mensagens da conversa.
        output_file: Caminho do arquivo JSON salvo com a ocorrência.
        escalated_file: Caminho do arquivo de escalonamento (apenas para HIGH).
        classification_error: Mensagem de erro caso a classificação falhe.
        resident_info: Informações do morador consultado via tool.
        multiple_incidents_detected: True se o relato contém mais de um
            incidente distinto, sinalizando rejeição do input.
        injection_detected: True se o relato contém padrões adversariais de
            prompt injection, sinalizando rejeição do input antes de qualquer
            chamada ao LLM.
        session_history: Histórico acumulado de ocorrências processadas na
            sessão corrente. Cada entrada representa uma ocorrência já
            classificada com sucesso, contendo os campos relevantes para
            consulta de reincidência e contexto entre interações.
        execution_start_time: Timestamp (time.time()) do início da execução.
        execution_end_time: Timestamp (time.time()) do final da execução.
        llm_start_time: Timestamp (time.time()) do início do LLM em classify_incident.
        llm_end_time: Timestamp (time.time()) do final do LLM em classify_incident.
        nodes_executed: Lista de nós executados durante o processamento (com reducer).
    """

    user_input: str
    reported_by: str
    reported_at: str
    occurrence_id: str | None
    category: Category | None
    severity: Severity | None
    involved_people: list[str]
    apartment: str | None
    building: str | None
    summary: str | None
    conversation_history: list[str]
    output_file: str | None
    escalated_file: str | None
    classification_error: str | None
    resident_info: dict | None
    multiple_incidents_detected: bool | None
    injection_detected: bool | None
    session_history: list[dict]
    execution_start_time: float | None
    execution_end_time: float | None
    llm_start_time: float | None
    llm_end_time: float | None
    nodes_executed: Annotated[list[str], _append_to_list]

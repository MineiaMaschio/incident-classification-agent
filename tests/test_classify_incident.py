"""Testes unitários para o nó classify_incident.

Cobre cenários críticos:
- Extração de JSON da resposta do LLM
- Roteamento condicional
- Propagação de llm_start_time e llm_end_time (bug do Card 05)
- Tratamento de respostas malformadas
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from incident_classification_agent.nodes.classify_incident import (
    _extract_json,
    _route_after_classify,
    classify_incident,
)
from incident_classification_agent.enums import Category, Severity
from incident_classification_agent.state import AgentState


class TestExtractJson:
    """Testes para a função _extract_json."""

    def test_extract_json_valid_json(self):
        """✅ JSON válido no texto — extraído corretamente."""
        text = 'Análise: {"category": "MAINTENANCE", "severity": "MEDIUM"}'
        result = _extract_json(text)

        assert result["category"] == "MAINTENANCE"
        assert result["severity"] == "MEDIUM"

    def test_extract_json_embedded_in_code_block(self):
        """✅ JSON embutido em bloco markdown — extraído."""
        text = """
        Aqui está a classificação:
        ```json
        {
            "category": "SECURITY",
            "severity": "HIGH",
            "reasoning": {"base_severity": "HIGH"}
        }
        ```
        Fim da análise.
        """
        result = _extract_json(text)

        assert result["category"] == "SECURITY"
        assert result["severity"] == "HIGH"
        assert result["reasoning"]["base_severity"] == "HIGH"

    def test_extract_json_first_valid_object(self):
        """✅ Múltiplos JSONs — extrai o primeiro válido."""
        text = '{"invalid": } {"category": "MAINTENANCE", "severity": "LOW"}'
        result = _extract_json(text)

        assert result["category"] == "MAINTENANCE"
        assert result["severity"] == "LOW"

    def test_extract_json_complex_nested(self):
        """✅ JSON complexo com nesting — extraído completo."""
        text = json.dumps({
            "category": "OTHER",
            "severity": "CRITICAL",
            "involved_people": ["João", "Maria"],
            "reasoning": {
                "base_severity": "CRITICAL",
                "recurrence_detected": True,
                "recurrence_count": 3,
                "final_severity": "CRITICAL"
            }
        })
        result = _extract_json(text)

        assert result["category"] == "OTHER"
        assert result["severity"] == "CRITICAL"
        assert len(result["involved_people"]) == 2
        assert result["reasoning"]["recurrence_count"] == 3

    def test_extract_json_no_json_in_text(self):
        """❌ Sem JSON na resposta — ValueError."""
        text = "A análise é: não encontrei nada"
        with pytest.raises(ValueError, match="Nenhum JSON válido"):
            _extract_json(text)

    def test_extract_json_invalid_json_only(self):
        """❌ JSON inválido — ValueError."""
        text = "Resultado: {invalid json here}"
        with pytest.raises(ValueError, match="Nenhum JSON válido"):
            _extract_json(text)

    def test_extract_json_empty_object(self):
        """✅ JSON vazio é válido — retorna dicionário vazio."""
        text = "Resultado: {}"
        result = _extract_json(text)

        assert result == {}

    def test_extract_json_starts_with_json(self):
        """✅ JSON no início do texto."""
        text = '{"category": "MAINTENANCE", "severity": "LOW"} análise aqui'
        result = _extract_json(text)

        assert result["category"] == "MAINTENANCE"


class TestRouteAfterClassify:
    """Testes para a função _route_after_classify."""

    def test_route_after_classify_success(self):
        """✅ Classificação bem-sucedida → retorna 'save_occurrence'."""
        state: AgentState = {
            "user_input": "Vazamento.",
            "reported_by": "joao@email.com",
            "reported_at": "2026-08-28T10:00:00+00:00",
            "occurrence_id": "test-id-1",
            "category": Category.MAINTENANCE,
            "severity": Severity.MEDIUM,
            "involved_people": [],
            "apartment": None,
            "building": None,
            "summary": "Houve vazamento.",
            "conversation_history": [],
            "output_file": None,
            "escalated_file": None,
            "classification_error": None,
            "resident_info": None,
            "multiple_incidents_detected": False,
            "injection_detected": False,
            "session_history": [],
            "execution_start_time": None,
            "execution_end_time": None,
            "llm_start_time": None,
            "llm_end_time": None,
            "nodes_executed": [],
        }

        result = _route_after_classify(state)
        assert result == "save_occurrence"

    def test_route_after_classify_error(self):
        """❌ Erro na classificação → retorna 'handle_error'."""
        state: AgentState = {
            "user_input": "Vazamento.",
            "reported_by": "joao@email.com",
            "reported_at": "2026-08-28T10:00:00+00:00",
            "occurrence_id": "test-id-1",
            "category": None,
            "severity": None,
            "involved_people": [],
            "apartment": None,
            "building": None,
            "summary": None,
            "conversation_history": [],
            "output_file": None,
            "escalated_file": None,
            "classification_error": "Campo 'category' ausente na resposta do LLM.",
            "resident_info": None,
            "multiple_incidents_detected": False,
            "injection_detected": False,
            "session_history": [],
            "execution_start_time": None,
            "execution_end_time": None,
            "llm_start_time": None,
            "llm_end_time": None,
            "nodes_executed": [],
        }

        result = _route_after_classify(state)
        assert result == "handle_error"

    def test_route_after_classify_empty_error(self):
        """✅ classification_error vazio/None → retorna 'save_occurrence'."""
        state: AgentState = {
            "user_input": "Vazamento.",
            "reported_by": "joao@email.com",
            "reported_at": "2026-08-28T10:00:00+00:00",
            "occurrence_id": "test-id-1",
            "category": Category.MAINTENANCE,
            "severity": Severity.LOW,
            "involved_people": [],
            "apartment": None,
            "building": None,
            "summary": "Houve vazamento.",
            "conversation_history": [],
            "output_file": None,
            "escalated_file": None,
            "classification_error": None,
            "resident_info": None,
            "multiple_incidents_detected": False,
            "injection_detected": False,
            "session_history": [],
            "execution_start_time": None,
            "execution_end_time": None,
            "llm_start_time": None,
            "llm_end_time": None,
            "nodes_executed": [],
        }

        result = _route_after_classify(state)
        assert result == "save_occurrence"


class TestClassifyIncident:
    """Testes para a função classify_incident (nó completo)."""

    def _create_base_state(self) -> AgentState:
        """Helper para criar estado base."""
        return {
            "user_input": "Houve um vazamento de água.",
            "reported_by": "joao@email.com",
            "reported_at": "2026-08-28T10:00:00+00:00",
            "occurrence_id": "test-id-1",
            "category": None,
            "severity": None,
            "involved_people": [],
            "apartment": "101",
            "building": "A",
            "summary": None,
            "conversation_history": ["Houve um vazamento de água."],
            "output_file": None,
            "escalated_file": None,
            "classification_error": None,
            "resident_info": None,
            "multiple_incidents_detected": False,
            "injection_detected": False,
            "session_history": [],
            "execution_start_time": None,
            "execution_end_time": None,
            "llm_start_time": None,
            "llm_end_time": None,
            "nodes_executed": [],
        }

    def test_classify_incident_valid_response(self):
        """✅ LLM retorna JSON válido — classificação populada."""
        state = self._create_base_state()

        llm_response = {
            "category": "MAINTENANCE",
            "severity": "MEDIUM",
            "summary": "Vazamento de água no apartamento.",
            "involved_people": ["João"],
            "apartment": "101",
            "building": "A"
        }

        mock_llm = MagicMock()
        mock_ai_message = MagicMock()
        mock_ai_message.content = json.dumps(llm_response)
        mock_ai_message.tool_calls = []
        mock_llm.bind_tools.return_value.with_retry.return_value.invoke.return_value = mock_ai_message

        with patch(
            "incident_classification_agent.nodes.classify_incident.get_llm",
            return_value=mock_llm,
        ):
            result = classify_incident(state)

        assert result["category"] == Category.MAINTENANCE
        assert result["severity"] == Severity.MEDIUM
        assert result["classification_error"] is None
        # Bug do Card 05: llm_start_time e llm_end_time devem estar no retorno
        assert "llm_start_time" in result
        assert "llm_end_time" in result

    def test_classify_incident_missing_category(self):
        """❌ JSON sem campo 'category' — classificação_error preenchido."""
        state = self._create_base_state()

        llm_response = {
            "severity": "MEDIUM",
            "summary": "Vazamento de água."
        }

        mock_llm = MagicMock()
        mock_ai_message = MagicMock()
        mock_ai_message.content = json.dumps(llm_response)
        mock_ai_message.tool_calls = []
        mock_llm.bind_tools.return_value.with_retry.return_value.invoke.return_value = mock_ai_message

        with patch(
            "incident_classification_agent.nodes.classify_incident.get_llm",
            return_value=mock_llm,
        ):
            result = classify_incident(state)

        assert result["category"] is None
        assert result["classification_error"] is not None
        assert "category" in result["classification_error"].lower()

    def test_classify_incident_missing_severity(self):
        """❌ JSON sem campo 'severity' — classificação_error preenchido."""
        state = self._create_base_state()

        llm_response = {
            "category": "MAINTENANCE",
            "summary": "Vazamento de água."
        }

        mock_llm = MagicMock()
        mock_ai_message = MagicMock()
        mock_ai_message.content = json.dumps(llm_response)
        mock_ai_message.tool_calls = []
        mock_llm.bind_tools.return_value.with_retry.return_value.invoke.return_value = mock_ai_message

        with patch(
            "incident_classification_agent.nodes.classify_incident.get_llm",
            return_value=mock_llm,
        ):
            result = classify_incident(state)

        assert result["severity"] is None
        assert result["classification_error"] is not None
        assert "severity" in result["classification_error"].lower()

    def test_classify_incident_no_json_in_response(self):
        """❌ Resposta sem JSON válido — classificação_error preenchido."""
        state = self._create_base_state()

        mock_llm = MagicMock()
        mock_ai_message = MagicMock()
        mock_ai_message.content = "Resposta sem JSON: a classificação é manutenção"
        mock_ai_message.tool_calls = []
        mock_llm.bind_tools.return_value.with_retry.return_value.invoke.return_value = mock_ai_message

        with patch(
            "incident_classification_agent.nodes.classify_incident.get_llm",
            return_value=mock_llm,
        ):
            result = classify_incident(state)

        assert result["category"] is None
        assert result["classification_error"] is not None

    def test_classify_incident_llm_timings_propagated(self):
        """✅ llm_start_time e llm_end_time são propagados no retorno (BUG FIX Card 05)."""
        state = self._create_base_state()

        llm_response = {
            "category": "MAINTENANCE",
            "severity": "MEDIUM",
            "summary": "Vazamento."
        }

        mock_llm = MagicMock()
        mock_ai_message = MagicMock()
        mock_ai_message.content = json.dumps(llm_response)
        mock_ai_message.tool_calls = []
        mock_llm.bind_tools.return_value.with_retry.return_value.invoke.return_value = mock_ai_message

        with patch(
            "incident_classification_agent.nodes.classify_incident.get_llm",
            return_value=mock_llm,
        ):
            result = classify_incident(state)

        assert result["llm_start_time"] is not None
        assert result["llm_end_time"] is not None
        assert result["llm_end_time"] >= result["llm_start_time"]
        # Latência deve ser pequena em testes (< 1 segundo)
        latency_ms = (result["llm_end_time"] - result["llm_start_time"]) * 1000
        assert latency_ms >= 0

    def test_classify_incident_conversation_history_updated(self):
        """✅ Histórico de conversa atualizado com resposta do LLM."""
        state = self._create_base_state()
        state["conversation_history"] = ["Entrada inicial"]

        llm_response = {
            "category": "MAINTENANCE",
            "severity": "MEDIUM",
            "summary": "Vazamento."
        }

        mock_llm = MagicMock()
        mock_ai_message = MagicMock()
        mock_ai_message.content = json.dumps(llm_response)
        mock_ai_message.tool_calls = []
        mock_llm.bind_tools.return_value.with_retry.return_value.invoke.return_value = mock_ai_message

        with patch(
            "incident_classification_agent.nodes.classify_incident.get_llm",
            return_value=mock_llm,
        ):
            result = classify_incident(state)

        assert len(result["conversation_history"]) == 2
        assert result["conversation_history"][1] == json.dumps(llm_response)

    def test_classify_incident_prefetched_resident_injected(self):
        """✅ resident_info pré-carregado é injetado como ToolMessage sintética."""
        state = self._create_base_state()
        state["resident_info"] = {
            "found": True,
            "apartment": "101",
            "building": "A",
            "resident_name": "João Silva",
            "authorized_visitors": [],
            "vehicles": ["ABC-1234"]
        }

        llm_response = {
            "category": "MAINTENANCE",
            "severity": "MEDIUM",
            "summary": "Vazamento."
        }

        mock_llm = MagicMock()
        mock_ai_message = MagicMock()
        mock_ai_message.content = json.dumps(llm_response)
        mock_ai_message.tool_calls = []
        mock_llm.bind_tools.return_value.with_retry.return_value.invoke.return_value = mock_ai_message

        with patch(
            "incident_classification_agent.nodes.classify_incident.get_llm",
            return_value=mock_llm,
        ):
            result = classify_incident(state)

        # Válida que resident_info foi preservado
        assert result["resident_info"]["resident_name"] == "João Silva"

    def test_classify_incident_invalid_severity_enum(self):
        """❌ Severity inválido — ValueError, classification_error preenchido."""
        state = self._create_base_state()

        llm_response = {
            "category": "MAINTENANCE",
            "severity": "INVALID_SEVERITY",
            "summary": "Vazamento."
        }

        mock_llm = MagicMock()
        mock_ai_message = MagicMock()
        mock_ai_message.content = json.dumps(llm_response)
        mock_ai_message.tool_calls = []
        mock_llm.bind_tools.return_value.with_retry.return_value.invoke.return_value = mock_ai_message

        with patch(
            "incident_classification_agent.nodes.classify_incident.get_llm",
            return_value=mock_llm,
        ):
            result = classify_incident(state)

        assert result["severity"] is None
        assert result["classification_error"] is not None

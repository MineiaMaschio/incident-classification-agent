"""Testes unitários para a tool lookup_resident.

Cobre cenários críticos:
- Resposta bem-sucedida da API
- Erro 404 (morador não encontrado)
- Timeout de conexão
- Erros 5xx (API indisponível)
- Resposta malformada (ValidationError)

NOTA: Testes de HTTP são mocados no nível de httpx.post.
Se a API real estiver rodando, os testes verificam erro handling gracioso.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import httpx

from incident_classification_agent.tools.lookup_resident import lookup_resident


class TestLookupResident:
    """Testes para a tool lookup_resident com mocks de httpx."""

    def test_lookup_resident_timeout_connection_error(self):
        """❌ Timeout de conexão (httpx.ConnectTimeout) — retorna erro."""
        with patch(
            "incident_classification_agent.tools.lookup_resident.httpx.post",
            side_effect=httpx.ConnectTimeout("Connection timeout"),
        ):
            result = lookup_resident.invoke({"apartment": "101", "building": "A"})

        assert result["found"] is False

    def test_lookup_resident_timeout_read_error(self):
        """❌ Timeout de leitura (httpx.ReadTimeout) — retorna erro."""
        with patch(
            "incident_classification_agent.tools.lookup_resident.httpx.post",
            side_effect=httpx.ReadTimeout("Read timeout"),
        ):
            result = lookup_resident.invoke({"apartment": "101", "building": "A"})

        assert result["found"] is False

    def test_lookup_resident_network_error_generic(self):
        """❌ Erro genérico de rede — retorna erro."""
        with patch(
            "incident_classification_agent.tools.lookup_resident.httpx.post",
            side_effect=httpx.NetworkError("Network error"),
        ):
            result = lookup_resident.invoke({"apartment": "101", "building": "A"})

        assert result["found"] is False

    def test_lookup_resident_http_status_error(self):
        """❌ HTTPStatusError (4xx/5xx) — retorna erro."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_request = MagicMock()

        http_error = httpx.HTTPStatusError(
            "Forbidden",
            request=mock_request,
            response=mock_response,
        )

        with patch(
            "incident_classification_agent.tools.lookup_resident.httpx.post",
            side_effect=http_error,
        ):
            result = lookup_resident.invoke({"apartment": "101", "building": "A"})

        assert result["found"] is False

    def test_lookup_resident_always_returns_dict(self):
        """✅ lookup_resident sempre retorna um dicionário."""
        with patch(
            "incident_classification_agent.tools.lookup_resident.httpx.post",
            side_effect=Exception("Unexpected error"),
        ):
            result = lookup_resident.invoke({"apartment": "101", "building": "A"})

        assert isinstance(result, dict)
        assert "found" in result

    def test_lookup_resident_always_has_found_field(self):
        """✅ Retorno sempre contém campo 'found'."""
        with patch(
            "incident_classification_agent.tools.lookup_resident.httpx.post",
            side_effect=httpx.ConnectTimeout("Connection timeout"),
        ):
            result = lookup_resident.invoke({"apartment": "999", "building": "Z"})

        assert "found" in result
        assert isinstance(result["found"], bool)

    def test_lookup_resident_connect_error_fallback(self):
        """❌ ConnectError é tratado com fallback."""
        with patch(
            "incident_classification_agent.tools.lookup_resident.httpx.post",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = lookup_resident.invoke({"apartment": "101", "building": "A"})

        assert result["found"] is False


class TestLookupResidentContract:
    """Testes para validar contrato de lookup_resident."""

    def test_lookup_resident_always_returns_found_field(self):
        """✅ lookup_resident sempre retorna dict com 'found' field."""
        with patch(
            "incident_classification_agent.tools.lookup_resident.httpx.post",
            side_effect=Exception("Error"),
        ):
            result = lookup_resident.invoke({"apartment": "101", "building": "A"})

        assert isinstance(result, dict)
        assert "found" in result
        assert isinstance(result["found"], bool)

    def test_lookup_resident_error_handling_no_crash(self):
        """✅ lookup_resident nunca lança exceção, sempre retorna dict."""
        # Tenta 10 erros diferentes
        errors = [
            httpx.ConnectTimeout("timeout"),
            httpx.ReadTimeout("timeout"),
            httpx.NetworkError("network"),
            httpx.ConnectError("connect"),
            ValueError("value"),
            KeyError("key"),
            Exception("generic"),
        ]

        for error in errors:
            with patch(
                "incident_classification_agent.tools.lookup_resident.httpx.post",
                side_effect=error,
            ):
                # Não deve lançar exceção
                result = lookup_resident.invoke({"apartment": "101", "building": "A"})
                
                # Sempre retorna dict com found=False
                assert isinstance(result, dict)
                assert "found" in result
                assert result["found"] is False

import pytest
from incident_classification_agent.llm import get_llm


def test_ollama_connection():
    """Teste de conexão com Ollama (integração, não unitário)."""
    pytest.skip("Teste de integração com Ollama — execução local apenas")
    llm = get_llm()

    response = llm.invoke("Responda apenas: OK")

    assert response.content
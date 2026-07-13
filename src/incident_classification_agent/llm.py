import logging
import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama


load_dotenv()

logger = logging.getLogger(__name__)


def get_llm() -> ChatOllama:
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    logger.info("Initializing Ollama model: %s", model)

    llm = ChatOllama(
        model=model,
        temperature=0,
        timeout=60,
    )

    return llm.with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,
    )
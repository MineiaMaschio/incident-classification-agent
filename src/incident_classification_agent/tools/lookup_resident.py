"""Tool responsável por consultar dados de moradores via API HTTP."""

import logging
import os

import httpx
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

logger = logging.getLogger(__name__)

_RESIDENTS_API_URL = os.getenv("RESIDENTS_API_URL", "http://localhost:8000")


@tool
def lookup_resident(apartment: str, building: str | None = None) -> dict:
    """Consulta os dados cadastrais do morador de um apartamento específico.

    Útil para verificar se o apartamento existe no condomínio, confirmar o
    nome do morador e checar se ele possui visitantes ou veículos autorizados.

    Args:
        apartment: Número do apartamento (ex: "402", "101-B").
        building: Bloco ou torre do apartamento (ex: "A", "Torre 1"). Opcional.

    Returns:
        Dicionário com os dados do morador encontrado, ou com ``found=False``
        caso o apartamento não esteja cadastrado. Estrutura quando encontrado:
        - ``found``: True
        - ``apartment``: número do apartamento
        - ``building``: bloco/torre
        - ``resident_name``: nome do morador
        - ``authorized_visitors``: lista de visitantes pré-autorizados
        - ``vehicles``: lista de placas de veículos cadastrados
        - ``phone``: telefone de contato (mascarado)
    """
    params: dict[str, str] = {"apartment": apartment}
    if building is not None:
        params["building"] = building

    url = f"{_RESIDENTS_API_URL}/residents"
    logger.info("Consultando API de moradores: %s params=%s", url, params)

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data: dict = response.json()

    except httpx.ConnectError as exc:
        logger.info("API indisponível (ConnectError): %s", exc)
        return {"found": False, "error": "API indisponível"}

    except httpx.TimeoutException as exc:
        logger.info("Timeout ao consultar API de moradores: %s", exc)
        return {"found": False, "error": "API indisponível"}

    except Exception as exc:  # noqa: BLE001
        logger.info("Erro inesperado ao consultar API de moradores: %s", exc)
        return {"found": False, "error": "API indisponível"}

    if data.get("found"):
        logger.info(
            "Morador encontrado: apartamento=%s bloco=%s → %s",
            apartment,
            building,
            data.get("resident_name"),
        )
        return {
            "found": True,
            "apartment": data.get("apartment"),
            "building": data.get("building"),
            "resident_name": data.get("resident_name"),
            "authorized_visitors": data.get("authorized_visitors", []),
            "vehicles": data.get("vehicles", []),
            "phone": data.get("phone"),
        }

    logger.info(
        "Morador não encontrado: apartamento=%s bloco=%s",
        apartment,
        building,
    )
    return {"found": False, "apartment": apartment, "building": building}

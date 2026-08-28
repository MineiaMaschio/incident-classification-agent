"""Tool responsável por consultar dados de moradores via API HTTP."""

import logging
import os

import httpx
from dotenv import load_dotenv
from langchain_core.tools import tool
from pydantic import BaseModel, ValidationError

load_dotenv()

logger = logging.getLogger(__name__)

_RESIDENTS_API_URL = os.getenv("RESIDENTS_API_URL", "http://localhost:8000")


class _ResidentResponse(BaseModel):
    """Schema de validação da resposta da API de moradores.

    Garante que mudanças no contrato do servidor sejam detectadas na
    deserialização, não em KeyError silencioso em tempo de execução.
    """

    found: bool
    apartment: str | None = None
    building: str | None = None
    resident_name: str | None = None
    authorized_visitors: list[str] = []
    vehicles: list[str] = []
    phone: str | None = None


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
        - ``phone``: telefone de contato — disponível no estado interno,
          não exposto na resposta ao usuário (cf. generate_response)
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
            data = _ResidentResponse.model_validate(response.json())

    except httpx.ConnectError as exc:
        logger.warning("API indisponível (ConnectError): %s", exc)
        return {"found": False, "error": "API indisponível"}

    except httpx.TimeoutException as exc:
        logger.warning("Timeout ao consultar API de moradores: %s", exc)
        return {"found": False, "error": "API indisponível"}

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Erro HTTP ao consultar API de moradores: status=%s url=%s",
            exc.response.status_code,
            exc.request.url,
        )
        return {"found": False, "error": "API indisponível"}

    except ValidationError as exc:
        logger.error("Resposta da API fora do contrato esperado: %s", exc)
        return {"found": False, "error": "API indisponível"}

    except Exception as exc:  # noqa: BLE001
        logger.error("Erro inesperado ao consultar API de moradores: %s", exc)
        return {"found": False, "error": "API indisponível"}

    if data.found:
        logger.info(
            "Morador encontrado: apartamento=%s bloco=%s → %s",
            apartment,
            building,
            data.resident_name,
        )
        return {
            "found": True,
            "apartment": data.apartment,
            "building": data.building,
            "resident_name": data.resident_name,
            "authorized_visitors": data.authorized_visitors,
            "vehicles": data.vehicles,
            "phone": data.phone,
        }

    logger.info(
        "Morador não encontrado: apartamento=%s bloco=%s",
        apartment,
        building,
    )
    return {"found": False, "apartment": apartment, "building": building}

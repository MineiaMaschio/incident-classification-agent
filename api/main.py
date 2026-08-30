"""Servidor FastAPI para consulta de moradores do condomínio.

Expõe o endpoint GET /residents para que ferramentas do agente possam
consultar dados cadastrais sem acesso direto ao sistema de arquivos.
"""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Caminho para o arquivo de dados relativo à raiz do projeto.
# __file__ está em <root>/api/main.py → duas subidas chegam à raiz.
_DATA_PATH = Path(__file__).parent.parent / "data" / "residents.json"

app = FastAPI(
    title="Residents API",
    description="API de consulta de moradores para o Incident Classification Agent.",
    version="1.0.0",
)


def _load_residents() -> list[dict]:
    """Carrega a lista de moradores do arquivo residents.json.

    Returns:
        Lista de dicionários com os dados dos moradores.

    Raises:
        HTTPException: 500 se o arquivo não existir ou não puder ser lido.
    """
    if not _DATA_PATH.exists():
        logger.error("residents.json not found at %s", _DATA_PATH)
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao carregar dados.",
        )
    try:
        return json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load residents.json: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao carregar dados.",
        ) from exc


@app.get("/residents")
def get_resident(
    apartment: str = Query(..., min_length=1, description="Número do apartamento (obrigatório)."),
    building: str | None = Query(default=None, description="Bloco ou torre do apartamento (opcional)."),
) -> JSONResponse:
    """Consulta os dados cadastrais do morador de um apartamento específico.

    A busca é case-insensitive. O parâmetro ``building`` é opcional; quando
    omitido, retorna o primeiro apartamento com o número informado independente
    do bloco.

    Args:
        apartment: Número do apartamento (ex: "101", "402"). Obrigatório.
        building: Bloco ou torre (ex: "A", "B"). Opcional.

    Returns:
        JSON com os dados do morador quando encontrado::

            {
                "found": true,
                "apartment": "101",
                "building": "A",
                "resident_name": "Carlos Mendes",
                "authorized_visitors": ["Ana Mendes"],
                "vehicles": ["ABC-1234"],
                "phone": "(11) 9****-1234"
            }

        Ou ``{"found": false}`` quando não localizado.

    Raises:
        HTTPException 422: se ``apartment`` estiver ausente ou vazio.
        HTTPException 500: se o arquivo de dados não puder ser lido.
    """
    residents = _load_residents()

    for resident in residents:
        apt_match = (
            resident.get("apartment", "").strip().lower() == apartment.strip().lower()
        )
        building_match = (
            building is None
            or resident.get("building", "").strip().lower() == building.strip().lower()
        )
        if apt_match and building_match:
            logger.info(
                "Resident found: apartment=%s building=%s → %s",
                apartment,
                building,
                resident.get("resident_name"),
            )
            return JSONResponse(
                content={
                    "found": True,
                    "apartment": resident.get("apartment"),
                    "building": resident.get("building"),
                    "resident_name": resident.get("resident_name"),
                    "authorized_visitors": resident.get("authorized_visitors", []),
                    "vehicles": resident.get("vehicles", []),
                    "phone": resident.get("phone"),
                }
            )

    logger.info("No resident found: apartment=%s building=%s", apartment, building)
    return JSONResponse(content={"found": False})

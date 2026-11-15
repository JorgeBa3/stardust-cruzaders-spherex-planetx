"""Cliente para los servicios de IRSA (NASA/IPAC Infrared Science Archive) que
dan acceso a las observaciones de SPHEREx.

CONFIRMADO en vivo (2026-11-14) contra irsa.ipac.caltech.edu:
- Existe una tabla TAP dedicada "spherex.obscore" (vista via TAP_SCHEMA.tables).
- El patron de cutout por URL funciona (ejemplo real de la doc del Cutout Tool):
    https://irsa.ipac.caltech.edu/ibe/data/spherex/qr/level2/.../archivo.fits
        ?center=<ra>,<dec>&size=<grados>
- El endpoint generico SIA (https://irsa.ipac.caltech.edu/SIA) funciona para otras
  misiones (se probo con wise_allwise y si devolvio filas).

NO CONFIRMADO / A VALIDAR el dia del hackathon:
- COLLECTION=spherex_qr2 en el SIA generico devolvio 0 filas en las posiciones de
  prueba (WISE 0855 y la posicion de ejemplo de la doc del Cutout Tool). Puede ser
  que el nombre de coleccion sea otro, o que el servicio de IRSA estuviera saturado
  (vimos varios 502 Proxy Error durante las pruebas, probablemente por la carga del
  hackathon). Por eso este cliente intenta TAP primero y cae a SIA como respaldo.
- Las consultas ADQL con CONTAINS/POINT/CIRCLE sobre spherex.obscore dieron timeout
  en esta sesion (>60-90s), incluso sin filtro de posicion. Puede ser que la tabla
  no tenga indice espacial, o que el servidor estuviera lento. Si esto persiste,
  usar el Moving Object Search Tool (MOST) o el SPHEREx Data Explorer como
  alternativa, o contactar a IRSA User Support.

Esto es intencional: preferimos un backend honesto con fallback y timeouts claros
en vez de asumir un endpoint "mock" que luego falla en la demo.
"""

from __future__ import annotations

import csv
import io
import logging

import requests

logger = logging.getLogger(__name__)

TAP_SYNC_URL = "https://irsa.ipac.caltech.edu/TAP/sync"
SIA_URL = "https://irsa.ipac.caltech.edu/SIA"

# Nombres de coleccion a probar en el fallback SIA. Ajustar cuando se confirme
# el nombre real (ver docstring del modulo).
SIA_COLLECTIONS_TO_TRY = ["spherex_qr2", "spherex_qr3", "spherex_dr1"]

DEFAULT_TIMEOUT_S = 25


class SpherexSearchError(Exception):
    pass


def _parse_csv(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def query_spherex_tap(ra_deg: float, dec_deg: float, radius_deg: float, max_rows: int = 200) -> list[dict]:
    """Busca observaciones de SPHEREx cerca de (ra, dec) via TAP (spherex.obscore).

    Puede tardar o fallar si IRSA esta saturado; el llamador debe manejar
    SpherexSearchError y hacer fallback a query_spherex_sia si hace falta.
    """
    query = (
        f"SELECT TOP {max_rows} obs_collection, obs_id, s_ra, s_dec, t_min, t_max, "
        f"em_min, em_max, s_fov, access_url, access_format "
        f"FROM spherex.obscore "
        f"WHERE CONTAINS(POINT('ICRS', s_ra, s_dec), "
        f"CIRCLE('ICRS', {ra_deg}, {dec_deg}, {radius_deg})) = 1"
    )
    try:
        resp = requests.get(
            TAP_SYNC_URL,
            params={"QUERY": query, "FORMAT": "csv"},
            timeout=DEFAULT_TIMEOUT_S,
        )
        resp.raise_for_status()
        return _parse_csv(resp.text)
    except requests.RequestException as exc:
        logger.warning("TAP query a spherex.obscore fallo: %s", exc)
        raise SpherexSearchError(str(exc)) from exc


def query_spherex_sia(ra_deg: float, dec_deg: float, radius_deg: float, max_rows: int = 200) -> list[dict]:
    """Fallback usando el servicio generico SIA v2 de IRSA.

    Prueba varios nombres de COLLECTION (ver SIA_COLLECTIONS_TO_TRY) hasta que
    alguno devuelva filas.
    """
    rows: list[dict] = []
    for collection in SIA_COLLECTIONS_TO_TRY:
        params = [
            ("COLLECTION", collection),
            ("POS", f"circle {ra_deg} {dec_deg} {radius_deg}"),
            ("RESPONSEFORMAT", "CSV"),
            ("MAXREC", str(max_rows)),
        ]
        try:
            resp = requests.get(SIA_URL, params=params, timeout=DEFAULT_TIMEOUT_S)
            resp.raise_for_status()
            parsed = _parse_csv(resp.text)
            if parsed:
                rows.extend(parsed)
        except requests.RequestException as exc:
            logger.warning("SIA query con COLLECTION=%s fallo: %s", collection, exc)
    if not rows:
        raise SpherexSearchError(
            "SIA no devolvio filas para ninguna coleccion probada: "
            f"{SIA_COLLECTIONS_TO_TRY}. Verificar nombre de coleccion real."
        )
    return rows


def search_spherex(ra_deg: float, dec_deg: float, radius_deg: float = 0.05) -> list[dict]:
    """Punto de entrada unico: intenta TAP, si falla cae a SIA."""
    try:
        rows = query_spherex_tap(ra_deg, dec_deg, radius_deg)
        if rows:
            return rows
    except SpherexSearchError:
        pass
    return query_spherex_sia(ra_deg, dec_deg, radius_deg)

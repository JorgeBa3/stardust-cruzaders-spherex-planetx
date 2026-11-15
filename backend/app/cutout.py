"""Descarga recortes (cutouts) de SPHEREx y los convierte a PNG para el frontend.

El patron de URL de cutout esta CONFIRMADO en la documentacion oficial de IRSA
(https://irsa.ipac.caltech.edu/data/SPHEREx/docs/cutout_tool.html):

    curl -o cutout.fits "<access_url_del_fits>?center=<ra>,<dec>&size=<grados>"

Los FITS de SPHEREx son Multi-Extension (MEF): varias HDUs con distinta WCS
(imagen, varianza, flags, PSF, etc). Para el MVP tomamos la primera HDU con
datos de imagen 2D (normalmente la extension 1), no asumimos que siempre sea
la misma posicion sin verificar.
"""

from __future__ import annotations

import io
import logging

import numpy as np
import requests
from astropy.io import fits
from astropy.visualization import AsinhStretch, ZScaleInterval
from PIL import Image

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_S = 30


class CutoutError(Exception):
    pass


def fetch_cutout_fits_bytes(access_url: str, ra_deg: float, dec_deg: float, size_deg: float) -> bytes:
    try:
        resp = requests.get(
            access_url,
            params={"center": f"{ra_deg},{dec_deg}", "size": size_deg},
            timeout=DEFAULT_TIMEOUT_S,
        )
        resp.raise_for_status()
        return resp.content
    except requests.RequestException as exc:
        raise CutoutError(f"No se pudo descargar el cutout de {access_url}: {exc}") from exc


def _first_image_hdu(hdul: fits.HDUList) -> np.ndarray:
    for hdu in hdul:
        data = hdu.data
        if data is not None and getattr(data, "ndim", 0) == 2:
            return np.asarray(data, dtype=float)
    raise CutoutError("El FITS no tiene ninguna HDU con datos de imagen 2D.")


def array_to_png(data: np.ndarray, flip_vertical: bool = True) -> bytes:
    """Escala un array 2D (zscale + asinh) y lo guarda como PNG en escala de grises.

    Comun entre el pipeline real (FITS de IRSA) y el modo demo (demo_data.py),
    para que ambos se vean visualmente consistentes.
    """
    data = np.nan_to_num(np.asarray(data, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)

    vmin, vmax = ZScaleInterval().get_limits(data)
    if vmax <= vmin:
        vmax = vmin + 1.0
    scaled = np.clip((data - vmin) / (vmax - vmin), 0, 1)
    scaled = AsinhStretch()(scaled)

    img_8bit = (scaled * 255).astype(np.uint8)
    if flip_vertical:
        # FITS tiene origen abajo-izquierda; las imagenes se leen arriba-izquierda.
        img_8bit = np.flipud(img_8bit)

    image = Image.fromarray(img_8bit, mode="L")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def fits_bytes_to_png(fits_bytes: bytes) -> bytes:
    try:
        with fits.open(io.BytesIO(fits_bytes)) as hdul:
            data = _first_image_hdu(hdul)
    except OSError as exc:
        raise CutoutError(f"El contenido devuelto no es un FITS valido: {exc}") from exc

    return array_to_png(data)


def get_cutout_png(access_url: str, ra_deg: float, dec_deg: float, size_deg: float) -> bytes:
    fits_bytes = fetch_cutout_fits_bytes(access_url, ra_deg, dec_deg, size_deg)
    return fits_bytes_to_png(fits_bytes)

"""Modo demo offline: genera secuencias de imagenes SINTETICAS por objeto de
prueba para poder mostrar el flujo completo (play, blink) sin depender de que
IRSA responda en ese momento.

IMPORTANTE: esto NO es dato real de SPHEREx. Es una simulacion simple (un
"objeto" que se mueve o cambia de brillo sobre un fondo de estrellas falsas)
pensada solo para poder ensayar/demostrar la interfaz. El frontend debe dejar
esto claramente marcado como demo/simulado en todo momento. Antes de la
presentacion final, preferir siempre datos reales cacheados (ver PLAN.md,
seccion de riesgos) si IRSA ya esta estable.
"""

from __future__ import annotations

import hashlib

import numpy as np

from .cutout import array_to_png

N_EPOCHS = 6
IMAGE_SIZE = 96

# Que tipo de variacion simular por objeto, eligiendo lo que mejor representa
# el fenomeno real que ese objeto de prueba ilustra en el challenge.
MOTION_TARGET_KEYWORDS = ("barnard", "wise 0855")
VARIABLE_TARGET_KEYWORDS = ("rw aurigae", "r draconis")
BINARY_TARGET_KEYWORDS = ("epsilon indi",)


def _rng_for(target_name: str) -> np.random.Generator:
    seed = int(hashlib.sha256(target_name.encode("utf-8")).hexdigest()[:8], 16)
    return np.random.default_rng(seed)


def _gaussian_blob(size: int, cy: float, cx: float, amplitude: float, sigma: float = 2.0) -> np.ndarray:
    y, x = np.mgrid[0:size, 0:size]
    return amplitude * np.exp(-(((y - cy) ** 2 + (x - cx) ** 2) / (2 * sigma**2)))


def _background_stars(size: int, rng: np.random.Generator, n: int = 12) -> np.ndarray:
    img = np.zeros((size, size))
    for _ in range(n):
        cy, cx = rng.uniform(5, size - 5, size=2)
        amp = rng.uniform(20, 80)
        img += _gaussian_blob(size, cy, cx, amp, sigma=rng.uniform(1.2, 2.2))
    return img


def _kind_for(target_name: str) -> str:
    lowered = target_name.lower()
    if any(k in lowered for k in MOTION_TARGET_KEYWORDS):
        return "motion"
    if any(k in lowered for k in VARIABLE_TARGET_KEYWORDS):
        return "variable"
    if any(k in lowered for k in BINARY_TARGET_KEYWORDS):
        return "binary"
    return "static"


def synthetic_epoch_array(
    target_name: str, epoch_index: int, n_epochs: int = N_EPOCHS, size: int = IMAGE_SIZE
) -> np.ndarray:
    rng = _rng_for(target_name)
    image = _background_stars(size, rng)

    cy, cx = size / 2, size / 2
    t = epoch_index / max(n_epochs - 1, 1)
    kind = _kind_for(target_name)

    if kind == "motion":
        # Objeto que se desplaza en linea recta entre epocas (proper motion alto).
        dy, dx = size * 0.28, size * 0.22
        sy = cy - dy / 2 + dy * t
        sx = cx - dx / 2 + dx * t
        image += _gaussian_blob(size, sy, sx, amplitude=180, sigma=1.6)
    elif kind == "variable":
        # Brillo variable tipo Mira / variable joven.
        phase = 2 * np.pi * (epoch_index / n_epochs)
        amplitude = 90 + 110 * (0.5 + 0.5 * np.sin(phase))
        image += _gaussian_blob(size, cy, cx, amplitude=amplitude, sigma=1.8)
    elif kind == "binary":
        # Par de enanas marrones: separacion fija, un poco de orbita simulada.
        sep = 6 + 1.5 * np.sin(2 * np.pi * t)
        image += _gaussian_blob(size, cy, cx - sep / 2, amplitude=140, sigma=1.5)
        image += _gaussian_blob(size, cy, cx + sep / 2, amplitude=100, sigma=1.5)
    else:
        image += _gaussian_blob(size, cy, cx, amplitude=150, sigma=1.6)

    noise = rng.normal(0, 4, size=(size, size))
    return image + noise


def synthetic_epoch_png(target_name: str, epoch_index: int, n_epochs: int = N_EPOCHS) -> bytes:
    array = synthetic_epoch_array(target_name, epoch_index, n_epochs)
    return array_to_png(array, flip_vertical=False)


def demo_epochs_for(target_name: str, n_epochs: int = N_EPOCHS) -> list[dict]:
    # SPHEREx mapea el cielo completo cada ~6 meses; usamos ese espaciado en MJD
    # solo para que la tabla de epocas se vea realista.
    base_mjd = 61000.0
    spacing_days = 182.5
    epochs = []
    for i in range(n_epochs):
        epochs.append(
            {
                "obs_id": f"DEMO-{i + 1:02d}",
                "obs_collection": "demo_sintetico",
                "t_min_mjd": round(base_mjd + i * spacing_days, 2),
                "t_max_mjd": round(base_mjd + i * spacing_days + 0.01, 2),
                "em_min_m": None,
                "em_max_m": None,
                "s_fov_deg": None,
                "access_url": f"demo://{target_name}/{i}",
            }
        )
    return epochs

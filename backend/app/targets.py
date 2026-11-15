"""Objetos de prueba obligatorios del challenge "Planet X and SPHEREx".

Coordenadas J2000 en grados decimales. Fuentes:
- Barnard's Star, Epsilon Indi A, RW Aurigae: infobox de Wikipedia (Gaia DR3 / Hipparcos).
- WISE 0855: dado explícitamente por el texto del challenge.
- R Draconis: Hipparcos (HIP 81014), cruzado con la Wikipedia en sueco.

OJO:
- Barnard's Star tiene movimiento propio muy alto (~10.3"/año). Estas coordenadas
  son época ~2016 (Gaia DR2/DR3); para observaciones 2025-2026 el error introducido
  es de pocos arcsec, aceptable para centrar una búsqueda con FOV >= 0.02 deg,
  pero si hace falta precisión real, propagar el proper motion con astropy.
- Epsilon Indi B (Ba/Bb) NO tiene coordenadas propias confiables obtenidas en esta
  sesión: la literatura da separaciones contradictorias respecto a Epsilon Indi A
  (1500 AU en el paper de descubrimiento de 2003 vs. ~11600 AU según Gaia, que-
  equivale a ~0.9 grados de separación). Por ahora este preset apunta a
  Epsilon Indi A. ANTES DEL HACKATHON: confirmar en SIMBAD ("* eps Ind B") el
  offset real y corregir, o usar el Moving Object Search Tool (MOST) de IRSA.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    name: str
    ra_deg: float
    dec_deg: float
    note: str


PRESET_TARGETS: list[Target] = [
    Target(
        name="Barnard's Star",
        ra_deg=269.452077,
        dec_deg=4.693365,
        note="Estrella de movimiento propio muy alto (~10.3 arcsec/anio).",
    ),
    Target(
        name="Epsilon Indi B (placeholder = posicion de Epsilon Indi A)",
        ra_deg=330.840223,
        dec_deg=-56.785979,
        note="VERIFICAR offset real de la pareja de enanas marrones B antes del evento (ver SIMBAD '* eps Ind B').",
    ),
    Target(
        name="WISE 0855",
        ra_deg=133.795130,
        dec_deg=-7.245147,
        note="Enana marrona rapida. RA 08h55m10.831s Dec -07d14m42.53s (dado por el challenge).",
    ),
    Target(
        name="RW Aurigae",
        ra_deg=76.956068,
        dec_deg=30.401326,
        note="Estrella variable joven (RW Aur A).",
    ),
    Target(
        name="R Draconis",
        ra_deg=248.167583,
        dec_deg=66.754983,
        note="Variable Mira, periodo ~245.6 dias.",
    ),
]

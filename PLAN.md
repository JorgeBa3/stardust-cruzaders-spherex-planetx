# Plan — "Planet X and SPHEREx" (NASA Space Apps Challenge 2026)

Dificultad: **Advanced** · Temas: Astrophysics, Planets & Moons, Software
Página oficial: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/

## 1. El challenge en una frase

Construir una **web pública tipo "blink comparator"**: el usuario ingresa coordenadas (RA/Dec), y la herramienta muestra una secuencia temporal de imágenes del cielo de la misión **SPHEREx** (102 bandas infrarrojas, todo el cielo cada ~6 meses desde mayo 2025) para que se noten a simple vista objetos que se mueven o varían (asteroides, cometas, enanas marrones, estrellas variables).

Es el mismo concepto que **backyardworlds.org** / **WiseView** (ciencia ciudadana con WISE), pero para SPHEREx.

## 2. Objetivos de los jueces (qué nos hace ganar)

Space Apps evalúa típicamente: **Impact, Creativity, Validity, Relevance, Presentation**.

- **Relevance**: cumplir literalmente lo pedido — input RA/Dec → "video" de imágenes a través del tiempo.
- **Validity**: usar datos reales de IRSA (no mockups), que funcione en vivo con los 5 objetos de prueba.
- **Creativity**: manejo inteligente de las 102 bandas (sumar por array, espectros al vuelo), blink/resta entre épocas.
- **Impact**: enmarcarlo como herramienta de ciencia ciudadana real (siguiente backyardworlds.org).
- **Presentation**: demo en vivo + fallback cacheado si la API de IRSA falla el día de la demo.

## 3. Objetos de prueba obligatorios

| Objeto | Nota |
|---|---|
| Barnard's Star | estrella de movimiento propio alto |
| Epsilon Indi B | par de enanas marrones orbitando una estrella |
| WISE 0855 | enana marrón rápida — RA 08h55m10.831s, Dec −7°14′42.53″ |
| RW Aurigae | estrella variable |
| R Draconis | estrella variable |

El MVP **tiene que verse bien con estos 5** antes que con cualquier otra cosa.

## 4. Fuentes de datos (confirmadas desde la página de Resources del challenge)

- **IRSA (NASA/IPAC Infrared Science Archive) — SPHEREx**: https://irsa.ipac.caltech.edu/Missions/spherex.html
  - **Cutout Tool**: extrae recortes espaciales de los FITS multi-extensión de SPHEREx → esto es el corazón técnico del proyecto.
  - **Mosaic Tool**: mosaicos multi-banda personalizados.
  - **Moving Object Search Tool (MOST)**: dado un objeto/órbita, encuentra qué imágenes de SPHEREx lo cubrieron y en qué época — muy útil para no tener que buscar manualmente las épocas disponibles.
  - **Source Discovery Tool**: detección de fuentes sin prior de posición.
  - **Spectrophotometry Tool**: extrae espectros por forced photometry (la "extra kudos" del challenge).
  - **HiPS Cubes**: si IRSA expone SPHEREx como HiPS, se puede usar directo en **Aladin Lite** sin servidor propio — revisar esto primero, puede ahorrar muchísimo tiempo de desarrollo.
  - **Cloud Data Access**: SPHEREx también en AWS S3 (útil si queremos bajar volumen directo).
  - Releases: QR2/QR3 ya disponibles; DR1 llega en noviembre 2026 — usar QR2/QR3 como fuente principal.
- **SPHEREx Tutorial Notebooks (Python)**: https://caltech-ipac.github.io/irsa-tutorials/spherex/ — notebooks de ejemplo para cutouts, PSF, mosaicos, HiPS, Source Discovery. **Leer esto primero, literalmente da el código base para el backend.**
- **WiseView** (modelo/inspiración explícita del challenge): http://byw.tools/wiseview — estudiar su UX de blink/overlay.
- **Gaia DR3**: https://archive.stsci.edu/missions-and-data/gaia — para overlay opcional de catálogo.
- **Aladin Lite (CDS)**: sugerido en el challenge para mostrar/mapear datos astronómicos en el navegador.
- **Astropy**: sugerido para manejo de FITS/WCS.

## 5. Arquitectura propuesta

```
[Usuario] → [Frontend: Next.js/React + Aladin Lite]
                 │  (RA/Dec, banda, rango de fechas)
                 ▼
        [Backend: Python FastAPI]
                 │  proxy + cache + conversión FITS→PNG
                 ▼
        [IRSA: Cutout Tool / MOST / HiPS]
```

- **Frontend**: Next.js (o incluso HTML+JS simple si el equipo es chico) + **Aladin Lite** embebido para exploración de cielo, overlay de catálogos (Gaia/WISE) y, si hay HiPS de SPHEREx, para mostrar las épocas directo.
- **Backend**: Python/FastAPI — natural porque las tutorial notebooks de IRSA ya están en Python (astropy, astroquery). Responsabilidades:
  - Dado RA/Dec (+ FOV), consultar **MOST** o el índice de observaciones para listar épocas disponibles.
  - Pedir cutouts por época/banda al **Cutout Tool**.
  - Convertir FITS → PNG/JPEG (zscale/asinh stretch) con astropy + Pillow/numpy, cacheando en disco.
  - Endpoint para sumar bandas por array (6 arrays) y para diff/resta entre épocas.
- **Cache**: cache en disco simple (hackathon-grade) para los 5 objetos de prueba precalculados — es el fallback si IRSA está lento/caído durante la demo.
- **Deploy**: frontend en Vercel; backend en Render/Fly.io (o todo junto si falta tiempo).

## 6. Flujo funcional (MVP)

1. Usuario ingresa RA/Dec, o elige uno de los 5 objetos de prueba de una lista rápida.
2. Front llama al backend → backend resuelve qué épocas/observaciones de SPHEREx cubren ese punto (MOST o equivalente).
3. Backend pide los cutouts FITS de cada época (banda agregada por array, para empezar simple) y los convierte a imagen.
4. Front muestra la secuencia como "mini video" con: play/pause, slider de tiempo, blink entre dos épocas, resta de imágenes.
5. (Nice to have) selector de banda/array individual, overlay Gaia/WISE vía Aladin, generación de espectro al vuelo, FOV ajustable, coords en la URL (`?ra=...&dec=...`), flags de contaminación visibles.

## 7. Roadmap (hackathon ~48h)

- **Día 0 (antes del evento)**
  - Leer las SPHEREx Tutorial Notebooks completas (cutouts + HiPS + source discovery).
  - Confirmar si existe HiPS público de SPHEREx usable en Aladin Lite directo (decide si el backend es imprescindible o solo un proxy liviano).
  - Decidir stack final y armar roles del equipo (frontend, backend/datos, demo/pitch).
  - Repo skeleton + acceso de prueba a Cutout Tool/MOST con WISE 0855.

- **Bloque 1 (h0–h6): pipeline de datos mínimo**
  - End-to-end con un solo objeto (WISE 0855): coords → cutouts de 2+ épocas → PNG servido por el backend.

- **Bloque 2 (h6–h16): UI base**
  - Input de coordenadas, lista de objetos de prueba, visor con reproducción de secuencia de imágenes.

- **Bloque 3 (h16–h28): diferenciadores**
  - Blink/diff entre épocas, selector de banda/array, FOV ajustable, overlay Gaia/WISE con Aladin Lite, coords en querystring.

- **Bloque 4 (h28–h36): robustez + pulido**
  - Metadata/contamination flags visibles, manejo de errores de API, cache pre-calculada de los 5 objetos de prueba (fallback offline), deploy público.

- **Bloque 5 (h36–h44): pitch**
  - Video demo, slides, README con storytelling tipo "el próximo backyardworlds.org", probar los 5 objetos en vivo.

- **Buffer (h44–h48)**: QA final y submission.

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| API de IRSA lenta/caída durante la demo | Pre-cachear resultados de los 5 objetos de prueba antes del día de la demo |
| 102 bandas es demasiado para mostrar bien | Empezar agregando por los 6 arrays del detector, no por banda individual |
| CORS llamando IRSA desde el browser | Backend como proxy/cache, nunca llamar IRSA directo desde el frontend |
| Poco tiempo para FITS→imagen desde cero | Reusar directamente el código de las SPHEREx Tutorial Notebooks (cutouts/PSF) |
| HiPS de SPHEREx no existe o no es usable en Aladin | Fallback: Cutout Tool + conversión propia FITS→PNG |

## 9. Próximos pasos inmediatos

1. Crear repo (monorepo simple: `/frontend`, `/backend`).
2. Correr las SPHEREx Tutorial Notebooks localmente con WISE 0855 para validar acceso a datos.
3. Decidir equipo y roles.
4. Confirmar disponibilidad de HiPS de SPHEREx (define si Aladin Lite puede cargar las épocas directo o si todo pasa por el backend).
5. Armar el pipeline mínimo (Bloque 1) antes de tocar UI.

## 10. Referencias

- Challenge: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- IRSA SPHEREx: https://irsa.ipac.caltech.edu/Missions/spherex.html
- SPHEREx Tutorial Notebooks: https://caltech-ipac.github.io/irsa-tutorials/spherex/
- WiseView (inspiración): http://byw.tools/wiseview
- Gaia DR3: https://archive.stsci.edu/missions-and-data/gaia
- Backyard Worlds (proyecto de ciencia ciudadana análogo): https://backyardworlds.org

"""Backend FastAPI para "Planet X and SPHEREx".

Endpoints:
  GET /health
  GET /api/targets                                  -> objetos de prueba del challenge
  GET /api/search?ra=&dec=&radius=                   -> lista de observaciones/epocas
  GET /api/cutout?access_url=&ra=&dec=&size=          -> PNG del recorte

Correr en local:
  cd backend
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from . import cutout, demo_data, irsa_client, targets

app = FastAPI(title="Planet X and SPHEREx API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: abierto. Restringir antes de un deploy publico real.
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/targets")
def get_targets():
    return [
        {"name": t.name, "ra_deg": t.ra_deg, "dec_deg": t.dec_deg, "note": t.note}
        for t in targets.PRESET_TARGETS
    ]


@app.get("/api/search")
def search(
    ra: float = Query(..., description="Right Ascension en grados decimales (ICRS)"),
    dec: float = Query(..., description="Declination en grados decimales (ICRS)"),
    radius: float = Query(0.05, description="Radio de busqueda en grados"),
    source: str = Query("live", pattern="^(live|demo)$", description="'live' consulta IRSA; 'demo' usa datos sinteticos offline"),
    target: str | None = Query(None, description="Nombre exacto del preset (obligatorio si source=demo)"),
):
    if source == "demo":
        if not target:
            raise HTTPException(status_code=400, detail="Falta 'target' para source=demo")
        epochs = demo_data.demo_epochs_for(target)
        return {"count": len(epochs), "epochs": epochs, "demo": True}

    try:
        rows = irsa_client.search_spherex(ra, dec, radius)
    except irsa_client.SpherexSearchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    epochs = []
    for row in rows:
        access_url = row.get("access_url")
        if not access_url:
            continue
        epochs.append(
            {
                "obs_id": row.get("obs_id"),
                "obs_collection": row.get("obs_collection"),
                "t_min_mjd": row.get("t_min"),
                "t_max_mjd": row.get("t_max"),
                "em_min_m": row.get("em_min"),
                "em_max_m": row.get("em_max"),
                "s_fov_deg": row.get("s_fov"),
                "access_url": access_url,
            }
        )
    epochs.sort(key=lambda e: e["t_min_mjd"] or "")
    return {"count": len(epochs), "epochs": epochs, "demo": False}


@app.get("/api/cutout")
def get_cutout(
    ra: float = Query(...),
    dec: float = Query(...),
    size: float = Query(0.02, description="Tamano del recorte en grados"),
    access_url: str | None = Query(None, description="access_url devuelto por /api/search (requerido si source=live)"),
    source: str = Query("live", pattern="^(live|demo)$"),
    target: str | None = Query(None, description="Nombre exacto del preset (requerido si source=demo)"),
    epoch: int | None = Query(None, description="indice de epoca (requerido si source=demo)"),
):
    if source == "demo":
        if target is None or epoch is None:
            raise HTTPException(status_code=400, detail="Faltan 'target' y/o 'epoch' para source=demo")
        png_bytes = demo_data.synthetic_epoch_png(target, epoch)
        return Response(content=png_bytes, media_type="image/png")

    if not access_url:
        raise HTTPException(status_code=400, detail="Falta 'access_url' para source=live")
    try:
        png_bytes = cutout.get_cutout_png(access_url, ra, dec, size)
    except cutout.CutoutError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return Response(content=png_bytes, media_type="image/png")

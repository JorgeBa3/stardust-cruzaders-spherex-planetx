# Planet X and SPHEREx

Skeleton funcional para el challenge NASA Space Apps 2026 "Planet X and SPHEREx".
Ver [PLAN.md](PLAN.md) para el plan completo (roadmap, riesgos, referencias).

**Nota sobre uso de IA:** parte del codigo y la documentacion de este proyecto
se desarrollo con asistencia de herramientas de inteligencia artificial
(generacion de codigo asistida). Las decisiones de diseno, validacion de datos
y revision final fueron hechas por el equipo.

## Estructura

```
backend/   FastAPI: busca observaciones de SPHEREx en IRSA y sirve cutouts como PNG
frontend/  Sitio estatico (sin build step): input RA/Dec, visor de secuencia, blink, Aladin Lite
```

## Arrancar el backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Probar: http://localhost:8000/api/targets y http://localhost:8000/health

## Arrancar el frontend

No necesita build. Solo servirlo como estatico (abrir `index.html` directo puede
tener problemas de CORS con `fetch`, mejor servir con un server simple):

```bash
cd frontend
python -m http.server 5500
```

Abrir http://localhost:5500 — el frontend asume que el backend esta en
`http://localhost:8000` (configurable seteando `window.BACKEND_URL` antes de
cargar `app.js`, o editando la constante en `app.js`).

## Estado actual / que falta (ver PLAN.md seccion 9)

- [x] Backend con endpoints `/api/targets`, `/api/search`, `/api/cutout`.
- [x] Frontend minimo: preset de objetos de prueba, slider de epocas, play/pause, blink A/B, panel Aladin Lite de contexto.
- [ ] **CRITICO — validar antes del hackathon**: el nombre real de la coleccion
      SPHEREx en el servicio SIA de IRSA. Durante el desarrollo, consultas con
      `COLLECTION=spherex_qr2` devolvieron 0 filas (puede ser el nombre
      incorrecto o que IRSA estuviera saturado por el trafico del hackathon).
      Ver los comentarios en `backend/app/irsa_client.py`.
- [ ] Confirmar las coordenadas reales de Epsilon Indi B (ver `backend/app/targets.py`).
- [ ] Agregar seleccion de banda / suma por array (los 102 canales -> 6 arrays).
- [ ] Resta entre epocas (diff), overlay Gaia/WISE, coords en la URL.
- [ ] Cache en disco de los 5 objetos de prueba como fallback offline para la demo.

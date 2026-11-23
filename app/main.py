"""Quiniela de pronosticos Miss Universo: cada quien arma su apuesta (Top
30 -> Top 12 -> Top 5 -> Top 3 -> ganadora) y se compara contra el
resultado real para armar un ranking de quien le pego mas.
"""
import json
import os
import secrets
import uuid

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import db, logic
from app.data import CUPOS, NIVELES, ORIGEN

APP_DIR = os.path.dirname(__file__)
ADMIN_KEY = (os.environ.get("ADMIN_KEY") or secrets.token_urlsafe(8)).strip()

app = FastAPI(title="Quiniela Miss Universo")
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()
    print("=" * 60)
    print("Link de admin (guardalo para vos, no lo compartas):")
    print(f"  /admin?key={ADMIN_KEY}")
    print("=" * 60)


def _candidatas_json() -> str:
    candidatas = db.listar_candidatas()
    return json.dumps(
        [{"id": c["id"], "pais": c["pais"], "nombre": c["nombre"], "continente": c["continente"]}
         for c in candidatas]
    )


def _wizard_contexto(request: Request, *, es_admin: bool, nombre_previo: str = "",
                      picks_previos: dict | None = None, ganadora_previa: int | None = None,
                      error: str | None = None) -> dict:
    return {
        "request": request,
        "es_admin": es_admin,
        "admin_key": request.query_params.get("key", "") if es_admin else "",
        "nombre_previo": nombre_previo,
        "picks_previos_json": json.dumps(picks_previos or {}),
        "ganadora_previa": ganadora_previa or 0,
        "candidatas_json": _candidatas_json(),
        "niveles_json": json.dumps(NIVELES),
        "cupos": CUPOS,
        "cupos_json": json.dumps(CUPOS),
        "origen_json": json.dumps(ORIGEN),
        "error": error,
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if db.apuestas_cerradas():
        return templates.TemplateResponse(request, "cerradas.html", {})

    token = request.cookies.get("pid")
    participante = db.get_participante_por_cookie(token) if token else None
    picks_previos = db.obtener_picks(participante["id"]) if participante else None
    nombre_previo = participante["nombre"] if participante else ""
    ganadora_previa = participante["ganadora_id"] if participante else None

    resp = templates.TemplateResponse(
        request,
        "apostar.html",
        _wizard_contexto(
            request, es_admin=False, nombre_previo=nombre_previo,
            picks_previos=picks_previos, ganadora_previa=ganadora_previa,
        ),
    )
    return resp


@app.post("/apostar")
async def apostar(request: Request):
    if db.apuestas_cerradas():
        return RedirectResponse("/", status_code=303)

    form = await request.form()
    nombre = (form.get("nombre") or "").strip()
    picks_por_nivel = {
        nivel: [int(v) for k, v in form.multi_items() if k == nivel] for nivel in NIVELES
    }
    ganadora_raw = form.get("ganadora")
    ganadora_id = int(ganadora_raw) if ganadora_raw else None

    if not nombre:
        error = "Che, nos falta tu nombre."
    else:
        error = logic.validar_apuesta(picks_por_nivel, ganadora_id)

    if error:
        token = request.cookies.get("pid")
        participante = db.get_participante_por_cookie(token) if token else None
        return templates.TemplateResponse(
            request,
            "apostar.html",
            _wizard_contexto(
                request, es_admin=False, nombre_previo=nombre,
                picks_previos=picks_por_nivel, ganadora_previa=ganadora_id, error=error,
            ),
            status_code=400,
        )

    token = request.cookies.get("pid") or str(uuid.uuid4())
    token = db.guardar_apuesta(
        cookie_token=token, nombre=nombre, picks_por_nivel=picks_por_nivel,
        ganadora_id=ganadora_id,
    )
    resp = RedirectResponse("/gracias", status_code=303)
    resp.set_cookie("pid", token, max_age=60 * 60 * 24 * 120)
    return resp


@app.get("/gracias", response_class=HTMLResponse)
def gracias(request: Request):
    return templates.TemplateResponse(request, "gracias.html", {})


@app.get("/ranking", response_class=HTMLResponse)
def ranking(request: Request):
    tabla = logic.calcular_tabla_posiciones()
    real = db.get_resultado_real()
    hay_resultado = bool(db.obtener_picks(real["id"]).get("top30"))
    return templates.TemplateResponse(
        request, "ranking.html", {"tabla": tabla, "hay_resultado": hay_resultado}
    )


# ---------------------------------------------------------------------------
# Admin: no hay login de verdad, es un link secreto con una key. Para un
# jueguito entre amigos por WhatsApp alcanza y sobra (no lo compartas).
# ---------------------------------------------------------------------------


def _chequear_key(key: str) -> bool:
    return secrets.compare_digest(key or "", ADMIN_KEY)


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, key: str = ""):
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)

    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "key": key,
            "cerradas": db.apuestas_cerradas(),
            "cantidad_participantes": db.contar_participantes(),
            "participantes": db.listar_participantes(),
        },
    )


@app.post("/admin/toggle-apuestas")
def admin_toggle_apuestas(key: str = Form(...)):
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)
    db.set_apuestas_cerradas(not db.apuestas_cerradas())
    return RedirectResponse(f"/admin?key={key}", status_code=303)


@app.get("/admin/resultado", response_class=HTMLResponse)
def admin_resultado_form(request: Request, key: str = ""):
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)

    real = db.get_resultado_real()
    picks_previos = db.obtener_picks(real["id"])
    return templates.TemplateResponse(
        request,
        "apostar.html",
        _wizard_contexto(
            request, es_admin=True, picks_previos=picks_previos,
            ganadora_previa=real["ganadora_id"],
        ),
    )


@app.post("/admin/resultado")
async def admin_resultado_guardar(request: Request):
    form = await request.form()
    key = form.get("key", "")
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)

    picks_por_nivel = {
        nivel: [int(v) for k, v in form.multi_items() if k == nivel] for nivel in NIVELES
    }
    ganadora_raw = form.get("ganadora")
    ganadora_id = int(ganadora_raw) if ganadora_raw else None

    error = logic.validar_apuesta(picks_por_nivel, ganadora_id)
    if error:
        return templates.TemplateResponse(
            request,
            "apostar.html",
            _wizard_contexto(
                request, es_admin=True, picks_previos=picks_por_nivel,
                ganadora_previa=ganadora_id, error=error,
            ),
            status_code=400,
        )

    db.guardar_apuesta(
        cookie_token=None, nombre=db.NOMBRE_RESULTADO_REAL, picks_por_nivel=picks_por_nivel,
        ganadora_id=ganadora_id, es_resultado_real=True,
    )
    return RedirectResponse(f"/ranking", status_code=303)


@app.post("/admin/reset")
def admin_reset(key: str = Form(...)):
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)
    db.reset_todo()
    return RedirectResponse(f"/admin?key={key}", status_code=303)

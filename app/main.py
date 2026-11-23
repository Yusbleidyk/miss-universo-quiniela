"""Quiniela de pronosticos Miss Universo: cada quien arma su apuesta (Top
30 -> Top 12 -> Top 5 -> Top 3 -> ganadora) y se compara contra el
resultado real para armar un ranking de quien le pego mas.
"""
import json
import os
import secrets
import uuid
from urllib.parse import quote

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


@app.get("/apuesta/{participante_id}", response_class=HTMLResponse)
def ver_apuesta(request: Request, participante_id: int):
    participante = db.get_participante_por_id(participante_id)
    if not participante or participante["es_resultado_real"]:
        return HTMLResponse("<h1>404 - no existe esa apuesta</h1>", status_code=404)

    detalle = db.obtener_picks_detallados(participante_id)
    ganadora = db.get_participante_por_id(participante_id)["ganadora_id"]
    return templates.TemplateResponse(
        request,
        "detalle_apuesta.html",
        {
            "nombre": participante["nombre"],
            "detalle": detalle,
            "ganadora_id": ganadora,
        },
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


NIVELES_RESULTADO = NIVELES + ["ganadora"]


@app.get("/admin/resultado", response_class=HTMLResponse)
def admin_resultado_dashboard(request: Request, key: str = ""):
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)

    real = db.get_resultado_real()
    picks_reales = db.obtener_picks(real["id"])

    filas = []
    habilitado = True
    for nivel in NIVELES:
        cantidad = len(picks_reales.get(nivel, []))
        cargado = cantidad == CUPOS[nivel]
        filas.append({"nivel": nivel, "cargado": cargado, "cantidad": cantidad, "habilitado": habilitado})
        habilitado = cargado

    ganadora = None
    if real["ganadora_id"]:
        todas = {c["id"]: c for c in db.listar_candidatas()}
        ganadora = todas.get(real["ganadora_id"])
    filas.append({
        "nivel": "ganadora", "cargado": real["ganadora_id"] is not None,
        "cantidad": 1 if real["ganadora_id"] else 0, "habilitado": habilitado,
        "ganadora_nombre": f"{ganadora['pais']} - {ganadora['nombre']}" if ganadora else None,
    })

    return templates.TemplateResponse(
        request, "admin_resultado.html", {"key": key, "filas": filas}
    )


@app.get("/admin/resultado/{nivel}", response_class=HTMLResponse)
def admin_resultado_nivel_form(request: Request, nivel: str, key: str = "", error: str = ""):
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)
    if nivel not in NIVELES_RESULTADO:
        return HTMLResponse("<h1>404</h1>", status_code=404)

    real = db.get_resultado_real()
    picks_reales = db.obtener_picks(real["id"])
    todas = {c["id"]: c for c in db.listar_candidatas()}

    if nivel == "ganadora":
        candidatas_disponibles = [todas[cid] for cid in picks_reales.get("top3", []) if cid in todas]
        seleccion_previa = [real["ganadora_id"]] if real["ganadora_id"] else []
        cupo = 1
        tipo_input = "radio"
    else:
        origen = ORIGEN[nivel]
        if origen is None:
            candidatas_disponibles = list(db.listar_candidatas())
        else:
            candidatas_disponibles = [todas[cid] for cid in picks_reales.get(origen, []) if cid in todas]
        seleccion_previa = picks_reales.get(nivel, [])
        cupo = CUPOS[nivel]
        tipo_input = "checkbox"

    return templates.TemplateResponse(
        request,
        "admin_nivel.html",
        {
            "key": key,
            "nivel": nivel,
            "cupo": cupo,
            "tipo_input": tipo_input,
            "candidatas": candidatas_disponibles,
            "seleccion_previa": set(seleccion_previa),
            "error": error,
        },
    )


@app.post("/admin/resultado/{nivel}")
async def admin_resultado_nivel_guardar(request: Request, nivel: str):
    form = await request.form()
    key = form.get("key", "")
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)
    if nivel not in NIVELES_RESULTADO:
        return HTMLResponse("<h1>404</h1>", status_code=404)

    ids = [int(v) for k, v in form.multi_items() if k == "candidata"]

    if nivel == "ganadora":
        ganadora_id = ids[0] if ids else None
        error = logic.validar_ganadora_real(ganadora_id)
        if not error:
            db.guardar_resultado_ganadora(ganadora_id)
    else:
        error = logic.validar_nivel_real(nivel, ids)
        if not error:
            db.guardar_resultado_nivel(nivel, ids)

    if error:
        return RedirectResponse(
            f"/admin/resultado/{nivel}?key={key}&error={quote(error)}", status_code=303
        )
    return RedirectResponse(f"/admin/resultado?key={key}", status_code=303)


@app.post("/admin/reset")
def admin_reset(key: str = Form(...)):
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)
    db.reset_todo()
    return RedirectResponse(f"/admin?key={key}", status_code=303)

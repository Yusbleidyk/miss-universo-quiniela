"""Quiniela Miss Universo: app FastAPI chiquita para votar por WhatsApp."""
import os
import secrets
import uuid
from collections import defaultdict

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db, logic
from app.data import CUOTAS_GRUPOS

APP_DIR = os.path.dirname(__file__)
ADMIN_KEY = (os.environ.get("ADMIN_KEY") or secrets.token_urlsafe(8)).strip()

app = FastAPI(title="Quiniela Miss Universo")
app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()
    print("=" * 60)
    print(f"Link de admin (guardalo para vos, no lo compartas):")
    print(f"  /admin?key={ADMIN_KEY}")
    print("=" * 60)


def get_votante_id(request: Request) -> str:
    return request.cookies.get("vid") or str(uuid.uuid4())


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    ronda = db.get_ronda_actual()
    votante_id = get_votante_id(request)

    if ronda == "done":
        ganadora = db.candidatas_en_etapa("ganadora")
        resp = templates.TemplateResponse(
            request, "done.html", {"ganadora": ganadora[0] if ganadora else None}
        )
        resp.set_cookie("vid", votante_id, max_age=60 * 60 * 24 * 60)
        return resp

    ya_voto = db.ya_voto(ronda, votante_id)
    candidatas = db.candidatas_en_etapa(ronda)

    grupos = None
    if ronda == "groups":
        grupos = defaultdict(list)
        for c in candidatas:
            grupos[c["continente"]].append(c)
        grupos = dict(sorted(grupos.items()))

    resp = templates.TemplateResponse(
        request,
        "vote.html",
        {
            "ronda": ronda,
            "nombre_ronda": logic.NOMBRES_RONDA[ronda],
            "ya_voto": ya_voto,
            "candidatas": candidatas,
            "grupos": grupos,
            "cuotas_grupos": CUOTAS_GRUPOS,
            "cupo_total": logic.cupo_total(ronda),
            "votantes": db.contar_votantes_unicos(ronda),
        },
    )
    resp.set_cookie("vid", votante_id, max_age=60 * 60 * 24 * 60)
    return resp


@app.post("/vote")
async def vote(request: Request):
    ronda = db.get_ronda_actual()
    votante_id = get_votante_id(request)

    if ronda == "done" or db.ya_voto(ronda, votante_id):
        return RedirectResponse("/", status_code=303)

    form = await request.form()
    seleccionadas = [int(v) for k, v in form.multi_items() if k == "candidata"]

    error = _validar_seleccion(ronda, seleccionadas)
    if error:
        candidatas = db.candidatas_en_etapa(ronda)
        grupos = None
        if ronda == "groups":
            grupos = defaultdict(list)
            for c in candidatas:
                grupos[c["continente"]].append(c)
            grupos = dict(sorted(grupos.items()))
        return templates.TemplateResponse(
            request,
            "vote.html",
            {
                "ronda": ronda,
                "nombre_ronda": logic.NOMBRES_RONDA[ronda],
                "ya_voto": False,
                "candidatas": candidatas,
                "grupos": grupos,
                "cuotas_grupos": CUOTAS_GRUPOS,
                "cupo_total": logic.cupo_total(ronda),
                "votantes": db.contar_votantes_unicos(ronda),
                "error": error,
            },
            status_code=400,
        )

    db.registrar_votos(ronda, votante_id, seleccionadas)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("vid", votante_id, max_age=60 * 60 * 24 * 60)
    return resp


def _validar_seleccion(ronda: str, seleccionadas: list[int]) -> str | None:
    """Valida que se haya elegido exactamente el cupo correcto. None = OK."""
    candidatas = {c["id"]: c for c in db.candidatas_en_etapa(ronda)}
    for cid in seleccionadas:
        if cid not in candidatas:
            return "Che, alguna seleccion no es valida. Probá de nuevo."

    if ronda == "groups":
        por_continente = defaultdict(int)
        for cid in seleccionadas:
            por_continente[candidatas[cid]["continente"]] += 1
        for continente, cupo in CUOTAS_GRUPOS.items():
            if por_continente.get(continente, 0) != cupo:
                return f"En {continente} tenés que elegir exactamente {cupo}."
        return None

    cupo = logic.cupo_total(ronda)
    if len(seleccionadas) != cupo:
        return f"Tenés que elegir exactamente {cupo} candidatas."
    return None


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

    ronda = db.get_ronda_actual()
    tally = db.tally_ronda(ronda) if ronda != "done" else []
    ganadora = db.candidatas_en_etapa("ganadora")

    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "key": key,
            "ronda": ronda,
            "nombre_ronda": logic.NOMBRES_RONDA[ronda],
            "tally": tally,
            "votantes": db.contar_votantes_unicos(ronda) if ronda != "done" else 0,
            "ganadora": ganadora[0] if ganadora else None,
        },
    )


@app.post("/admin/advance")
def admin_advance(key: str = Form(...)):
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)
    logic.cerrar_ronda_y_avanzar()
    return RedirectResponse(f"/admin?key={key}", status_code=303)


@app.post("/admin/reset")
def admin_reset(key: str = Form(...)):
    if not _chequear_key(key):
        return HTMLResponse("<h1>401 - key invalida</h1>", status_code=401)
    db.reset_todo()
    return RedirectResponse(f"/admin?key={key}", status_code=303)

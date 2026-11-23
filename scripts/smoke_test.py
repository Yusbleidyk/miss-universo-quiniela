"""Smoke test manual: simula una vuelta completa de la quiniela contra un
servidor corriendo en localhost. No es parte de la app, es solo para QA
rapida durante el desarrollo. Borrar o ignorar en produccion.
"""
import sqlite3
import sys
import urllib.parse
import urllib.request
import http.cookiejar

sys.path.insert(0, ".")
from app.data import CUOTAS_GRUPOS, CUPO_RONDA  # noqa: E402 (reusa la fuente de verdad)

BASE = "http://127.0.0.1:8123"
ADMIN_KEY = "test123"
DB_PATH = "quiniela.db"

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def get(path):
    return opener.open(BASE + path, timeout=10)


def post_form(path, pairs):
    body = urllib.parse.urlencode(pairs, doseq=True).encode()
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    return opener.open(req, timeout=10)


def candidatos_para_votar(ronda):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    filas = conn.execute(
        "SELECT id, continente FROM candidatas WHERE etapa = ?", (ronda,)
    ).fetchall()
    conn.close()
    return filas


def elegir_ids(ronda, filas):
    if ronda == "groups":
        por_cont = {}
        for f in filas:
            por_cont.setdefault(f["continente"], []).append(f["id"])
        ids = []
        for cont, cupo in CUOTAS_GRUPOS.items():
            ids += por_cont.get(cont, [])[:cupo]
        return ids
    cupo = CUPO_RONDA[ronda]
    return [f["id"] for f in filas][:cupo]


def votar_ronda(ronda):
    filas = candidatos_para_votar(ronda)
    ids = elegir_ids(ronda, filas)
    r = post_form("/vote", [("candidata", i) for i in ids])
    print(f"  POST /vote (ronda={ronda}, {len(ids)} elegidas) -> {r.status}")
    assert r.status == 200


def avanzar():
    r = post_form("/admin/advance", [("key", ADMIN_KEY)])
    print(f"  POST /admin/advance -> {r.status}")
    assert r.status == 200


rondas = ["groups", "top30", "top12", "top5", "top3"]
for ronda in rondas:
    r = get("/")
    print(f"GET / -> {r.status}")
    assert r.status == 200
    votar_ronda(ronda)
    avanzar()

r = get("/")
html = r.read().decode()
print(f"GET / final -> {r.status}")
assert "ganadora" in html.lower() or "quiniela" in html.lower()
print("\nTODO OK: la quiniela corrio de punta a punta sin romperse.")

"""Smoke test de casos limite: reset, voto invalido, voto doble. No es
parte de la app, solo QA manual durante desarrollo."""
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

sys.path.insert(0, ".")
from app.data import CUOTAS_GRUPOS  # noqa: E402 (reusa la fuente de verdad)

BASE = "http://127.0.0.1:8123"
ADMIN_KEY = "test123"
DB_PATH = "quiniela.db"


def nueva_sesion():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def post_form(opener, path, pairs):
    body = urllib.parse.urlencode(pairs, doseq=True).encode()
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    return opener.open(req, timeout=10)


def get(opener, path):
    return opener.open(BASE + path, timeout=10)


opener = nueva_sesion()

print("1) Reset total...")
r = post_form(opener, "/admin/reset", [("key", ADMIN_KEY)])
print("   status:", r.status)

print("2) Votar mal a proposito (solo 2 candidatas en vez de 30)...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
filas = conn.execute("SELECT id FROM candidatas WHERE etapa='groups' LIMIT 2").fetchall()
conn.close()
try:
    post_form(opener, "/vote", [("candidata", f["id"]) for f in filas])
    raise AssertionError("se esperaba un 400 y no paso")
except urllib.error.HTTPError as e:
    html = e.read().decode()
    print("   status:", e.code, "| contiene mensaje de error:", "exactamente" in html)
    assert e.code == 400

print("3) Votar bien (30 justas)...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
filas = conn.execute("SELECT id, continente FROM candidatas WHERE etapa='groups'").fetchall()
conn.close()
por_cont = {}
for f in filas:
    por_cont.setdefault(f["continente"], []).append(f["id"])
ids = []
for cont, cupo in CUOTAS_GRUPOS.items():
    ids += por_cont.get(cont, [])[:cupo]
r = post_form(opener, "/vote", [("candidata", i) for i in ids])
print("   status:", r.status)
assert r.status == 200

print("4) Intentar votar de nuevo con la MISMA sesion (debe decir 'ya votaste')...")
r = get(opener, "/")
html = r.read().decode()
print("   status:", r.status, "| dice 'ya votaste':", "Ya votaste" in html)
assert "Ya votaste" in html

print("\nTODO OK: validaciones y anti doble-voto funcionando.")

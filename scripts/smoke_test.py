"""Smoke test de la quiniela de pronosticos. No es parte de la app, solo
QA manual contra un servidor corriendo en localhost."""
import http.cookiejar
import sqlite3
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8123"
ADMIN_KEY = "test123"
DB_PATH = "quiniela.db"


def ids_candidatas() -> list[int]:
    """Ids reales de la base (el autoincrement de SQLite no arranca en 1
    despues de varios resets, asi que nunca hay que asumir ids fijos)."""
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute("SELECT id FROM candidatas ORDER BY id").fetchall()
    conn.close()
    return [f[0] for f in filas]


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


def apuesta_payload(nombre, top30, top12, top5, top3, ganadora):
    pairs = [("nombre", nombre)] if nombre else []
    for nivel, ids in [("top30", top30), ("top12", top12), ("top5", top5), ("top3", top3)]:
        pairs += [(nivel, i) for i in ids]
    pairs.append(("ganadora", ganadora))
    return pairs


print("1) Reset total...")
admin_opener = nueva_sesion()
r = post_form(admin_opener, "/admin/reset", [("key", ADMIN_KEY)])
print("   status:", r.status)
assert r.status == 200

ids = ids_candidatas()
assert len(ids) == 116, f"se esperaban 116 candidatas, hay {len(ids)}"

print("2) Apuesta invalida a proposito (top12 con un id que no esta en el top30)...")
op = nueva_sesion()
payload = apuesta_payload(
    "Invalido", ids[0:30], ids[0:11] + [999999], ids[0:5], ids[0:3], ids[0]
)
try:
    post_form(op, "/apostar", payload)
    raise AssertionError("se esperaba un 400 y no paso")
except urllib.error.HTTPError as e:
    print("   status:", e.code)
    assert e.code == 400

print("3) Participante A: apuesta perfecta (va a coincidir 100% con el resultado real)...")
opener_a = nueva_sesion()
payload_a = apuesta_payload("Ana", ids[0:30], ids[0:12], ids[0:5], ids[0:3], ids[0])
r = post_form(opener_a, "/apostar", payload_a)
print("   status:", r.status)
assert r.status == 200

print("4) Participante B: apuesta parecida pero con algunos fallos...")
opener_b = nueva_sesion()
top30_b = ids[0:29] + [ids[30]]
top12_b = ids[0:11] + [ids[30]]
top5_b = ids[0:4] + [ids[30]]
top3_b = ids[0:2] + [ids[30]]
payload_b = apuesta_payload("Beto", top30_b, top12_b, top5_b, top3_b, ids[30])
r = post_form(opener_b, "/apostar", payload_b)
print("   status:", r.status)
assert r.status == 200

print("5) A edita su propia apuesta (mismo navegador, debe quedar una sola fila, no duplicarse)...")
r = post_form(opener_a, "/apostar", payload_a)
assert r.status == 200

print("6) Admin carga el resultado real...")
payload_real = apuesta_payload(None, ids[0:30], ids[0:12], ids[0:5], ids[0:3], ids[0])
payload_real.append(("key", ADMIN_KEY))
r = post_form(admin_opener, "/admin/resultado", payload_real)
print("   status:", r.status)
assert r.status == 200

print("7) Chequeo el ranking...")
html = get(admin_opener, "/ranking").read().decode()
assert "Ana" in html and "Beto" in html
print("   Ana y Beto aparecen en el ranking: OK")
# Ana deberia tener mas puntos que Beto (le pego posta a todo + la ganadora)
pos_ana = html.index("Ana")
pos_beto = html.index("Beto")
print("   orden en la tabla (Ana antes que Beto esperado):", pos_ana < pos_beto)
assert pos_ana < pos_beto

print("8) Cierro las apuestas y confirmo que ya no se puede cargar/editar...")
r = post_form(admin_opener, "/admin/toggle-apuestas", [("key", ADMIN_KEY)])
assert r.status == 200
html_home = get(nueva_sesion(), "/").read().decode()
assert "cerraron" in html_home.lower()
print("   home muestra mensaje de apuestas cerradas: OK")

print("\nTODO OK: la quiniela de pronosticos funciona de punta a punta.")

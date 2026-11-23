"""Reset manual rapido + check visual del HTML de la ronda groups."""
import urllib.request
import urllib.parse

body = urllib.parse.urlencode({"key": "test123"}).encode()
req = urllib.request.Request("http://127.0.0.1:8123/admin/reset", data=body, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
urllib.request.urlopen(req, timeout=10)
print("reset ok")

html = urllib.request.urlopen("http://127.0.0.1:8123/", timeout=10).read().decode()
print("--- primeras apariciones de continentes en el HTML ---")
for linea in html.splitlines():
    if "<h3" in linea or "Elegí exactamente" in linea:
        print(linea.strip())

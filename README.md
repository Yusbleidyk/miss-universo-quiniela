# Quiniela Miss Universo

Jueguito para votar entre amigos por WhatsApp: quien avanza de la fase de
grupos (por continente) al Top 30, despues al Top 12, Top 5, Top 2 y
finalmente la ganadora.

No tiene nada que ver con el resultado real del concurso -- es solo para
divertirse con el grupo.

## Como funciona

- Hay UN SOLO link publico (la home `/`) que mandas por WhatsApp. Siempre
  muestra la ronda que este abierta en ese momento.
- Cada persona vota una vez por ronda (se identifica por una cookie en su
  navegador, no hace falta cuenta ni login).
- Vos (el admin) tenes un link secreto `/admin?key=...` donde ves los votos
  en vivo y apretas un boton para cerrar la ronda actual y pasar a la
  siguiente. Las candidatas mas votadas de cada ronda avanzan solas.
- Rondas: grupos (por continente) -> Top 30 -> Top 12 -> Top 5 -> Top 2 ->
  ganadora.

## Correrlo en tu compu (para probar)

```powershell
cd miss-universo-quiniela
uv venv                      # si no lo hiciste ya
uv pip install -r requirements.txt --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
set ADMIN_KEY=ponele-cualquier-clave-larga
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Abrí `http://localhost:8000/` para votar y `http://localhost:8000/admin?key=ponele-cualquier-clave-larga`
para el panel admin. Esto NO sirve para compartir por WhatsApp todavia
porque solo funciona en tu compu -- para eso segui el paso de abajo.

## Subirlo para que el link funcione desde cualquier celular (Render.com, gratis)

No hace falta tarjeta de credito para el plan free de Render.

1. Cre a tu cuenta gratis en https://render.com (podes entrar con tu cuenta
   de GitHub).
2. Subi esta carpeta a un repo de GitHub (puede ser privado):
   ```powershell
   cd miss-universo-quiniela
   git init
   git add .
   git commit -m "Quiniela Miss Universo"
   ```
   Despues creá un repo vacio en GitHub y seguí las instrucciones que te da
   para conectarlo (`git remote add origin ...` y `git push`).
3. En Render: "New +" -> "Blueprint" -> elegi tu repo. Render va a leer el
   archivo `render.yaml` que ya esta en esta carpeta y va a configurar todo
   solo (incluida una `ADMIN_KEY` generada al azar).
4. Cuando termine el deploy (1-2 minutos), Render te da una URL tipo
   `https://quiniela-miss-universo.onrender.com`. Ese es el link que mandas
   por WhatsApp.
5. Para ver tu link de admin: en el dashboard de Render, entra al servicio
   -> pestaña "Environment" -> copiá el valor de `ADMIN_KEY` -> andá a
   `https://tu-url.onrender.com/admin?key=ESE_VALOR`. Guardatelo, no lo
   compartas en el grupo.

### Cosas a tener en cuenta del plan free de Render

- El servicio se "duerme" si nadie lo visita en 15 minutos, y tarda unos
  30-50 segundos en despertar la primera vez que alguien entra despues de
  eso. Es normal, no esta roto.
- Los votos se guardan en un archivo (SQLite) dentro del propio servicio.
  Mientras no hagas un redeploy (no vuelvas a hacer `git push`), los votos
  quedan ahi tranquilos. Si necesitas hacer un cambio de codigo a mitad de
  la votacion, avisale al grupo que los votos de esa ronda se van a
  reiniciar.

## Panel admin: cerrar una ronda

1. Entra a `/admin?key=TU_KEY`.
2. Mira la barra de votos en vivo por candidata.
3. Cuando quieras cortar la votacion de esa ronda, apreta "Cerrar ronda y
   avanzar". Las mas votadas pasan solas a la siguiente ronda (si hay
   empate justo en el limite, desempata por orden alfabetico de pais -- es
   un jueguito entre amigos, no hace falta mas precision que esa).
4. Mandale de nuevo el mismo link de siempre al grupo para que voten la
   ronda nueva.

## Estructura del proyecto

```
app/
  main.py        rutas de FastAPI (/, /vote, /admin, /admin/advance, /admin/reset)
  db.py          acceso a SQLite (sin ORM, es chiquito)
  logic.py       calculo de quien avanza en cada ronda
  data.py        lista de candidatas Miss Universe 2026 + cuotas por continente/ronda
  templates/     HTML con Jinja2 + Tailwind (via CDN)
scripts/
  smoke_test*.py pruebas manuales de punta a punta (no se usan en produccion)
```

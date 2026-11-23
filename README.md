# Quiniela Miss Universo

Quiniela de pronosticos para jugar entre amigos por WhatsApp: cada quien
arma SU PROPIA apuesta completa (Top 30 -> Top 12 -> Top 5 -> Top 3 ->
ganadora) y despues, cuando sale el resultado real del concurso, se arma
un ranking de quien le pego mas.

No tiene nada que ver con votar en vivo quien avanza -- es un juego de
pronosticos tipo "quiniela deportiva", cada uno apuesta antes de saber el
resultado.

Usa las candidatas de Miss Universe 2026 (116 paises, final el 24/11/2026
en San Juan, Puerto Rico) y calca el formato oficial de la noche final
(edicion 2025, la mas reciente confirmada): Top 30 -> Top 12 (traje de
bano) -> Top 5 (vestido de noche) -> Top 3 (preguntas) -> ganadora
(pregunta final).

## Como funciona

- Hay UN SOLO link publico (la home `/`) que mandas por WhatsApp.
- Cada persona entra, pone su nombre y arma su apuesta en un wizard paso a
  paso: elige 30 candidatas, despues (DE ESAS 30) elige 12, despues (DE
  ESAS 12) elige 5, despues (DE ESAS 5) elige 3, y por ultimo elige su
  ganadora entre esas 3. Cada nivel tiene que salir del anterior -- no se
  puede predecir que alguien llega al Top 12 si no la pusiste en tu Top 30.
- Mientras las apuestas esten abiertas, cada quien puede volver a entrar
  al mismo link y editar su apuesta (se identifica por una cookie, no hace
  falta cuenta).
- Vos (el admin) cerras las apuestas antes de que arranque el show real
  desde tu panel `/admin?key=...`, para que nadie pueda cambiar su apuesta
  despues de ver como va el concurso.
- Despues del show, cargas el resultado REAL (el mismo wizard, pero para
  vos) desde `/admin/resultado?key=...`.
- Cualquiera puede entrar a `/ranking` (mismo link para todos) y ver quien
  le pego mas: 1 punto por cada acierto en cada nivel (Top 30, Top 12,
  Top 5, Top 3) + 10 puntos extra si le pego a la ganadora exacta. Desde
  ahi tambien se puede ver el detalle completo de la apuesta de cada
  persona (que eligio en cada nivel) con el link "ver" de cada fila.

## Correrlo en tu compu (para probar)

```powershell
cd miss-universo-quiniela
uv venv                      # si no lo hiciste ya
uv pip install -r requirements.txt --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
set ADMIN_KEY=ponele-cualquier-clave-larga
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Abrí `http://localhost:8000/` para armar una apuesta y
`http://localhost:8000/admin?key=ponele-cualquier-clave-larga` para el
panel admin. Esto NO sirve para compartir por WhatsApp todavia porque solo
funciona en tu compu -- para eso segui el paso de abajo.

## Subirlo para que el link funcione desde cualquier celular (Render.com, gratis)

No hace falta tarjeta de credito para el plan free de Render.

1. Cre a tu cuenta gratis en https://render.com (podes entrar con tu cuenta
   de GitHub).
2. Subi esta carpeta a un repo de GitHub (puede ser privado).
3. En Render: "New +" -> "Blueprint" -> elegi tu repo. Render va a leer el
   archivo `render.yaml` que ya esta en esta carpeta y va a configurar todo
   solo (incluida una `ADMIN_KEY` generada al azar).
4. Cuando termine el deploy (1-2 minutos), Render te da una URL. Ese es el
   link que mandas por WhatsApp.
5. Tu link de admin: en el dashboard de Render, entra al servicio ->
   pestaña "Environment" -> copia el valor de `ADMIN_KEY` -> anda a
   `https://tu-url.onrender.com/admin?key=ESE_VALOR`. Guardatelo, no lo
   compartas en el grupo.

### Cosas a tener en cuenta del plan free de Render

- El servicio se "duerme" si nadie lo visita en 15 minutos, y tarda unos
  30-50 segundos en despertar la primera vez que alguien entra despues de
  eso. Es normal, no esta roto.
- Las apuestas se guardan en un archivo (SQLite) dentro del propio
  servicio. Mientras no hagas un redeploy (no vuelvas a hacer `git push`),
  quedan ahi tranquilas.

## Flujo recomendado para el dia del evento

1. Cargar las apuestas de todos ANTES de que arranque la transmision.
2. Entrar al admin y apretar "Cerrar apuestas" justo antes de que arranque
   el show (para que nadie edite su apuesta viendo como va el concurso en
   vivo).
3. Despues de la final, buscar el resultado oficial (Wikipedia o
   missuniverse.com) y cargarlo en `/admin/resultado?key=...`.
4. Compartir el link `/ranking` para que todos vean quien gano la quiniela.

## Estructura del proyecto

```
app/
  main.py        rutas de FastAPI (/, /apostar, /ranking, /admin, /admin/resultado)
  db.py          acceso a SQLite (sin ORM, es chiquito)
  logic.py       validacion de apuestas (anidacion) + calculo del ranking
  data.py        lista de candidatas Miss Universe 2026 + niveles/cupos
  templates/     HTML con Jinja2 + Tailwind (via CDN), wizard en JS vanilla
scripts/
  smoke_test.py  prueba manual de punta a punta (no se usa en produccion)
```

"""Capa de acceso a datos: SQLite con sqlite3 puro (sin ORM, no hace falta).

Modelo nuevo (quiniela de pronosticos, no votacion colectiva):
- candidatas: el catalogo de las 116 candidatas (fijo).
- participantes: cada persona que arma su apuesta. Se identifica por una
  cookie (cookie_token). Una fila especial con es_resultado_real=1 guarda
  el resultado REAL del concurso, cargado por el admin -- se trata igual
  que un participante mas para poder reusar el mismo codigo de guardado y
  de comparacion de puntaje.
- picks: que candidatas eligio cada participante (o la realidad) en cada
  nivel (top30/top12/top5/top3).
- estado: un flag global para cerrar las apuestas antes de que arranque el
  show real.
"""
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from app.data import CANDIDATAS, NIVELES

DB_PATH = Path(__file__).parent.parent / "quiniela.db"
NOMBRE_RESULTADO_REAL = "RESULTADO REAL"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Crea las tablas si no existen y siembra candidatas + fila de resultado real."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS candidatas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pais TEXT NOT NULL,
                nombre TEXT NOT NULL,
                continente TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS participantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cookie_token TEXT UNIQUE,
                es_resultado_real INTEGER NOT NULL DEFAULT 0,
                ganadora_id INTEGER REFERENCES candidatas(id),
                creado_en TEXT NOT NULL DEFAULT (datetime('now')),
                actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participante_id INTEGER NOT NULL REFERENCES participantes(id),
                nivel TEXT NOT NULL,
                candidata_id INTEGER NOT NULL REFERENCES candidatas(id)
            );

            CREATE TABLE IF NOT EXISTS estado (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                apuestas_cerradas INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        if conn.execute("SELECT COUNT(*) AS n FROM candidatas").fetchone()["n"] == 0:
            conn.executemany(
                "INSERT INTO candidatas (pais, nombre, continente) VALUES (?, ?, ?)",
                CANDIDATAS,
            )

        # Migracion defensiva: si la tabla "estado" venia de una version vieja
        # de la app (sin la columna apuestas_cerradas), se la agregamos en vez
        # de romper. Asi no hace falta borrar la base de datos al actualizar.
        columnas_estado = {fila["name"] for fila in conn.execute("PRAGMA table_info(estado)")}
        if "apuestas_cerradas" not in columnas_estado:
            conn.execute("ALTER TABLE estado ADD COLUMN apuestas_cerradas INTEGER NOT NULL DEFAULT 0")

        if conn.execute("SELECT COUNT(*) AS n FROM estado").fetchone()["n"] == 0:
            conn.execute("INSERT INTO estado (id, apuestas_cerradas) VALUES (1, 0)")
        existe_real = conn.execute(
            "SELECT 1 FROM participantes WHERE es_resultado_real = 1"
        ).fetchone()
        if not existe_real:
            conn.execute(
                "INSERT INTO participantes (nombre, cookie_token, es_resultado_real) "
                "VALUES (?, NULL, 1)",
                (NOMBRE_RESULTADO_REAL,),
            )


def listar_candidatas() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM candidatas ORDER BY continente, pais"
        ).fetchall()


def apuestas_cerradas() -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT apuestas_cerradas FROM estado WHERE id = 1").fetchone()
        return bool(row["apuestas_cerradas"])


def set_apuestas_cerradas(valor: bool) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE estado SET apuestas_cerradas = ? WHERE id = 1", (int(valor),))


def get_participante_por_cookie(token: str) -> sqlite3.Row | None:
    if not token:
        return None
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM participantes WHERE cookie_token = ?", (token,)
        ).fetchone()


def get_resultado_real() -> sqlite3.Row:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM participantes WHERE es_resultado_real = 1"
        ).fetchone()


def get_participante_por_id(participante_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM participantes WHERE id = ?", (participante_id,)
        ).fetchone()


def obtener_picks(participante_id: int) -> dict[str, list[int]]:
    with get_conn() as conn:
        filas = conn.execute(
            "SELECT nivel, candidata_id FROM picks WHERE participante_id = ?",
            (participante_id,),
        ).fetchall()
    picks: dict[str, list[int]] = {nivel: [] for nivel in NIVELES}
    for fila in filas:
        picks.setdefault(fila["nivel"], []).append(fila["candidata_id"])
    return picks


def obtener_picks_detallados(participante_id: int) -> dict[str, list[sqlite3.Row]]:
    """Igual que obtener_picks pero trae pais/nombre de cada candidata (para mostrar)."""
    with get_conn() as conn:
        filas = conn.execute(
            """
            SELECT p.nivel, c.id, c.pais, c.nombre
            FROM picks p JOIN candidatas c ON c.id = p.candidata_id
            WHERE p.participante_id = ?
            ORDER BY c.pais
            """,
            (participante_id,),
        ).fetchall()
    detalle: dict[str, list[sqlite3.Row]] = {nivel: [] for nivel in NIVELES}
    for fila in filas:
        detalle.setdefault(fila["nivel"], []).append(fila)
    return detalle


def guardar_apuesta(
    *, cookie_token: str | None, nombre: str, picks_por_nivel: dict[str, list[int]],
    ganadora_id: int, es_resultado_real: bool = False,
) -> str:
    """Crea o actualiza (upsert) la apuesta de un participante. Devuelve su cookie_token."""
    with get_conn() as conn:
        if es_resultado_real:
            fila = conn.execute(
                "SELECT id FROM participantes WHERE es_resultado_real = 1"
            ).fetchone()
            participante_id = fila["id"]
            conn.execute(
                "UPDATE participantes SET ganadora_id = ?, actualizado_en = datetime('now') "
                "WHERE id = ?",
                (ganadora_id, participante_id),
            )
        else:
            fila = conn.execute(
                "SELECT id FROM participantes WHERE cookie_token = ?", (cookie_token,)
            ).fetchone()
            if fila:
                participante_id = fila["id"]
                conn.execute(
                    "UPDATE participantes SET nombre = ?, ganadora_id = ?, "
                    "actualizado_en = datetime('now') WHERE id = ?",
                    (nombre, ganadora_id, participante_id),
                )
            else:
                cookie_token = cookie_token or str(uuid.uuid4())
                cur = conn.execute(
                    "INSERT INTO participantes (nombre, cookie_token, ganadora_id) "
                    "VALUES (?, ?, ?)",
                    (nombre, cookie_token, ganadora_id),
                )
                participante_id = cur.lastrowid

        conn.execute("DELETE FROM picks WHERE participante_id = ?", (participante_id,))
        filas_nuevas = [
            (participante_id, nivel, cid)
            for nivel, ids in picks_por_nivel.items()
            for cid in ids
        ]
        conn.executemany(
            "INSERT INTO picks (participante_id, nivel, candidata_id) VALUES (?, ?, ?)",
            filas_nuevas,
        )
    return cookie_token


def listar_participantes() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM participantes WHERE es_resultado_real = 0 ORDER BY nombre"
        ).fetchall()


def contar_participantes() -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM participantes WHERE es_resultado_real = 0"
        ).fetchone()
        return row["n"]


def reset_todo() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM picks")
        conn.execute("DELETE FROM participantes")
        conn.execute(
            "INSERT INTO participantes (nombre, cookie_token, es_resultado_real) "
            "VALUES (?, NULL, 1)",
            (NOMBRE_RESULTADO_REAL,),
        )
        conn.execute("UPDATE estado SET apuestas_cerradas = 0 WHERE id = 1")

"""Capa de acceso a datos: SQLite con sqlite3 puro (sin ORM, no hace falta)."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.data import CANDIDATAS

DB_PATH = Path(__file__).parent.parent / "quiniela.db"


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
    """Crea las tablas si no existen y siembra las candidatas la primera vez."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS candidatas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pais TEXT NOT NULL,
                nombre TEXT NOT NULL,
                continente TEXT NOT NULL,
                etapa TEXT NOT NULL DEFAULT 'groups'
            );

            CREATE TABLE IF NOT EXISTS votos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ronda TEXT NOT NULL,
                candidata_id INTEGER NOT NULL REFERENCES candidatas(id),
                votante_id TEXT NOT NULL,
                creado_en TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS estado (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                ronda_actual TEXT NOT NULL DEFAULT 'groups'
            );
            """
        )
        row = conn.execute("SELECT COUNT(*) AS n FROM candidatas").fetchone()
        if row["n"] == 0:
            conn.executemany(
                "INSERT INTO candidatas (pais, nombre, continente, etapa) "
                "VALUES (?, ?, ?, 'groups')",
                CANDIDATAS,
            )
        if conn.execute("SELECT COUNT(*) AS n FROM estado").fetchone()["n"] == 0:
            conn.execute("INSERT INTO estado (id, ronda_actual) VALUES (1, 'groups')")


def get_ronda_actual() -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT ronda_actual FROM estado WHERE id = 1").fetchone()
        return row["ronda_actual"]


def set_ronda_actual(ronda: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE estado SET ronda_actual = ? WHERE id = 1", (ronda,))


def candidatas_en_etapa(etapa: str) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM candidatas WHERE etapa = ? ORDER BY continente, pais",
            (etapa,),
        ).fetchall()


def ya_voto(ronda: str, votante_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM votos WHERE ronda = ? AND votante_id = ? LIMIT 1",
            (ronda, votante_id),
        ).fetchone()
        return row is not None


def registrar_votos(ronda: str, votante_id: str, candidata_ids: list[int]) -> None:
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO votos (ronda, candidata_id, votante_id) VALUES (?, ?, ?)",
            [(ronda, cid, votante_id) for cid in candidata_ids],
        )


def contar_votantes_unicos(ronda: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(DISTINCT votante_id) AS n FROM votos WHERE ronda = ?",
            (ronda,),
        ).fetchone()
        return row["n"]


def tally_ronda(ronda: str) -> list[sqlite3.Row]:
    """Devuelve candidatas de la etapa `ronda` ordenadas por votos (desc)."""
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT c.*, COALESCE(v.votos, 0) AS votos
            FROM candidatas c
            LEFT JOIN (
                SELECT candidata_id, COUNT(*) AS votos
                FROM votos WHERE ronda = ?
                GROUP BY candidata_id
            ) v ON v.candidata_id = c.id
            WHERE c.etapa = ?
            ORDER BY votos DESC, c.pais ASC
            """,
            (ronda, ronda),
        ).fetchall()


def actualizar_etapas(ganadoras_ids: list[int], perdedoras_ids: list[int], etapa_siguiente: str) -> None:
    with get_conn() as conn:
        conn.executemany(
            "UPDATE candidatas SET etapa = ? WHERE id = ?",
            [(etapa_siguiente, cid) for cid in ganadoras_ids],
        )
        conn.executemany(
            "UPDATE candidatas SET etapa = ? WHERE id = ?",
            [("eliminada", cid) for cid in perdedoras_ids],
        )


def reset_todo() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM votos")
        conn.execute("DELETE FROM candidatas")
        conn.executemany(
            "INSERT INTO candidatas (pais, nombre, continente, etapa) "
            "VALUES (?, ?, ?, 'groups')",
            CANDIDATAS,
        )
        conn.execute("UPDATE estado SET ronda_actual = 'groups' WHERE id = 1")

"""Capa de acceso a datos con SQLAlchemy Core (sin ORM, no hace falta).

Usa Postgres en produccion (Render) y SQLite en desarrollo local, con el
MISMO codigo -- SQLAlchemy se encarga de las diferencias de sintaxis entre
los dos motores. Esto es critico: los Web Services gratis de Render
borran el filesystem local cada vez que el servicio "se duerme" por
inactividad (15 min), asi que SQLite local en el propio contenedor NO
sirve para guardar datos reales -- hace falta una base de datos aparte
que persista (Postgres).

Modelo (quiniela de pronosticos, no votacion colectiva):
- candidatas: el catalogo de las 116 candidatas (fijo).
- participantes: cada persona que arma su apuesta. Se identifica por una
  cookie (cookie_token). Una fila especial con es_resultado_real=True
  guarda el resultado REAL del concurso, cargado por el admin -- se trata
  igual que un participante mas para reusar el mismo codigo de guardado y
  de comparacion de puntaje.
- picks: que candidatas eligio cada participante (o la realidad) en cada
  nivel (top30/top12/top5/top3).
- estado: un flag global para cerrar las apuestas antes de que arranque
  el show real.
"""
import os
import uuid

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String,
    Table, create_engine, delete, func, insert, select, update,
)

from app.data import CANDIDATAS, NIVELES

NOMBRE_RESULTADO_REAL = "RESULTADO REAL"


def _url_sqlalchemy(url: str) -> str:
    """Render da DATABASE_URL como postgres://... ; SQLAlchemy+psycopg3
    necesita el prefijo postgresql+psycopg://..."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = _url_sqlalchemy(os.environ.get("DATABASE_URL", "sqlite:///quiniela.db"))
engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

candidatas = Table(
    "candidatas", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pais", String, nullable=False),
    Column("nombre", String, nullable=False),
    Column("continente", String, nullable=False),
)

participantes = Table(
    "participantes", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre", String, nullable=False),
    Column("cookie_token", String, unique=True, nullable=True),
    Column("es_resultado_real", Boolean, nullable=False, default=False),
    Column("ganadora_id", Integer, ForeignKey("candidatas.id"), nullable=True),
    Column("creado_en", DateTime(timezone=True), server_default=func.now()),
    Column("actualizado_en", DateTime(timezone=True), server_default=func.now()),
)

picks = Table(
    "picks", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("participante_id", Integer, ForeignKey("participantes.id"), nullable=False),
    Column("nivel", String, nullable=False),
    Column("candidata_id", Integer, ForeignKey("candidatas.id"), nullable=False),
)

estado = Table(
    "estado", metadata,
    Column("id", Integer, primary_key=True),
    Column("apuestas_cerradas", Boolean, nullable=False, default=False),
)


def init_db() -> None:
    """Crea las tablas si no existen y siembra candidatas + fila de resultado real."""
    metadata.create_all(engine)
    with engine.begin() as conn:
        if conn.execute(select(func.count()).select_from(candidatas)).scalar() == 0:
            conn.execute(
                insert(candidatas),
                [{"pais": p, "nombre": n, "continente": c} for p, n, c in CANDIDATAS],
            )
        if conn.execute(select(func.count()).select_from(estado)).scalar() == 0:
            conn.execute(insert(estado).values(id=1, apuestas_cerradas=False))
        existe_real = conn.execute(
            select(participantes.c.id).where(participantes.c.es_resultado_real.is_(True))
        ).first()
        if not existe_real:
            conn.execute(
                insert(participantes).values(
                    nombre=NOMBRE_RESULTADO_REAL, cookie_token=None, es_resultado_real=True
                )
            )


def listar_candidatas():
    with engine.connect() as conn:
        return conn.execute(
            select(candidatas).order_by(candidatas.c.continente, candidatas.c.pais)
        ).mappings().all()


def apuestas_cerradas() -> bool:
    with engine.connect() as conn:
        return bool(
            conn.execute(select(estado.c.apuestas_cerradas).where(estado.c.id == 1)).scalar()
        )


def set_apuestas_cerradas(valor: bool) -> None:
    with engine.begin() as conn:
        conn.execute(update(estado).where(estado.c.id == 1).values(apuestas_cerradas=valor))


def get_participante_por_cookie(token: str | None):
    if not token:
        return None
    with engine.connect() as conn:
        return conn.execute(
            select(participantes).where(participantes.c.cookie_token == token)
        ).mappings().first()


def get_participante_por_id(participante_id: int):
    with engine.connect() as conn:
        return conn.execute(
            select(participantes).where(participantes.c.id == participante_id)
        ).mappings().first()


def get_resultado_real():
    with engine.connect() as conn:
        return conn.execute(
            select(participantes).where(participantes.c.es_resultado_real.is_(True))
        ).mappings().first()


def obtener_picks(participante_id: int) -> dict[str, list[int]]:
    with engine.connect() as conn:
        filas = conn.execute(
            select(picks.c.nivel, picks.c.candidata_id)
            .where(picks.c.participante_id == participante_id)
        ).mappings().all()
    resultado: dict[str, list[int]] = {nivel: [] for nivel in NIVELES}
    for fila in filas:
        resultado.setdefault(fila["nivel"], []).append(fila["candidata_id"])
    return resultado


def obtener_picks_detallados(participante_id: int) -> dict[str, list]:
    """Igual que obtener_picks pero trae pais/nombre de cada candidata (para mostrar)."""
    with engine.connect() as conn:
        filas = conn.execute(
            select(picks.c.nivel, candidatas.c.id, candidatas.c.pais, candidatas.c.nombre)
            .select_from(picks.join(candidatas, candidatas.c.id == picks.c.candidata_id))
            .where(picks.c.participante_id == participante_id)
            .order_by(candidatas.c.pais)
        ).mappings().all()
    detalle: dict[str, list] = {nivel: [] for nivel in NIVELES}
    for fila in filas:
        detalle.setdefault(fila["nivel"], []).append(fila)
    return detalle


def guardar_apuesta(
    *, cookie_token: str | None, nombre: str, picks_por_nivel: dict[str, list[int]],
    ganadora_id: int, es_resultado_real: bool = False,
) -> str:
    """Crea o actualiza (upsert) la apuesta de un participante. Devuelve su cookie_token."""
    with engine.begin() as conn:
        if es_resultado_real:
            participante_id = conn.execute(
                select(participantes.c.id).where(participantes.c.es_resultado_real.is_(True))
            ).scalar_one()
            conn.execute(
                update(participantes)
                .where(participantes.c.id == participante_id)
                .values(ganadora_id=ganadora_id, actualizado_en=func.now())
            )
        else:
            fila = conn.execute(
                select(participantes.c.id).where(participantes.c.cookie_token == cookie_token)
            ).first()
            if fila:
                participante_id = fila[0]
                conn.execute(
                    update(participantes)
                    .where(participantes.c.id == participante_id)
                    .values(nombre=nombre, ganadora_id=ganadora_id, actualizado_en=func.now())
                )
            else:
                cookie_token = cookie_token or str(uuid.uuid4())
                participante_id = conn.execute(
                    insert(participantes)
                    .values(nombre=nombre, cookie_token=cookie_token, ganadora_id=ganadora_id)
                    .returning(participantes.c.id)
                ).scalar_one()

        conn.execute(delete(picks).where(picks.c.participante_id == participante_id))
        filas_nuevas = [
            {"participante_id": participante_id, "nivel": nivel, "candidata_id": cid}
            for nivel, ids in picks_por_nivel.items()
            for cid in ids
        ]
        if filas_nuevas:
            conn.execute(insert(picks), filas_nuevas)
    return cookie_token


def listar_participantes():
    with engine.connect() as conn:
        return conn.execute(
            select(participantes)
            .where(participantes.c.es_resultado_real.is_(False))
            .order_by(participantes.c.nombre)
        ).mappings().all()


def contar_participantes() -> int:
    with engine.connect() as conn:
        return conn.execute(
            select(func.count()).select_from(participantes)
            .where(participantes.c.es_resultado_real.is_(False))
        ).scalar()


def reset_todo() -> None:
    with engine.begin() as conn:
        conn.execute(delete(picks))
        conn.execute(delete(participantes))
        conn.execute(
            insert(participantes).values(
                nombre=NOMBRE_RESULTADO_REAL, cookie_token=None, es_resultado_real=True
            )
        )
        conn.execute(update(estado).where(estado.c.id == 1).values(apuestas_cerradas=False))

"""Logica para cerrar una ronda y calcular quienes avanzan a la siguiente."""
from app import db
from app.data import CUPO_RONDA, ORDEN_RONDAS


def siguiente_ronda(ronda: str) -> str:
    idx = ORDEN_RONDAS.index(ronda)
    return ORDEN_RONDAS[idx + 1]


def cerrar_ronda_y_avanzar() -> str:
    """Cierra la ronda actual, promueve a las mas votadas y devuelve la ronda nueva.

    Todas las rondas (incluida "groups") usan el mismo criterio: las
    `CUPO_RONDA[ronda]` candidatas con mas votos avanzan, el resto queda
    eliminada. El concurso real tampoco reparte cupos por continente para
    el Top 30 -- es puro puntaje entre todas juntas.
    """
    ronda = db.get_ronda_actual()
    if ronda == "done":
        return ronda  # ya terminamos, no hay nada para cerrar

    etapa_siguiente = siguiente_ronda(ronda)
    filas = db.tally_ronda(ronda)
    cupo = CUPO_RONDA[ronda]
    ganadoras_ids = [c["id"] for c in filas[:cupo]]
    perdedoras_ids = [c["id"] for c in filas[cupo:]]

    # Cuando esta ronda era la ultima antes de "done", su ganadora es LA
    # ganadora final (no importa como se llame la ronda).
    etapa_destino = "ganadora" if etapa_siguiente == "done" else etapa_siguiente
    db.actualizar_etapas(ganadoras_ids, perdedoras_ids, etapa_destino)
    db.set_ronda_actual(etapa_siguiente)
    return etapa_siguiente


def cupo_total(ronda: str) -> int:
    """Cupo total de candidatas que avanzan en esta ronda (para la UI)."""
    return CUPO_RONDA.get(ronda, 0)


NOMBRES_RONDA = {
    "groups": "Preliminar - elegi el Top 30",
    "top30": "Top 30 - Ronda de traje de bano",
    "top12": "Top 12 - Ronda de vestido de noche",
    "top5": "Top 5 - Ronda de preguntas",
    "top3": "Top 3 - Pregunta final",
    "done": "\U0001f451 Tenemos ganadora",
}

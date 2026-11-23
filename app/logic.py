"""Logica para cerrar una ronda y calcular quienes avanzan a la siguiente."""
from app import db
from app.data import CUOTAS_GRUPOS, CUPO_RONDA, ORDEN_RONDAS


def siguiente_ronda(ronda: str) -> str:
    idx = ORDEN_RONDAS.index(ronda)
    return ORDEN_RONDAS[idx + 1]


def cerrar_ronda_y_avanzar() -> str:
    """Cierra la ronda actual, promueve a las ganadoras y devuelve la ronda nueva.

    En "groups" el cupo es por continente (CUOTAS_GRUPOS).
    En el resto el cupo es un numero unico de todo el grupo (CUPO_RONDA).
    """
    ronda = db.get_ronda_actual()
    if ronda == "done":
        return ronda  # ya terminamos, no hay nada para cerrar

    etapa_siguiente = siguiente_ronda(ronda)
    ganadoras_ids: list[int] = []
    perdedoras_ids: list[int] = []

    if ronda == "groups":
        filas = db.tally_ronda(ronda)
        por_continente: dict[str, list] = {}
        for fila in filas:
            por_continente.setdefault(fila["continente"], []).append(fila)
        for continente, candidatas in por_continente.items():
            cupo = CUOTAS_GRUPOS.get(continente, 0)
            ganadoras_ids += [c["id"] for c in candidatas[:cupo]]
            perdedoras_ids += [c["id"] for c in candidatas[cupo:]]
    else:
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
    if ronda == "groups":
        return sum(CUOTAS_GRUPOS.values())
    return CUPO_RONDA.get(ronda, 0)


def cupo_por_continente(continente: str) -> int:
    return CUOTAS_GRUPOS.get(continente, 0)


NOMBRES_RONDA = {
    "groups": "Fase de grupos (por continente)",
    "top30": "Top 30 - Ronda de traje de bano",
    "top12": "Top 12 - Ronda de vestido de noche",
    "top5": "Top 5 - Ronda de preguntas",
    "top3": "Top 3 - Pregunta final",
    "done": "\U0001f451 Tenemos ganadora",
}

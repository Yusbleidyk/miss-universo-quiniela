"""Validacion de apuestas y calculo de la tabla de posiciones."""
from app import db
from app.data import BONUS_GANADORA, CUPOS, NIVELES, ORIGEN


def validar_apuesta(picks_por_nivel: dict[str, list[int]], ganadora_id: int | None) -> str | None:
    """Valida cupos exactos, anidacion (cada nivel sale del anterior) y que la
    ganadora elegida este dentro del Top 3 propio. Devuelve un mensaje de
    error, o None si esta todo bien.
    """
    ids_validos = {c["id"] for c in db.listar_candidatas()}

    for nivel in NIVELES:
        elegidas = picks_por_nivel.get(nivel, [])
        cupo = CUPOS[nivel]

        if len(set(elegidas)) != len(elegidas):
            return f"Elegiste una candidata repetida en {nivel}."
        if len(elegidas) != cupo:
            return f"Tenés que elegir exactamente {cupo} candidatas en {nivel} (elegiste {len(elegidas)})."
        if any(cid not in ids_validos for cid in elegidas):
            return "Che, alguna seleccion no es valida. Probá de nuevo."

        origen = ORIGEN[nivel]
        if origen is not None:
            permitidas = set(picks_por_nivel.get(origen, []))
            if not set(elegidas).issubset(permitidas):
                return f"Las candidatas de {nivel} tienen que salir de tu propio {origen}."

    if ganadora_id is None:
        return "Tenés que elegir una ganadora."
    if ganadora_id not in set(picks_por_nivel.get("top3", [])):
        return "La ganadora tiene que ser una de las 3 que elegiste en el Top 3."

    return None


def calcular_tabla_posiciones() -> list[dict]:
    """Compara cada participante contra el resultado real y arma el ranking.

    Si todavia no se cargo ningun resultado real, todos quedan en 0 (no es
    un error, simplemente no hay nada contra que comparar todavia).
    """
    real = db.get_resultado_real()
    picks_reales = db.obtener_picks(real["id"])

    tabla = []
    for participante in db.listar_participantes():
        picks_propios = db.obtener_picks(participante["id"])
        aciertos_por_nivel = {}
        score = 0
        for nivel in NIVELES:
            aciertos = len(set(picks_propios.get(nivel, [])) & set(picks_reales.get(nivel, [])))
            aciertos_por_nivel[nivel] = aciertos
            score += aciertos

        acerto_ganadora = (
            real["ganadora_id"] is not None
            and participante["ganadora_id"] == real["ganadora_id"]
        )
        if acerto_ganadora:
            score += BONUS_GANADORA

        tabla.append(
            {
                "id": participante["id"],
                "nombre": participante["nombre"],
                "score": score,
                "aciertos": aciertos_por_nivel,
                "acerto_ganadora": acerto_ganadora,
                "tiene_apuesta": any(picks_propios.get(n) for n in NIVELES),
            }
        )

    tabla.sort(key=lambda fila: fila["score"], reverse=True)
    return tabla

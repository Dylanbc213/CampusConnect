"""Presentación de fechas sin modificar los valores almacenados."""

from datetime import datetime


def fecha_publicacion(valor, ahora=None):
    try:
        fecha = datetime.fromisoformat(valor)
        actual = ahora if ahora is not None else datetime.now(fecha.tzinfo)
        segundos = max(0, int((actual - fecha).total_seconds()))
    except (TypeError, ValueError, OverflowError):
        return "Fecha no disponible"
    if segundos < 60:
        cantidad, unidad = segundos, "segundo"
    elif segundos < 3600:
        cantidad, unidad = segundos // 60, "minuto"
    elif segundos < 86400:
        cantidad, unidad = segundos // 3600, "hora"
    else:
        cantidad, unidad = segundos // 86400, "día"
    return "Hace {} {}{} · {:02d}/{:02d}/{:04d}".format(
        cantidad, unidad, "" if cantidad == 1 else "s", fecha.day, fecha.month, fecha.year)

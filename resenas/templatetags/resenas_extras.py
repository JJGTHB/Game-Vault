from django import template

register = template.Library()


def _n(valor):
    return max(0, min(5, int(round(valor))))


@register.filter
def estrellas(valor):
    """4 -> ★★★★ (solo estrellas llenas; acepta promedios decimales)."""
    if valor is None:
        return ''
    return '★' * _n(valor)


@register.filter
def puntaje(valor):
    """4 -> 4-★★★★ (mismo formato que el selector de calificación)."""
    if valor is None:
        return ''
    n = _n(valor)
    return f'{n}-' + '★' * n


@register.filter
def clase_puntuacion(valor):
    """'alta' (4-5), 'media' (3) o 'baja' (1-2)."""
    if valor is None:
        return ''
    if valor >= 4:
        return 'alta'
    if valor >= 3:
        return 'media'
    return 'baja'

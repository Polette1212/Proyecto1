from django import template


register = template.Library()


# ============================================================
# OBTENER EL VALOR DE UN CAMPO
# ============================================================

@register.filter
def field_value(instance, field_name):

    value = getattr(
        instance,
        field_name,
        ""
    )

    return value() if callable(value) else value


# ============================================================
# COMPROBAR SI EL USUARIO PERTENECE A UN GRUPO
# ============================================================

@register.filter
def has_group(user, group_name):

    if not user or not user.is_authenticated:
        return False

    return user.groups.filter(
        name=group_name
    ).exists()
from django.contrib import admin

from .models import (
    GamerProfile,
    Game,
    LibraryEntry,
    Cart,
    CartItem,
    Order,
    OrderItem,
    UserAccess,
)


# ============================================================
# PERFIL DE JUGADOR
# ============================================================

@admin.register(GamerProfile)
class GamerProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "nickname",
        "favorite_genre",
        "avatar",
    )

    search_fields = (
        "user__username",
        "user__email",
        "nickname",
        "favorite_genre",
    )

    list_filter = (
        "favorite_genre",
    )


# ============================================================
# JUEGOS
# ============================================================

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "genre",
        "platform",
        "launch_year",
        "price",
        "stock",
        "created_at",
    )

    search_fields = (
        "title",
        "genre",
        "platform",
    )

    list_filter = (
        "genre",
        "platform",
        "launch_year",
    )

    ordering = (
        "-created_at",
    )


# ============================================================
# BIBLIOTECA
# ============================================================

@admin.register(LibraryEntry)
class LibraryEntryAdmin(admin.ModelAdmin):

    list_display = (
        "gamer",
        "game",
        "status",
        "score",
        "added_at",
    )

    search_fields = (
        "gamer__nickname",
        "gamer__user__username",
        "game__title",
    )

    list_filter = (
        "status",
        "score",
    )


# ============================================================
# CARRITO
# ============================================================

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "session_key",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "session_key",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )


# ============================================================
# PRODUCTOS DEL CARRITO
# ============================================================

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):

    list_display = (
        "cart",
        "game",
        "quantity",
    )

    search_fields = (
        "cart__user__username",
        "game__title",
    )

    list_filter = (
        "quantity",
    )


# ============================================================
# PEDIDOS / TRANSACCIONES
# ============================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "customer_name",
        "customer_rut",
        "customer_email",
        "status",
        "payment_method",
        "subtotal",
        "discount",
        "total",
        "created_at",
    )

    search_fields = (
        "customer_name",
        "customer_rut",
        "customer_email",
        "user__username",
    )

    list_filter = (
        "status",
        "payment_method",
        "customer_type",
        "created_at",
    )

    ordering = (
        "-created_at",
    )


# ============================================================
# DETALLE DEL PEDIDO
# ============================================================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "game",
        "quantity",
        "unit_price",
        "subtotal",
    )

    search_fields = (
        "order__customer_name",
        "order__customer_rut",
        "game__title",
    )

    list_filter = (
        "game",
    )


# ============================================================
# CONTROL DE ACCESO
# ============================================================

@admin.register(UserAccess)
class UserAccessAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "get_role",
        "enabled",
        "unrestricted_hours",
        "access_start",
        "access_end",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )

    list_filter = (
        "enabled",
        "unrestricted_hours",
        "access_start",
        "access_end",
    )

    readonly_fields = (
        "updated_at",
    )


    @admin.display(
        description="Rol"
    )
    def get_role(self, obj):

        if obj.user.is_superuser:
            return "Administrador"

        if obj.user.groups.filter(
            name="Operador"
        ).exists():
            return "Operador"

        if obj.user.groups.filter(
            name="Consulta"
        ).exists():
            return "Consulta"

        return "Usuario"
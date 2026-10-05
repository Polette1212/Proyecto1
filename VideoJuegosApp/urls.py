from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # CATÁLOGO
    # ========================================================

    path(
        "catalogo/",
        views.videojuegos,
        name="videojuegos"
    ),

    path(
        "catalogo/detalle/<int:id>/",
        views.detalle,
        name="detalle"
    ),


    # ========================================================
    # AUTENTICACIÓN / REGISTRO
    # ========================================================

    path(
        "registro/",
        views.register,
        name="register"
    ),

    path(
        "cerrar-sesion/",
        views.logout_user,
        name="logout_user"
    ),


    # ========================================================
    # CARRITO
    # ========================================================

    path(
        "carrito/",
        views.cart_view,
        name="cart"
    ),

    path(
        "carrito/agregar/<int:game_id>/",
        views.cart_add,
        name="cart_add"
    ),

    path(
        "carrito/actualizar/<int:item_id>/",
        views.cart_update,
        name="cart_update"
    ),

    path(
        "carrito/eliminar/<int:item_id>/",
        views.cart_remove,
        name="cart_remove"
    ),


    # ========================================================
    # CHECKOUT / COMPRA
    # ========================================================

    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    path(
        "compra/<int:order_id>/",
        views.order_success,
        name="order_success"
    ),

    path(
        "compra/<int:order_id>/comprobante/",
        views.order_receipt_pdf,
        name="order_receipt_pdf"
    ),

    path(
        "historial/",
        views.order_history,
        name="order_history"
    ),


    # ========================================================
    # DASHBOARD
    # ========================================================

    path(
        "",
        views.dashboard,
        name="vault_dashboard"
    ),


    # ========================================================
    # ADMINISTRACIÓN DE USUARIOS
    # SOLO ADMINISTRADOR
    # ========================================================

    path(
        "administracion/usuarios/",
        views.admin_users,
        name="admin_users"
    ),

    path(
        "administracion/usuarios/nuevo/",
        views.admin_user_create,
        name="admin_user_create"
    ),

    path(
        "administracion/usuarios/<int:user_id>/editar/",
        views.admin_user_edit,
        name="admin_user_edit"
    ),

    path(
        "administracion/usuarios/<int:user_id>/password/",
        views.admin_user_password,
        name="admin_user_password"
    ),

    path(
        "administracion/usuarios/<int:user_id>/eliminar/",
        views.admin_user_delete,
        name="admin_user_delete"
    ),


    # ========================================================
    # ADMINISTRACIÓN DE COMPRAS / PEDIDOS
    # SOLO ADMINISTRADOR
    # ========================================================

    path(
        "administracion/compras/",
        views.admin_orders,
        name="admin_orders"
    ),

    path(
        "administracion/compras/<int:order_id>/",
        views.admin_order_detail,
        name="admin_order_detail"
    ),

    path(
        "administracion/compras/<int:order_id>/eliminar/",
        views.admin_order_delete,
        name="admin_order_delete"
    ),


    # ========================================================
    # CONTROL DE ACCESO
    # SOLO ADMINISTRADOR
    #
    # Permite:
    # - Ver Operadores y Consulta.
    # - Habilitar / suspender.
    # - Configurar horario.
    # ========================================================

    path(
        "administracion/accesos/",
        views.admin_access,
        name="admin_access"
    ),

    path(
        "administracion/accesos/<int:user_id>/editar/",
        views.admin_access_edit,
        name="admin_access_edit"
    ),

    path(
        "administracion/accesos/<int:user_id>/alternar/",
        views.admin_access_toggle,
        name="admin_access_toggle"
    ),


    # ========================================================
    # CRUD
    # ========================================================

    path(
        "<str:module>/",
        views.record_list,
        name="vault_list"
    ),

    path(
        "<str:module>/nuevo/",
        views.record_form,
        name="vault_create"
    ),

    path(
        "<str:module>/<int:pk>/editar/",
        views.record_form,
        name="vault_edit"
    ),

    path(
        "<str:module>/<int:pk>/eliminar/",
        views.record_delete,
        name="vault_delete"
    ),

]
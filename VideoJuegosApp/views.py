import json
import os
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AccessAuthenticationForm,
    AdminUserCreateForm,
    AdminUserPasswordForm,
    AdminUserUpdateForm,
    GameForm,
    GamerProfileForm,
    LibraryEntryForm,
    RegisterForm,
    UserAccessForm,
)

from .models import (
    Cart,
    CartItem,
    Game,
    GamerProfile,
    LibraryEntry,
    Order,
    OrderItem,
    UserAccess,
)


# ============================================================
# CARGAR VIDEOJUEGOS DESDE JSON
# ============================================================

def cargar_videojuegos():

    posibles_rutas = [
        os.path.join(
            settings.BASE_DIR,
            "VideoJuegosApp",
            "data",
            "videojuegos.json"
        ),

        os.path.join(
            settings.BASE_DIR,
            "VideoJuegosApp",
            "json",
            "videojuegos.json"
        ),

        os.path.join(
            settings.BASE_DIR,
            "videojuegos.json"
        ),
    ]

    for ruta in posibles_rutas:

        if os.path.exists(ruta):

            try:

                with open(
                    ruta,
                    "r",
                    encoding="utf-8"
                ) as archivo:

                    return json.load(archivo)

            except (
                json.JSONDecodeError,
                OSError
            ):

                return []

    return []


# ============================================================
# CATÁLOGO
# ============================================================

def videojuegos(request):

    juegos = (
        Game.objects
        .all()
        .order_by("title")
    )

    return render(
        request,
        "videojuegos.html",
        {
            "videojuegos": juegos,
            "role": role_for(request.user),
        }
    )


# ============================================================
# DETALLE DEL VIDEOJUEGO
# ============================================================

def detalle(request, id):

    juego = get_object_or_404(
        Game,
        id=id
    )

    return render(
        request,
        "detalle.html",
        {
            "juego": juego,
            "role": role_for(request.user),
        }
    )


# ============================================================
# REGISTRO DE USUARIOS
# ============================================================

def register(request):

    if request.user.is_authenticated:

        return redirect(
            "videojuegos"
        )

    if request.method == "POST":

        form = RegisterForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            GamerProfile.objects.create(
                user=user,
                nickname=user.username
            )

            login(
                request,
                user
            )

            messages.success(
                request,
                "Cuenta creada correctamente."
            )

            return redirect(
                "videojuegos"
            )

    else:

        form = RegisterForm()

    return render(
        request,
        "registration/register.html",
        {
            "form": form,
        }
    )


# ============================================================
# LOGIN CON CONTROL DE HORARIO
# ============================================================

def custom_login(request):

    if request.user.is_authenticated:

        return redirect(
            "videojuegos"
        )

    next_url = request.GET.get(
        "next"
    ) or request.POST.get(
        "next"
    )

    if request.method == "POST":

        form = AccessAuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(
                request,
                user
            )

            messages.success(
                request,
                f"Bienvenido a GameVault, "
                f"{user.username}."
            )

            if next_url:

                return redirect(
                    next_url
                )

            return redirect(
                "vault_dashboard"
            )

    else:

        form = AccessAuthenticationForm(
            request
        )

    return render(
        request,
        "registration/login.html",
        {
            "form": form,
            "next": next_url,
        }
    )


# ============================================================
# CERRAR SESIÓN
# ============================================================

def logout_user(request):

    logout(request)

    messages.success(
        request,
        "Sesión cerrada correctamente."
    )

    return redirect(
        "login"
    )


# ============================================================
# CONFIGURACIÓN DE MÓDULOS DEL PANEL
# ============================================================

MODULES = {

    "games": {

        "model": Game,

        "form": GameForm,

        "title": "Videojuegos",

        "icon": "🕹️",

        "fields": [
            "title",
            "genre",
            "platform",
            "launch_year",
            "price",
            "stock",
            "cover",
            "technical_sheet",
        ],
    },

    "gamers": {

        "model": GamerProfile,

        "form": GamerProfileForm,

        "title": "Perfiles gamer",

        "icon": "👾",

        "fields": [
            "nickname",
            "user",
            "favorite_genre",
        ],
    },

    "library": {

        "model": LibraryEntry,

        "form": LibraryEntryForm,

        "title": "Biblioteca",

        "icon": "⚡",

        "fields": [
            "gamer",
            "game",
            "status",
            "score",
        ],
    },
}


# ============================================================
# DETERMINAR ROL
# ============================================================

def role_for(user):

    if not user.is_authenticated:

        return "Visitante"

    if user.is_superuser:

        return "Administrador"

    if user.groups.filter(
        name="Operador"
    ).exists():

        return "Operador"

    if user.groups.filter(
        name="Consulta"
    ).exists():

        return "Consulta"

    return "Usuario"


# ============================================================
# PERMISO PARA CREAR Y MODIFICAR
# ============================================================

def can_write(user):

    return role_for(user) in [
        "Administrador",
        "Operador",
    ]


# ============================================================
# PERMISO PARA ELIMINAR
# ============================================================

def can_delete(user):

    return role_for(user) == "Administrador"


# ============================================================
# PERMISO PARA CONSULTAR EL PANEL
# ============================================================

def can_access_vault(user):

    return role_for(user) in [
        "Administrador",
        "Operador",
        "Consulta",
    ]


# ============================================================
# DECORADOR SOLO ADMINISTRADOR
# ============================================================

def admin_required(view_func):

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):

        if role_for(request.user) != "Administrador":

            messages.error(
                request,
                "Solo el Administrador puede acceder "
                "a esta sección."
            )

            return redirect(
                "vault_dashboard"
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# DASHBOARD
# ============================================================

@login_required
def dashboard(request):

    if not can_access_vault(request.user):

        messages.error(
            request,
            "No tienes permisos para acceder "
            "al panel administrativo."
        )

        return redirect(
            "videojuegos"
        )

    game_count = Game.objects.count()

    gamer_count = GamerProfile.objects.count()

    entry_count = LibraryEntry.objects.count()

    recent_entries = (
        LibraryEntry.objects
        .select_related(
            "gamer",
            "game"
        )
        .order_by("-added_at")[:5]
    )

    context = {
        "game_count": game_count,
        "gamer_count": gamer_count,
        "entry_count": entry_count,
        "recent_entries": recent_entries,
        "role": role_for(request.user),
    }

    # --------------------------------------------------------
    # INFORMACIÓN EXCLUSIVA DEL ADMINISTRADOR
    # --------------------------------------------------------

    if role_for(request.user) == "Administrador":

        context.update({

            "user_count": User.objects.count(),

            "order_count": Order.objects.count(),

            "restricted_user_count": (
                User.objects
                .filter(
                    groups__name__in=[
                        "Operador",
                        "Consulta",
                    ]
                )
                .distinct()
                .count()
            ),

            "recent_orders": (
                Order.objects
                .select_related("user")
                .order_by("-created_at")[:5]
            ),

            "sales_total": (
                Order.objects
                .filter(
                    status="pagada"
                )
                .aggregate(
                    total=Sum("total")
                )
                .get("total")
                or 0
            ),
        })

    return render(
        request,
        "vault/dashboard.html",
        context
    )


# ============================================================
# LISTADO DE REGISTROS
# ============================================================

@login_required
def record_list(request, module):

    if not can_access_vault(request.user):

        messages.error(
            request,
            "No tienes permisos para acceder "
            "a este módulo."
        )

        return redirect(
            "videojuegos"
        )

    if module not in MODULES:

        messages.error(
            request,
            "El módulo solicitado no existe."
        )

        return redirect(
            "vault_dashboard"
        )

    config = MODULES[module]

    model = config["model"]

    records = model.objects.all()

    # --------------------------------------------------------
    # BÚSQUEDA
    # --------------------------------------------------------

    search = request.GET.get(
        "q",
        ""
    ).strip()

    if search:

        if module == "games":

            records = records.filter(

                Q(
                    title__icontains=search
                )
                |
                Q(
                    genre__icontains=search
                )
                |
                Q(
                    platform__icontains=search
                )

            )

        elif module == "gamers":

            records = records.filter(

                Q(
                    nickname__icontains=search
                )
                |
                Q(
                    user__username__icontains=search
                )

            )

        elif module == "library":

            records = records.filter(

                Q(
                    gamer__nickname__icontains=search
                )
                |
                Q(
                    game__title__icontains=search
                )
                |
                Q(
                    status__icontains=search
                )

            )

    return render(
        request,
        "vault/list.html",
        {
            "module": module,
            "config": config,
            "records": records,
            "objects": records,
            "search": search,
            "query": search,
            "role": role_for(request.user),
            "can_write": can_write(
                request.user
            ),
            "can_delete": can_delete(
                request.user
            ),
        }
    )


# ============================================================
# CREAR / EDITAR REGISTRO
# ============================================================

@login_required
def record_form(
    request,
    module,
    pk=None
):

    if not can_access_vault(request.user):

        messages.error(
            request,
            "No tienes permisos para acceder al panel."
        )

        return redirect(
            "videojuegos"
        )

    if not can_write(request.user):

        messages.error(
            request,
            "Tu perfil solo permite consultar "
            "y buscar información."
        )

        return redirect(
            "vault_list",
            module=module
        )

    if module not in MODULES:

        messages.error(
            request,
            "El módulo solicitado no existe."
        )

        return redirect(
            "vault_dashboard"
        )

    config = MODULES[module]

    model = config["model"]

    form_class = config["form"]

    record = None

    if pk is not None:

        record = get_object_or_404(
            model,
            pk=pk
        )

    if request.method == "POST":

        form = form_class(
            request.POST,
            request.FILES,
            instance=record
        )

        if form.is_valid():

            form.save()

            if record:

                messages.success(
                    request,
                    "Registro actualizado correctamente."
                )

            else:

                messages.success(
                    request,
                    "Registro creado correctamente."
                )

            return redirect(
                "vault_list",
                module=module
            )

    else:

        form = form_class(
            instance=record
        )

    return render(
        request,
        "vault/form.html",
        {
            "form": form,
            "record": record,
            "module": module,
            "config": config,
            "role": role_for(request.user),
        }
    )


# ============================================================
# ELIMINAR REGISTRO
# ============================================================

@login_required
def record_delete(
    request,
    module,
    pk
):

    if not can_delete(request.user):

        messages.error(
            request,
            "Solo el Administrador puede eliminar registros."
        )

        return redirect(
            "vault_list",
            module=module
        )

    if module not in MODULES:

        messages.error(
            request,
            "El módulo solicitado no existe."
        )

        return redirect(
            "vault_dashboard"
        )

    config = MODULES[module]

    model = config["model"]

    record = get_object_or_404(
        model,
        pk=pk
    )

    # --------------------------------------------------------
    # PROTEGER VIDEOJUEGOS QUE TIENEN COMPRAS
    # --------------------------------------------------------

    if module == "games":

        if OrderItem.objects.filter(
            game=record
        ).exists():

            messages.error(
                request,
                "No se puede eliminar este videojuego "
                "porque ya forma parte de una compra registrada."
            )

            return redirect(
                "vault_list",
                module=module
            )

    # --------------------------------------------------------
    # CONFIRMACIÓN
    # --------------------------------------------------------

    if request.method == "POST":

        record.delete()

        messages.success(
            request,
            "Registro eliminado correctamente."
        )

        return redirect(
            "vault_list",
            module=module
        )

    return render(
        request,
        "vault/eliminar_registro.html",
        {
            "record": record,
            "module": module,
            "config": config,
        }
    )


# ============================================================
# OBTENER / CREAR CARRITO
# ============================================================

def get_current_cart(request):

    if request.user.is_authenticated:

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        return cart

    if not request.session.session_key:

        request.session.create()

    session_key = request.session.session_key

    cart, created = Cart.objects.get_or_create(
        session_key=session_key,
        defaults={
            "user": None,
        }
    )

    return cart


# ============================================================
# CARRITO
# ============================================================

def cart_view(request):

    cart = get_current_cart(request)

    items = (
        cart.items
        .select_related("game")
        .all()
    )

    total = cart.total()

    return render(
        request,
        "cart.html",
        {
            "cart": cart,
            "items": items,
            "total": total,
            "role": role_for(request.user),
        }
    )


# ============================================================
# AGREGAR PRODUCTO AL CARRITO
# ============================================================

def cart_add(
    request,
    game_id
):

    game = get_object_or_404(
        Game,
        id=game_id
    )

    if request.method != "POST":

        return redirect(
            "detalle",
            id=game.id
        )

    try:

        quantity = int(
            request.POST.get(
                "quantity",
                1
            )
        )

    except (
        TypeError,
        ValueError
    ):

        quantity = 1

    if quantity < 1:

        quantity = 1

    if game.stock <= 0:

        messages.error(
            request,
            "Este videojuego no tiene stock disponible."
        )

        return redirect(
            "detalle",
            id=game.id
        )

    cart = get_current_cart(request)

    item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        game=game,
        defaults={
            "quantity": quantity
        }
    )

    if not item_created:

        new_quantity = (
            item.quantity +
            quantity
        )

        if new_quantity > game.stock:

            messages.error(
                request,
                "No puedes agregar más unidades "
                "que el stock disponible."
            )

            return redirect(
                "cart"
            )

        item.quantity = new_quantity

        item.save()

    else:

        if quantity > game.stock:

            item.quantity = game.stock

            item.save()

            messages.warning(
                request,
                "La cantidad fue ajustada "
                "al stock disponible."
            )

    messages.success(
        request,
        f"{game.title} fue agregado al carrito."
    )

    return redirect(
        "cart"
    )


# ============================================================
# ACTUALIZAR CANTIDAD
# ============================================================

def cart_update(
    request,
    item_id
):

    cart = get_current_cart(request)

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart
    )

    if request.method != "POST":

        return redirect(
            "cart"
        )

    try:

        quantity = int(
            request.POST.get(
                "quantity",
                1
            )
        )

    except (
        TypeError,
        ValueError
    ):

        messages.error(
            request,
            "Cantidad inválida."
        )

        return redirect(
            "cart"
        )

    if quantity < 1:

        messages.error(
            request,
            "La cantidad debe ser mayor a cero."
        )

        return redirect(
            "cart"
        )

    if quantity > item.game.stock:

        messages.error(
            request,
            "La cantidad solicitada supera "
            "el stock disponible."
        )

        return redirect(
            "cart"
        )

    item.quantity = quantity

    item.save()

    messages.success(
        request,
        "Cantidad actualizada correctamente."
    )

    return redirect(
        "cart"
    )


# ============================================================
# ELIMINAR PRODUCTO DEL CARRITO
# ============================================================

def cart_remove(
    request,
    item_id
):

    cart = get_current_cart(request)

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart
    )

    if request.method == "POST":

        item.delete()

        messages.success(
            request,
            "Producto eliminado del carrito."
        )

    return redirect(
        "cart"
    )


# ============================================================
# CHECKOUT
# ============================================================

def checkout(request):

    cart = get_current_cart(request)

    items = (
        cart.items
        .select_related("game")
        .all()
    )

    if not items.exists():

        messages.warning(
            request,
            "Tu carrito está vacío."
        )

        return redirect(
            "cart"
        )

    total = cart.total()

    if request.user.is_authenticated:

        customer_type = "registrado"

        default_name = request.user.get_full_name()

        if not default_name:

            default_name = request.user.username

        default_email = request.user.email

    else:

        customer_type = "visitante"

        default_name = ""

        default_email = ""

    if request.method == "POST":

        customer_name = request.POST.get(
            "customer_name",
            ""
        ).strip()

        customer_rut = request.POST.get(
            "customer_rut",
            ""
        ).strip()

        shipping_address = request.POST.get(
            "shipping_address",
            ""
        ).strip()

        customer_phone = request.POST.get(
            "customer_phone",
            ""
        ).strip()

        customer_email = request.POST.get(
            "customer_email",
            ""
        ).strip().lower()

        payment_method = request.POST.get(
            "payment_method",
            ""
        ).strip()

        if not customer_name:

            messages.error(
                request,
                "Debes ingresar el nombre del cliente."
            )

            return redirect(
                "checkout"
            )

        if not customer_rut:

            messages.error(
                request,
                "Debes ingresar el RUT del cliente."
            )

            return redirect(
                "checkout"
            )

        if not shipping_address:

            messages.error(
                request,
                "Debes ingresar la dirección de despacho."
            )

            return redirect(
                "checkout"
            )

        if not customer_phone:

            messages.error(
                request,
                "Debes ingresar el teléfono del cliente."
            )

            return redirect(
                "checkout"
            )

        if not customer_email:

            messages.error(
                request,
                "Debes ingresar el correo electrónico."
            )

            return redirect(
                "checkout"
            )

        valid_payment_methods = [
            "tarjeta",
            "webpay",
        ]

        if payment_method not in valid_payment_methods:

            messages.error(
                request,
                "Debes seleccionar un método de pago válido."
            )

            return redirect(
                "checkout"
            )

        # ----------------------------------------------------
        # TRANSACCIÓN DE COMPRA
        # ----------------------------------------------------

        with transaction.atomic():

            cart = (
                Cart.objects
                .select_for_update()
                .get(
                    pk=cart.pk
                )
            )

            items = list(
                cart.items
                .select_related("game")
                .all()
            )

            if not items:

                messages.error(
                    request,
                    "El carrito está vacío."
                )

                return redirect(
                    "cart"
                )

            # ------------------------------------------------
            # VALIDAR STOCK
            # ------------------------------------------------

            for item in items:

                if item.quantity > item.game.stock:

                    messages.error(
                        request,
                        f"No hay stock suficiente para "
                        f"{item.game.title}. "
                        f"Stock disponible: "
                        f"{item.game.stock}."
                    )

                    return redirect(
                        "cart"
                    )

            # ------------------------------------------------
            # CALCULAR TOTALES
            # ------------------------------------------------

            order_subtotal = 0

            for item in items:

                order_subtotal += (
                    item.game.price *
                    item.quantity
                )

            order_discount = 0

            order_total = (
                order_subtotal -
                order_discount
            )

            # ------------------------------------------------
            # CREAR PEDIDO
            # ------------------------------------------------

            order = Order.objects.create(

                user=(
                    request.user
                    if request.user.is_authenticated
                    else None
                ),

                customer_name=customer_name,

                customer_rut=customer_rut,

                shipping_address=shipping_address,

                customer_email=customer_email,

                customer_phone=customer_phone,

                customer_type=customer_type,

                status="pagada",

                payment_method=payment_method,

                subtotal=order_subtotal,

                discount=order_discount,

                total=order_total,
            )

            # ------------------------------------------------
            # CREAR DETALLE
            # ------------------------------------------------

            for item in items:

                unit_price = item.game.price

                item_subtotal = (
                    unit_price *
                    item.quantity
                )

                OrderItem.objects.create(

                    order=order,

                    game=item.game,

                    quantity=item.quantity,

                    unit_price=unit_price,

                    subtotal=item_subtotal,
                )

                # --------------------------------------------
                # DESCONTAR STOCK
                # --------------------------------------------

                item.game.stock -= item.quantity

                item.game.save(
                    update_fields=[
                        "stock"
                    ]
                )

            # ------------------------------------------------
            # VACIAR CARRITO
            # ------------------------------------------------

            cart.items.all().delete()

        # ----------------------------------------------------
        # GUARDAR PEDIDO DEL VISITANTE
        # ----------------------------------------------------

        if not request.user.is_authenticated:

            request.session[
                "guest_order_id"
            ] = order.id

            request.session.modified = True

        messages.success(
            request,
            "¡Compra realizada correctamente!"
        )

        return redirect(
            "order_success",
            order_id=order.id
        )

    return render(
        request,
        "checkout.html",
        {
            "cart": cart,
            "items": items,
            "total": total,
            "customer_type": customer_type,
            "default_name": default_name,
            "default_email": default_email,
            "role": role_for(request.user),
        }
    )


# ============================================================
# COMPRA REALIZADA
# ============================================================

def order_success(
    request,
    order_id
):

    if request.user.is_authenticated:

        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user
        )

    else:

        guest_order_id = request.session.get(
            "guest_order_id"
        )

        if guest_order_id != order_id:

            messages.error(
                request,
                "No tienes permiso para consultar esta compra."
            )

            return redirect(
                "videojuegos"
            )

        order = get_object_or_404(
            Order,
            id=order_id,
            user__isnull=True
        )

    return render(
        request,
        "order_success.html",
        {
            "order": order,
            "items": (
                order.items
                .select_related("game")
                .all()
            ),
            "role": role_for(request.user),
        }
    )


# ============================================================
# HISTORIAL DE COMPRAS DEL USUARIO
# ============================================================

@login_required
def order_history(request):

    orders = (
        Order.objects
        .filter(
            user=request.user
        )
        .prefetch_related(
            "items__game"
        )
        .order_by(
            "-created_at"
        )
    )

    return render(
        request,
        "order_history.html",
        {
            "orders": orders,
            "role": role_for(request.user),
        }
    )


# ============================================================
# COMPROBANTE PDF
# ============================================================

def order_receipt_pdf(
    request,
    order_id
):

    if request.user.is_authenticated:

        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user
        )

    else:

        guest_order_id = request.session.get(
            "guest_order_id"
        )

        if guest_order_id != order_id:

            messages.error(
                request,
                "No tienes permiso para descargar "
                "este comprobante."
            )

            return redirect(
                "videojuegos"
            )

        order = get_object_or_404(
            Order,
            id=order_id,
            user__isnull=True
        )

    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]

    title_style.fontSize = 22
    title_style.leading = 26
    title_style.spaceAfter = 12

    heading_style = styles["Heading2"]

    heading_style.fontSize = 14
    heading_style.leading = 18
    heading_style.spaceBefore = 10
    heading_style.spaceAfter = 8

    normal_style = styles["Normal"]

    normal_style.fontSize = 10
    normal_style.leading = 14

    elements = []

    elements.append(
        Paragraph(
            "GAMEVAULT",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "COMPROBANTE DE COMPRA",
            heading_style
        )
    )

    elements.append(
        Spacer(
            1,
            6
        )
    )

    elements.append(
        Paragraph(
            f"<b>Número de pedido:</b> #{order.id}",
            normal_style
        )
    )

    elements.append(
        Paragraph(
            f"<b>Fecha:</b> "
            f"{order.created_at.strftime('%d/%m/%Y %H:%M')}",
            normal_style
        )
    )

    elements.append(
        Paragraph(
            f"<b>Estado:</b> "
            f"{order.get_status_display()}",
            normal_style
        )
    )

    elements.append(
        Paragraph(
            f"<b>Tipo de cliente:</b> "
            f"{order.get_customer_type_display()}",
            normal_style
        )
    )

    elements.append(
        Paragraph(
            f"<b>Método de pago:</b> "
            f"{order.get_payment_method_display()}",
            normal_style
        )
    )

    elements.append(
        Spacer(
            1,
            10
        )
    )

    elements.append(
        Paragraph(
            "DATOS DEL CLIENTE",
            heading_style
        )
    )

    customer_data = [

        [
            Paragraph(
                "<b>Nombre</b>",
                normal_style
            ),
            Paragraph(
                str(order.customer_name),
                normal_style
            ),
        ],

        [
            Paragraph(
                "<b>RUT</b>",
                normal_style
            ),
            Paragraph(
                str(order.customer_rut),
                normal_style
            ),
        ],

        [
            Paragraph(
                "<b>Correo</b>",
                normal_style
            ),
            Paragraph(
                str(order.customer_email),
                normal_style
            ),
        ],

        [
            Paragraph(
                "<b>Teléfono</b>",
                normal_style
            ),
            Paragraph(
                str(order.customer_phone),
                normal_style
            ),
        ],

        [
            Paragraph(
                "<b>Dirección</b>",
                normal_style
            ),
            Paragraph(
                str(order.shipping_address),
                normal_style
            ),
        ],
    ]

    customer_table = Table(
        customer_data,
        colWidths=[
            42 * mm,
            125 * mm,
        ]
    )

    customer_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ]
        )
    )

    elements.append(
        customer_table
    )

    elements.append(
        Spacer(
            1,
            12
        )
    )

    elements.append(
        Paragraph(
            "PRODUCTOS COMPRADOS",
            heading_style
        )
    )

    product_data = [

        [
            Paragraph(
                "<b>Videojuego</b>",
                normal_style
            ),

            Paragraph(
                "<b>Cantidad</b>",
                normal_style
            ),

            Paragraph(
                "<b>Precio unitario</b>",
                normal_style
            ),

            Paragraph(
                "<b>Subtotal</b>",
                normal_style
            ),
        ]
    ]

    order_items = (
        order.items
        .select_related("game")
        .all()
    )

    for item in order_items:

        product_data.append(

            [

                Paragraph(
                    str(item.game.title),
                    normal_style
                ),

                Paragraph(
                    str(item.quantity),
                    normal_style
                ),

                Paragraph(
                    f"${item.unit_price:,.0f}",
                    normal_style
                ),

                Paragraph(
                    f"${item.subtotal:,.0f}",
                    normal_style
                ),

            ]
        )

    product_table = Table(
        product_data,
        colWidths=[
            82 * mm,
            20 * mm,
            35 * mm,
            35 * mm,
        ],
        repeatRows=1
    )

    product_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ]
        )
    )

    elements.append(
        product_table
    )

    elements.append(
        Spacer(
            1,
            12
        )
    )

    elements.append(
        Paragraph(
            "RESUMEN DE PAGO",
            heading_style
        )
    )

    summary_data = [

        [
            Paragraph(
                "<b>Subtotal</b>",
                normal_style
            ),

            Paragraph(
                f"${order.subtotal:,.0f}",
                normal_style
            ),
        ],

        [
            Paragraph(
                "<b>Descuento</b>",
                normal_style
            ),

            Paragraph(
                f"${order.discount:,.0f}",
                normal_style
            ),
        ],

        [
            Paragraph(
                "<b>TOTAL</b>",
                normal_style
            ),

            Paragraph(
                f"<b>${order.total:,.0f}</b>",
                normal_style
            ),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            120 * mm,
            47 * mm,
        ]
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                ),

                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    colors.lightgrey
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
            ]
        )
    )

    elements.append(
        summary_table
    )

    elements.append(
        Spacer(
            1,
            18
        )
    )

    elements.append(
        Paragraph(
            "Documento generado automáticamente por GameVault.",
            normal_style
        )
    )

    document.build(
        elements
    )

    pdf = buffer.getvalue()

    buffer.close()

    response = HttpResponse(
        pdf,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="comprobante_gamevault_{order.id}.pdf"'
    )

    return response


# ============================================================
# ADMINISTRACIÓN DE USUARIOS
# ============================================================

@admin_required
def admin_users(request):

    users = (
        User.objects
        .prefetch_related(
            "groups",
            "access_control"
        )
        .order_by(
            "username"
        )
    )

    search = request.GET.get(
        "q",
        ""
    ).strip()

    role_filter = request.GET.get(
        "role",
        ""
    ).strip()

    # --------------------------------------------------------
    # BÚSQUEDA
    # --------------------------------------------------------

    if search:

        users = users.filter(

            Q(
                username__icontains=search
            )
            |
            Q(
                first_name__icontains=search
            )
            |
            Q(
                last_name__icontains=search
            )
            |
            Q(
                email__icontains=search
            )

        )

    # --------------------------------------------------------
    # FILTRO POR ROL
    # --------------------------------------------------------

    if role_filter == "Administrador":

        users = users.filter(
            is_superuser=True
        )

    elif role_filter == "Operador":

        users = users.filter(
            groups__name="Operador"
        )

    elif role_filter == "Consulta":

        users = users.filter(
            groups__name="Consulta"
        )

    elif role_filter == "Usuario":

        users = users.filter(
            is_superuser=False
        ).exclude(
            groups__name__in=[
                "Operador",
                "Consulta",
            ]
        )

    users = users.distinct()

    return render(
        request,
        "vault/admin_users.html",
        {
            "users": users,
            "search": search,
            "role_filter": role_filter,
            "role": role_for(request.user),
        }
    )


# ============================================================
# CREAR USUARIO DESDE ADMINISTRACIÓN
# ============================================================

@admin_required
def admin_user_create(request):

    if request.method == "POST":

        form = AdminUserCreateForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                f"Usuario {user.username} "
                "creado correctamente."
            )

            return redirect(
                "admin_users"
            )

    else:

        form = AdminUserCreateForm()

    return render(
        request,
        "vault/admin_user_form.html",
        {
            "form": form,
            "title": "Crear usuario",
            "action": "Crear usuario",
            "role": role_for(request.user),
        }
    )


# ============================================================
# EDITAR USUARIO
# ============================================================

@admin_required
def admin_user_edit(
    request,
    user_id
):

    user = get_object_or_404(
        User,
        id=user_id
    )

    if request.method == "POST":

        form = AdminUserUpdateForm(
            request.POST,
            instance=user
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                f"Usuario {user.username} "
                "actualizado correctamente."
            )

            return redirect(
                "admin_users"
            )

    else:

        form = AdminUserUpdateForm(
            instance=user
        )

    return render(
        request,
        "vault/admin_user_form.html",
        {
            "form": form,
            "user_record": user,
            "title": "Editar usuario",
            "action": "Guardar cambios",
            "role": role_for(request.user),
        }
    )


# ============================================================
# CAMBIAR CONTRASEÑA
# ============================================================

@admin_required
def admin_user_password(
    request,
    user_id
):

    user = get_object_or_404(
        User,
        id=user_id
    )

    if request.method == "POST":

        form = AdminUserPasswordForm(
            user,
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                f"Contraseña de {user.username} "
                "actualizada correctamente."
            )

            return redirect(
                "admin_users"
            )

    else:

        form = AdminUserPasswordForm(
            user
        )

    return render(
        request,
        "vault/admin_user_password.html",
        {
            "form": form,
            "user_record": user,
            "role": role_for(request.user),
        }
    )


# ============================================================
# ELIMINAR USUARIO
# ============================================================

@admin_required
def admin_user_delete(
    request,
    user_id
):

    user = get_object_or_404(
        User,
        id=user_id
    )

    # --------------------------------------------------------
    # NO PERMITIR ELIMINAR LA PROPIA CUENTA
    # --------------------------------------------------------

    if user.id == request.user.id:

        messages.error(
            request,
            "No puedes eliminar la cuenta con la que "
            "estás actualmente conectado."
        )

        return redirect(
            "admin_users"
        )

    # --------------------------------------------------------
    # CONFIRMACIÓN
    # --------------------------------------------------------

    if request.method == "POST":

        username = user.username

        user.delete()

        messages.success(
            request,
            f"El usuario {username} "
            "fue eliminado correctamente."
        )

        return redirect(
            "admin_users"
        )

    return render(
        request,
        "vault/admin_user_delete.html",
        {
            "user_record": user,
            "role": role_for(request.user),
        }
    )


# ============================================================
# ADMINISTRACIÓN DE COMPRAS
# ============================================================

@admin_required
def admin_orders(request):

    orders = (
        Order.objects
        .select_related("user")
        .prefetch_related(
            "items__game"
        )
        .order_by(
            "-created_at"
        )
    )

    search = request.GET.get(
        "q",
        ""
    ).strip()

    status_filter = request.GET.get(
        "status",
        ""
    ).strip()

    # --------------------------------------------------------
    # BÚSQUEDA
    # --------------------------------------------------------

    if search:

        orders = orders.filter(

            Q(
                customer_name__icontains=search
            )
            |
            Q(
                customer_rut__icontains=search
            )
            |
            Q(
                customer_email__icontains=search
            )
            |
            Q(
                customer_phone__icontains=search
            )
            |
            Q(
                user__username__icontains=search
            )

        )

    # --------------------------------------------------------
    # FILTRO DE ESTADO
    # --------------------------------------------------------

    if status_filter in [
        "pendiente",
        "pagada",
        "cancelada",
    ]:

        orders = orders.filter(
            status=status_filter
        )

    return render(
        request,
        "vault/admin_orders.html",
        {
            "orders": orders,
            "search": search,
            "status_filter": status_filter,
            "role": role_for(request.user),
        }
    )


# ============================================================
# DETALLE DE COMPRA DESDE ADMINISTRACIÓN
# ============================================================

@admin_required
def admin_order_detail(
    request,
    order_id
):

    order = get_object_or_404(
        Order.objects
        .select_related("user")
        .prefetch_related(
            "items__game"
        ),
        id=order_id
    )

    return render(
        request,
        "vault/admin_order_detail.html",
        {
            "order": order,
            "items": order.items.all(),
            "role": role_for(request.user),
        }
    )


# ============================================================
# ELIMINAR COMPRA DESDE ADMINISTRACIÓN
# ============================================================

@admin_required
def admin_order_delete(
    request,
    order_id
):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == "POST":

        order_number = order.id

        order.delete()

        messages.success(
            request,
            f"La compra #{order_number} "
            "fue eliminada del historial."
        )

        return redirect(
            "admin_orders"
        )

    return render(
        request,
        "vault/admin_order_delete.html",
        {
            "order": order,
            "role": role_for(request.user),
        }
    )


# ============================================================
# CONTROL DE ACCESO
# ============================================================

@admin_required
def admin_access(request):

    restricted_users = (
        User.objects
        .filter(
            groups__name__in=[
                "Operador",
                "Consulta",
            ]
        )
        .distinct()
        .order_by(
            "username"
        )
    )

    # --------------------------------------------------------
    # ASEGURAR QUE CADA USUARIO RESTRINGIDO TENGA
    # SU CONFIGURACIÓN DE ACCESO
    # --------------------------------------------------------

    for user in restricted_users:

        UserAccess.objects.get_or_create(
            user=user
        )

    restricted_users = (
        User.objects
        .filter(
            groups__name__in=[
                "Operador",
                "Consulta",
            ]
        )
        .distinct()
        .prefetch_related(
            "groups",
            "access_control"
        )
        .order_by(
            "username"
        )
    )

    return render(
        request,
        "vault/admin_access.html",
        {
            "users": restricted_users,
            "role": role_for(request.user),
        }
    )

# ============================================================
# EDITAR HORARIO DE ACCESO
# ============================================================

@admin_required
def admin_access_edit(
    request,
    user_id
):

    user = get_object_or_404(
        User,
        id=user_id
    )

    # --------------------------------------------------------
    # SOLO OPERADOR Y CONSULTA
    # --------------------------------------------------------

    if not user.groups.filter(
        name__in=[
            "Operador",
            "Consulta",
        ]
    ).exists():

        messages.error(
            request,
            "El control de acceso solo se aplica "
            "a usuarios Operador y Consulta."
        )

        return redirect(
            "admin_access"
        )

    # --------------------------------------------------------
    # OBTENER O CREAR CONFIGURACIÓN
    # --------------------------------------------------------

    access, created = UserAccess.objects.get_or_create(
        user=user
    )

    # --------------------------------------------------------
    # GUARDAR CAMBIOS
    # --------------------------------------------------------

    if request.method == "POST":

        form = UserAccessForm(
            request.POST,
            instance=access
        )

        if form.is_valid():

            # Guardamos el formulario sin confirmar todavía.
            saved_access = form.save(
                commit=False
            )

            # ------------------------------------------------
            # GUARDADO EXPLÍCITO DE SIN RESTRICCIÓN HORARIA
            # ------------------------------------------------
            #
            # Los checkbox HTML solamente aparecen en POST
            # cuando están marcados.
            #
            # Marcado    -> True
            # Desmarcado -> False
            #
            saved_access.unrestricted_hours = (
                "unrestricted_hours" in request.POST
            )

            # Guardar definitivamente en la base de datos.
            saved_access.save()

            messages.success(
                request,
                f"Configuración de acceso de "
                f"{user.username} guardada correctamente."
            )

            return redirect(
                "admin_access"
            )

        else:

            messages.error(
                request,
                "No se pudo guardar la configuración. "
                "Revisa los campos marcados."
            )

    else:

        form = UserAccessForm(
            instance=access
        )

    # --------------------------------------------------------
    # MOSTRAR FORMULARIO
    # --------------------------------------------------------

    return render(
        request,
        "vault/admin_access_form.html",
        {
            "form": form,
            "user_record": user,
            "access": access,
            "role": role_for(request.user),
        }
    )


# ============================================================
# SUSPENDER / HABILITAR USUARIO
# ============================================================

@admin_required
def admin_access_toggle(
    request,
    user_id
):

    user = get_object_or_404(
        User,
        id=user_id
    )

    # --------------------------------------------------------
    # SOLO OPERADOR Y CONSULTA
    # --------------------------------------------------------

    if not user.groups.filter(
        name__in=[
            "Operador",
            "Consulta",
        ]
    ).exists():

        messages.error(
            request,
            "Este usuario no utiliza control de acceso."
        )

        return redirect(
            "admin_access"
        )

    # --------------------------------------------------------
    # OBTENER O CREAR CONFIGURACIÓN
    # --------------------------------------------------------

    access, created = UserAccess.objects.get_or_create(
        user=user
    )

    # --------------------------------------------------------
    # CAMBIAR ESTADO
    # --------------------------------------------------------

    if request.method == "POST":

        access.enabled = not access.enabled

        access.save(
            update_fields=[
                "enabled",
                "updated_at",
            ]
        )

        if access.enabled:

            messages.success(
                request,
                f"Acceso de {user.username} habilitado."
            )

        else:

            messages.warning(
                request,
                f"Acceso de {user.username} suspendido."
            )

    return redirect(
        "admin_access"
    )
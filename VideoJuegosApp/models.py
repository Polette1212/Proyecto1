from datetime import time

from django.conf import settings
from django.db import models


class GamerProfile(models.Model):
    """Mantenedor de jugadores registrados en GameVault."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gamer_profile"
    )

    nickname = models.CharField(
        max_length=40,
        unique=True
    )

    favorite_genre = models.CharField(
        max_length=60,
        blank=True
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "perfil gamer"
        verbose_name_plural = "perfiles gamer"

    def __str__(self):
        return self.nickname


class Game(models.Model):
    """Mantenedor de videojuegos disponibles para la tienda y biblioteca."""

    title = models.CharField(
        "título",
        max_length=120
    )

    genre = models.CharField(
        "género",
        max_length=60
    )

    platform = models.CharField(
        "plataforma",
        max_length=60
    )

    launch_year = models.PositiveIntegerField(
        "año de lanzamiento"
    )

    synopsis = models.TextField(
        "sinopsis"
    )

    price = models.DecimalField(
        "precio",
        max_digits=10,
        decimal_places=0,
        default=0
    )

    stock = models.PositiveIntegerField(
        "stock",
        default=0
    )

    cover = models.ImageField(
        "portada",
        upload_to="covers/",
        blank=True,
        null=True
    )

    technical_sheet = models.FileField(
        "ficha técnica",
        upload_to="technical_sheets/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["title"]

        verbose_name = "videojuego"
        verbose_name_plural = "videojuegos"

    def __str__(self):
        return self.title


class LibraryEntry(models.Model):
    """Transacción que relaciona un perfil gamer con un videojuego."""

    STATUS_CHOICES = [
        ("pendiente", "Pendiente"),
        ("jugando", "Jugando"),
        ("completado", "Completado"),
    ]

    gamer = models.ForeignKey(
        GamerProfile,
        on_delete=models.CASCADE,
        related_name="library_entries"
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="library_entries"
    )

    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default="pendiente"
    )

    score = models.PositiveSmallIntegerField(
        "puntuación",
        null=True,
        blank=True
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-added_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["gamer", "game"],
                name="unique_game_per_gamer"
            )
        ]

        verbose_name = "entrada de biblioteca"
        verbose_name_plural = "entradas de biblioteca"

    def __str__(self):
        return f"{self.gamer} - {self.game}"


# ============================================================
# CARRITO DE COMPRA
# ============================================================


class Cart(models.Model):
    """
    Carrito de compra.

    Puede pertenecer a un usuario registrado
    o a un visitante identificado mediante session_key.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        null=True,
        blank=True
    )

    session_key = models.CharField(
        max_length=40,
        unique=True,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def total(self):
        return sum(
            item.subtotal()
            for item in self.items.select_related("game")
        )

    def __str__(self):

        if self.user:
            return f"Carrito de {self.user.username}"

        return f"Carrito visitante {self.session_key}"


class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="cart_items"
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "game"],
                name="unique_game_per_cart"
            )
        ]

    def subtotal(self):
        return self.game.price * self.quantity

    def __str__(self):

        if self.cart.user:
            owner = self.cart.user.username
        else:
            owner = "Visitante"

        return (
            f"{owner} - "
            f"{self.game.title} x {self.quantity}"
        )


# ============================================================
# PEDIDOS / COMPRAS
# ============================================================


class Order(models.Model):

    STATUS_CHOICES = [
        ("pendiente", "Pendiente"),
        ("pagada", "Pagada"),
        ("cancelada", "Cancelada"),
    ]

    PAYMENT_CHOICES = [
        (
            "tarjeta",
            "Tarjeta de crédito o débito"
        ),
        (
            "webpay",
            "Webpay"
        ),
    ]

    CUSTOMER_TYPE_CHOICES = [
        (
            "registrado",
            "Cliente registrado"
        ),
        (
            "visitante",
            "Visitante"
        ),
    ]

    # --------------------------------------------------------
    # USUARIO
    # --------------------------------------------------------

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True
    )

    # --------------------------------------------------------
    # DATOS DEL CLIENTE
    # --------------------------------------------------------

    customer_name = models.CharField(
        "nombre completo",
        max_length=120,
        default=""
    )

    customer_rut = models.CharField(
        "RUT",
        max_length=20,
        default=""
    )

    customer_email = models.EmailField(
        "correo electrónico",
        max_length=150,
        default=""
    )

    customer_phone = models.CharField(
        "teléfono",
        max_length=30,
        default=""
    )

    shipping_address = models.CharField(
        "dirección de despacho",
        max_length=250,
        default=""
    )

    customer_type = models.CharField(
        "tipo de cliente",
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default="registrado"
    )

    # --------------------------------------------------------
    # DATOS DE LA COMPRA
    # --------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        "estado",
        max_length=20,
        choices=STATUS_CHOICES,
        default="pendiente"
    )

    payment_method = models.CharField(
        "método de pago",
        max_length=20,
        choices=PAYMENT_CHOICES
    )

    # --------------------------------------------------------
    # VALORES ECONÓMICOS
    # --------------------------------------------------------

    subtotal = models.DecimalField(
        "subtotal",
        max_digits=12,
        decimal_places=0,
        default=0
    )

    discount = models.DecimalField(
        "descuento",
        max_digits=12,
        decimal_places=0,
        default=0
    )

    total = models.DecimalField(
        "total",
        max_digits=12,
        decimal_places=0,
        default=0
    )

    class Meta:
        ordering = ["-created_at"]

        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):

        if self.user:
            return f"Pedido #{self.id} - {self.user.username}"

        return f"Pedido #{self.id} - Visitante"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.PROTECT,
        related_name="order_items"
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=0
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )

    def __str__(self):

        return (
            f"{self.game.title} x "
            f"{self.quantity}"
        )


# ============================================================
# CONTROL DE ACCESO DE USUARIOS
# ============================================================


class UserAccess(models.Model):
    """
    Control de acceso para usuarios con roles Operador o Consulta.

    Permite:
    - Habilitar o suspender manualmente una cuenta.
    - Acceso sin restricción horaria.
    - Definir hora de inicio de acceso.
    - Definir hora de término de acceso.

    El Administrador no queda limitado por este control.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_control"
    )

    enabled = models.BooleanField(
        "acceso habilitado",
        default=True
    )

    unrestricted_hours = models.BooleanField(
        "sin restricción horaria",
        default=False
    )

    access_start = models.TimeField(
        "inicio de acceso",
        default=time(8, 0)
    )

    access_end = models.TimeField(
        "término de acceso",
        default=time(18, 0)
    )

    updated_at = models.DateTimeField(
        "última actualización",
        auto_now=True
    )

    class Meta:
        verbose_name = "control de acceso"
        verbose_name_plural = "controles de acceso"
        ordering = ["user__username"]

    def __str__(self):

        estado = (
            "Habilitado"
            if self.enabled
            else "Suspendido"
        )

        if self.unrestricted_hours:
            return (
                f"{self.user.username} - "
                f"{estado} - "
                "Sin restricción horaria"
            )

        return (
            f"{self.user.username} - "
            f"{estado} - "
            f"{self.access_start.strftime('%H:%M')} a "
            f"{self.access_end.strftime('%H:%M')}"
        )
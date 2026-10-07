from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import (
    Game,
    GamerProfile,
    Order,
)

from .serializers import (
    GameSerializer,
    GamerProfileSerializer,
    OrderSerializer,
)


class RoleBasedViewSet(viewsets.ModelViewSet):
    """
    Permisos según el rol de GameVault:

    Administrador:
        GET, POST, PUT, PATCH, DELETE

    Operador:
        GET, POST, PUT, PATCH

    Consulta:
        GET
    """

    permission_classes = [IsAuthenticated]

    def role(self):

        user = self.request.user

        if user.is_superuser:
            return "Administrador"

        if user.groups.filter(
            name="Administrador"
        ).exists():
            return "Administrador"

        if user.groups.filter(
            name="Operador"
        ).exists():
            return "Operador"

        if user.groups.filter(
            name="Consulta"
        ).exists():
            return "Consulta"

        return None

    def check_role_permission(self):

        role = self.role()

        if role == "Administrador":

            return True

        if role == "Operador":

            return self.request.method in [
                "GET",
                "POST",
                "PUT",
                "PATCH",
            ]

        if role == "Consulta":

            return self.request.method == "GET"

        return False

    def initial(
        self,
        request,
        *args,
        **kwargs
    ):

        super().initial(
            request,
            *args,
            **kwargs
        )

        if not self.check_role_permission():

            raise PermissionDenied(
                detail=(
                    "No tienes permisos para realizar "
                    "esta operación."
                )
            )


class GameViewSet(RoleBasedViewSet):

    queryset = (
        Game.objects
        .all()
        .order_by("id")
    )

    serializer_class = GameSerializer


class GamerProfileViewSet(RoleBasedViewSet):

    queryset = (
        GamerProfile.objects
        .select_related("user")
        .all()
        .order_by("id")
    )

    serializer_class = GamerProfileSerializer


class OrderViewSet(RoleBasedViewSet):

    serializer_class = OrderSerializer

    def get_queryset(self):

        queryset = (
            Order.objects
            .select_related("user")
            .prefetch_related("items__game")
            .all()
            .order_by("-created_at")
        )

        role = self.role()

        if role == "Administrador":

            return queryset

        return queryset.filter(
            user=self.request.user
        )
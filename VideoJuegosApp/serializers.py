from django.db import transaction

from rest_framework import serializers

from .models import (
    Game,
    GamerProfile,
    Order,
    OrderItem,
)


class GameSerializer(serializers.ModelSerializer):

    class Meta:

        model = Game

        fields = [
            "id",
            "title",
            "genre",
            "platform",
            "launch_year",
            "synopsis",
            "price",
            "stock",
            "cover",
            "technical_sheet",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_price(self, value):

        if value < 0:

            raise serializers.ValidationError(
                "El precio no puede ser negativo."
            )

        return value

    def validate_stock(self, value):

        if value < 0:

            raise serializers.ValidationError(
                "El stock no puede ser negativo."
            )

        return value


class GamerProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:

        model = GamerProfile

        fields = [
            "id",
            "username",
            "nickname",
            "favorite_genre",
            "avatar",
        ]

        read_only_fields = [
            "id",
            "username",
        ]

    def validate(self, attrs):

        user = self.context["request"].user

        if GamerProfile.objects.filter(
            user=user
        ).exists():

            raise serializers.ValidationError(
                "El usuario autenticado ya tiene un perfil Gamer."
            )

        return attrs

    def create(self, validated_data):

        user = self.context["request"].user

        return GamerProfile.objects.create(
            user=user,
            **validated_data
        )


class OrderItemSerializer(serializers.ModelSerializer):

    game_title = serializers.CharField(
        source="game.title",
        read_only=True
    )

    class Meta:

        model = OrderItem

        fields = [
            "id",
            "game",
            "game_title",
            "quantity",
            "unit_price",
            "subtotal",
        ]

        read_only_fields = [
            "id",
            "game_title",
            "unit_price",
            "subtotal",
        ]


class OrderItemCreateSerializer(serializers.Serializer):

    game = serializers.PrimaryKeyRelatedField(
        queryset=Game.objects.all()
    )

    quantity = serializers.IntegerField(
        min_value=1
    )


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemCreateSerializer(
        many=True,
        write_only=True,
        required=False
    )

    user = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    order_items = OrderItemSerializer(
        source="items",
        many=True,
        read_only=True
    )

    class Meta:

        model = Order

        fields = [
            "id",
            "user",
            "customer_name",
            "customer_rut",
            "customer_email",
            "customer_phone",
            "shipping_address",
            "customer_type",
            "created_at",
            "status",
            "payment_method",
            "subtotal",
            "discount",
            "total",
            "items",
            "order_items",
        ]

        read_only_fields = [
            "id",
            "user",
            "created_at",
            "status",
            "subtotal",
            "discount",
            "total",
            "order_items",
        ]

    def get_fields(self):

        fields = super().get_fields()

        request = self.context.get(
            "request"
        )

        if request is None:

            return fields

        user = request.user

        is_admin = (
            user.is_superuser
            or user.groups.filter(
                name="Administrador"
            ).exists()
        )

        if not is_admin:

            sensitive_fields = [
                "customer_rut",
                "customer_phone",
                "shipping_address",
            ]

            for field_name in sensitive_fields:

                fields.pop(
                    field_name,
                    None
                )

        return fields

    def validate_items(self, value):

        if not value:

            raise serializers.ValidationError(
                "La orden debe contener al menos un videojuego."
            )

        game_ids = [
            item["game"].id
            for item in value
        ]

        if len(game_ids) != len(set(game_ids)):

            raise serializers.ValidationError(
                "No se puede repetir el mismo videojuego en una orden."
            )

        return value

    def create(self, validated_data):

        items_data = validated_data.pop(
            "items",
            []
        )

        if not items_data:

            raise serializers.ValidationError(
                {
                    "items": [
                        "La orden debe contener al menos un videojuego."
                    ]
                }
            )

        user = self.context["request"].user

        with transaction.atomic():

            games = {}

            for item_data in items_data:

                game_id = item_data["game"].id

                game = (
                    Game.objects
                    .select_for_update()
                    .get(pk=game_id)
                )

                quantity = item_data["quantity"]

                if game.stock < quantity:

                    raise serializers.ValidationError(
                        {
                            "items": [
                                (
                                    f"No hay stock suficiente para "
                                    f"'{game.title}'. "
                                    f"Stock disponible: {game.stock}."
                                )
                            ]
                        }
                    )

                games[game_id] = game

            order = Order.objects.create(
                user=user,
                status="pendiente",
                subtotal=0,
                discount=0,
                total=0,
                **validated_data
            )

            subtotal = 0

            for item_data in items_data:

                game = games[item_data["game"].id]

                quantity = item_data["quantity"]

                unit_price = game.price

                item_subtotal = (
                    unit_price * quantity
                )

                OrderItem.objects.create(
                    order=order,
                    game=game,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=item_subtotal
                )

                game.stock -= quantity

                game.save(
                    update_fields=["stock"]
                )

                subtotal += item_subtotal

            discount = 0

            total = subtotal - discount

            order.subtotal = subtotal
            order.discount = discount
            order.total = total

            order.save(
                update_fields=[
                    "subtotal",
                    "discount",
                    "total",
                ]
            )

        return order

    def update(
        self,
        instance,
        validated_data
    ):

        validated_data.pop(
            "items",
            None
        )

        protected_fields = [
            "user",
            "status",
            "subtotal",
            "discount",
            "total",
        ]

        for field_name in protected_fields:

            validated_data.pop(
                field_name,
                None
            )

        with transaction.atomic():

            for attr, value in validated_data.items():

                setattr(
                    instance,
                    attr,
                    value
                )

            instance.save()

        return instance
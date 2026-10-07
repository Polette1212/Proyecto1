from rest_framework.routers import DefaultRouter

from .api_views import (
    GameViewSet,
    GamerProfileViewSet,
    OrderViewSet,
)


router = DefaultRouter()

router.register(
    r"games",
    GameViewSet,
    basename="games"
)

router.register(
    r"gamers",
    GamerProfileViewSet,
    basename="gamers"
)

router.register(
    r"orders",
    OrderViewSet,
    basename="orders"
)


urlpatterns = router.urls
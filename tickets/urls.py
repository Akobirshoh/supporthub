from rest_framework.routers import SimpleRouter

from .views import CategoryViewSet, TicketViewSet

router = SimpleRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("tickets", TicketViewSet, basename="ticket")

urlpatterns = router.urls

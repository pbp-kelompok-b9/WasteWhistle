from rest_framework.routers import DefaultRouter

from .api_views import RewardViewSet

router = DefaultRouter()
router.register("rewards", RewardViewSet, basename="reward")

urlpatterns = router.urls
from .api_views import RewardViewSet


from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register("rewards", RewardViewSet, basename="reward")
urlpatterns = router.urls
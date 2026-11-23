from rest_framework.routers import DefaultRouter

from .views import BookViewSet, LoanRequestViewSet

router = DefaultRouter()
router.register("books", BookViewSet, basename="book")
router.register("loans", LoanRequestViewSet, basename="loan")

urlpatterns = router.urls

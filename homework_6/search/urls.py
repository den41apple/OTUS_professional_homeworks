from django.urls import path

from hasker.api.router import router
from .api.views import SearchApiViewSet
from .views import SearchView

app_name = "search"

router.register("search", SearchApiViewSet, basename="api_search")

urlpatterns = [
    path("search/", SearchView.as_view(), name="search")
]

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from qna.api.views import QuestionsApiViewSetBase
from ..views import SearchView


class SearchApiViewSet(QuestionsApiViewSetBase):
    q = openapi.Parameter('q', in_=openapi.IN_QUERY,
                          description="Search text",
                          type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[q, ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        search_text = self.request.query_params.get("q", "")
        search_text = search_text.lower()
        if search_text.startswith("tag:"):
            return SearchView.get_tag_queryset(search_text)
        return SearchView.get_text_queryset(search_text)

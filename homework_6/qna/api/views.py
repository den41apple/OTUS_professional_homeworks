from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from hasker.context import trending_questions_queryset
from .serializers import QuestionSerializer, AnswersSerializer
from ..models import Question, Answer
from ..views import IndexView


class Pagination(PageNumberPagination):
    page_size = IndexView.questions_on_page
    page_size_query_param = "page_size"
    max_page_size = 1_000


class QuestionsApiViewSetBase(mixins.ListModelMixin,
                              GenericViewSet):
    """Для переиспользования"""
    queryset = (Question
                .objects
                .order_by("-created_at")
                .all())
    serializer_class = QuestionSerializer
    pagination_class = Pagination


class QuestionsApiViewSet(mixins.RetrieveModelMixin,
                          QuestionsApiViewSetBase):
    pass


class AnswersApiViewSet(mixins.ListModelMixin,
                        GenericViewSet):
    model = Answer
    serializer_class = AnswersSerializer
    pagination_class = Pagination

    question_id = openapi.Parameter("question_id",
                                    in_=openapi.IN_QUERY,
                                    description="Id of question",
                                    type=openapi.TYPE_INTEGER,
                                    required=True)

    @swagger_auto_schema(manual_parameters=[question_id, ])
    def list(self, request, *args, **kwargs):
        question_id = request.query_params.get('question_id')
        error_message = None
        if not question_id:
            error_message = 'Missing required query parameter "question_id"'
        else:
            invalid_message = self._check_question_id_parameter(question_id)
            if invalid_message:
                error_message = invalid_message
        if error_message:
            return Response({
                "error": error_message
            },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return super().list(request, *args, **kwargs)

    @staticmethod
    def _check_question_id_parameter(question_id):
        try:
            int(question_id)
        except:
            return 'Invalid value for query parameter "question_id"'

    def get_queryset(self):
        question_id = self.request.query_params["question_id"]
        qs = (Answer.objects
              .select_related("question")
              .filter(question_id=question_id)
              .order_by("-created_at")
              .all())
        return qs


class TrendingApiView(mixins.ListModelMixin,
                      GenericViewSet):
    queryset = trending_questions_queryset
    serializer_class = QuestionSerializer

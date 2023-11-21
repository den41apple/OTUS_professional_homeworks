from django.urls import path

from hasker.api.router import router
from .api.views import QuestionsApiViewSet, TrendingApiView, AnswersApiViewSet
from .views import IndexView, AskQuestionView, QuestionDetailView, VoteView

app_name = "qna"


router.register("questions", QuestionsApiViewSet, basename="api_questions")
router.register("trending", TrendingApiView, basename="api_trending")
router.register("answers", AnswersApiViewSet, basename="api_answers")

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("ask/", AskQuestionView.as_view(), name="ask"),
    path("question/<int:pk>", QuestionDetailView.as_view(), name="question"),
    path("vote/", VoteView.as_view(), name="vote"),


]

from django.urls import path

from .views import IndexView, AskQuestionView, QuestionDetailView, VoteView

app_name = "qna"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("ask/", AskQuestionView.as_view(), name="ask"),
    path("question/<int:pk>", QuestionDetailView.as_view(), name="question"),
    path("vote/", VoteView.as_view(), name="vote"),
]

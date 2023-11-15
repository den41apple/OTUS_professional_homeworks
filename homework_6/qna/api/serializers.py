from rest_framework import serializers

from ..models import Question, Answer


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        exclude = "tag",

    author = serializers.SlugRelatedField(slug_field="username", read_only=True)
    tags = serializers.SlugRelatedField(slug_field="text", read_only=True, many=True, source="tag")


class AnswersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        exclude = "question",

    author = serializers.SlugRelatedField(slug_field="username",
                                          read_only=True)
    question_id = serializers.SlugRelatedField(slug_field="id",
                                               read_only=True,
                                               source="question")

from django import forms
from django.core.exceptions import ValidationError

from .models import Question, Answer


class AskForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = "title", "text", "tags"

    @staticmethod
    def three_tags_validator(value: str):
        """Проверка, чтоб было не более 3-х тэгов"""
        tags = value.split(",")
        if len(tags) > 3:
            raise ValidationError("No more than 3 tags are allowed")

    tags = forms.CharField(required=False, validators=[three_tags_validator])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial = {"title": None,
                        "text": None}
        self.fields["tags"].widget.attrs["placeholder"] = "tag1, tag2, tag3 ..."


class QuestionDetailForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = "text",


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial = {"text": None}
        self.fields["text"].label = False
        self.fields["text"].widget.attrs["placeholder"] = "..."
        self.fields["text"].widget.attrs["rows"] = 3

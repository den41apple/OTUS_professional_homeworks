from django.contrib import admin

from .models import Tag, Question, Answer, Vote

admin.site.register(Tag)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Vote)

#tasks/forms.py

from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Task, Comment


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "body")

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter task title",
                }
            ),

            "body": CKEditor5Widget(
                attrs={
                    "class": "django_ckeditor_5",
                },
                config_name="extends",
            ),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("comment",)
# tasks/urls.py
from django.urls import path

from .views import (
    TaskListView,
    TaskDetailView,
    TaskUpdateView,
    TaskDeleteView,
    TaskCreateView,
)

urlpatterns = [
    path("<int:pk>/", TaskDetailView.as_view(), name="task_detail"),
    path("<int:pk>/edit/", TaskUpdateView.as_view(), name="task_edit"),
    path("<int:pk>/delete/", TaskDeleteView.as_view(), name="task_delete"),
    path("new/", TaskCreateView.as_view(), name="task_new"),
    path("", TaskListView.as_view(), name="task_list"), 
]

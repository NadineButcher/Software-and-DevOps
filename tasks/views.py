# tasks/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from django.urls import reverse_lazy, reverse

from .forms import CommentForm
from .models import Task

class CommentGet(DetailView):
    model = Task
    template_name = "task_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        return context
    
class CommentPost(SingleObjectMixin, FormView):
    model = Task
    form_class = CommentForm
    template_name = "task_detail.html"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.task = self.object
        comment.author = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        task = self.object
        return reverse("task_detail", kwargs={"pk": task.pk})

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "task_list.html"

class TaskDetailView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        view = CommentGet.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = CommentPost.as_view()
        return view(request, *args, **kwargs)

class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    fields = (
        "title",
        "body",
    )
    template_name = "task_edit.html"

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user

class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Task
    template_name = "task_delete.html"
    success_url = reverse_lazy("task_list")

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = "task_new.html"
    fields = ("title", "body")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
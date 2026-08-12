# tasks/views.py

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.utils.decorators import method_decorator

from django.urls import reverse_lazy, reverse

from django_ratelimit.decorators import ratelimit

from .forms import CommentForm, TaskForm
from .models import Task


# ============================================================
# COMMENTS
# ============================================================

class CommentGet(LoginRequiredMixin,DetailView):

    model = Task
    template_name = "task_detail.html"

    @method_decorator(
        ratelimit(
            key="ip",
            rate="20/m",
            method="GET",
            block=True,
        )
    )
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        return context


class CommentPost(LoginRequiredMixin, SingleObjectMixin, FormView):

    model = Task
    form_class = CommentForm
    template_name = "task_detail.html"

    @method_decorator(
        ratelimit(
            key="ip",
            rate="10/m",
            method="POST",
            block=True,
        )
    )

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user

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
        return reverse(
            "task_detail",
            kwargs={"pk": task.pk}
        )


# ============================================================
# TASK LIST
# ============================================================

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "task_list.html"

    @method_decorator(
        ratelimit(
            key="ip",
            rate="20/m",
            method="GET",
            block=True,
        )
    )
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# ============================================================
# TASK DETAIL
# ============================================================

class TaskDetailView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        view = CommentGet.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = CommentPost.as_view()
        return view(request, *args, **kwargs)


# ============================================================
# TASK UPDATE
# ============================================================

class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):

    model = Task
    form_class = TaskForm
    template_name = "task_edit.html"

    @method_decorator(
            ratelimit(
                key="ip",
                rate="5/m",
                method="POST",
                block=True,
            )
        )
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user

# ============================================================
# TASK DELETE
# ============================================================

class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):

    model = Task
    template_name = "task_delete.html"
    success_url = reverse_lazy("task_list")


    @method_decorator(
        ratelimit(
            key="ip",
            rate="5/m",
            method="POST",
            block=True,
        )
    )
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


# ============================================================
# TASK CREATE
# ============================================================

class TaskCreateView(LoginRequiredMixin, CreateView):

    model = Task
    form_class = TaskForm
    template_name = "task_new.html"

    @method_decorator(
        ratelimit(
            key="ip",
            rate="5/m",
            method="POST",
            block=True,
        )
    )

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

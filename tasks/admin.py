# tasks/admin.py
from django.contrib import admin
from .models import Task, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

class TaskAdmin(admin.ModelAdmin):
    inlines = [
        CommentInline,
    ]
    list_display = [
        "title",
        "body",
        "author",
    ]

admin.site.register(Task, TaskAdmin)
admin.site.register(Comment)
                    


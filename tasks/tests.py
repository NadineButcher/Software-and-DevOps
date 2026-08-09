#tasks/test.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Task


User = get_user_model()


class TaskModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        cls.task = Task.objects.create(
            title="This is a test task!",
            body="This is the test body.",
            author=cls.user,
        )

    def test_task_string(self):
        self.assertEqual(
            str(self.task),
            "This is a test task!",
        )

    def test_model_content(self):
        self.assertEqual(
            self.task.title,
            "This is a test task!",
        )

        self.assertEqual(
            self.task.body,
            "This is the test body.",
        )

        self.assertEqual(
            self.task.author,
            self.user,
        )

    
    def test_url_exists_at_correct_location(self):
        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse(
                "task_detail",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )    

    def test_homepage(self):
        response = self.client.get(
            reverse("home")
        )

        self.assertEqual(
            response.status_code,
            200,
        )
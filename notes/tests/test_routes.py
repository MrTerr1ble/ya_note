from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username="Автор",
            password="password"
        )
        cls.reader = User.objects.create(
            username="Читатель простой", password="readerpassword"
        )
        cls.notes = Note.objects.create(
            title="title", text="text", slug="slug", author=cls.author
        )

    def setUp(self):
        self.client.login(username="Автор", password="password")

    """Главная страница доступна анонимному пользователю"""

    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    """Аутентифицированному пользователю доступна
      страница со списком заметок notes/,
      страница успешного добавления заметки done/,
      страница добавления новой заметки add/"""

    def test_pages_availability(self):
        urls = (
            "notes:list",
            "notes:success",
            "notes:add",
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    """Страницы отдельной заметки,
    удаления и редактирования заметки
    доступны только автору заметки.
    Если на эти страницы попытается зайти другой пользователь—
    вернётся ошибка 404."""

    def test_404_for_non_author_user(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        self.client.logout()
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ("notes:edit", "notes:delete", "notes:detail"):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.notes.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    """При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи,
        страницу добавления заметки,
        отдельной заметки,
        редактирования или удаления заметки анонимный пользователь
        перенаправляется на страницу логина."""

    def test_redirect_for_anonymous_user(self):
        self.client.logout()

        login_url = reverse("users:login")

        protected_views = [
            ("notes:list", None),
            ("notes:success", None),
            ("notes:add", None),
            ("notes:edit", (self.notes.slug,)),
            ("notes:delete", (self.notes.slug,)),
            ("notes:detail", (self.notes.slug,)),
        ]

        for view_name, args in protected_views:
            with self.subTest(view_name=view_name):
                url = reverse(view_name, args=args)
                expected_redirect_url = f"{login_url}?next={url}"
                response = self.client.get(url)
                self.assertRedirects(response, expected_redirect_url)

    """Страницы регистрации пользователей,
    входа в учётную запись и
    выхода из неё доступны всем пользователям."""

    def test_pages_availability_for_all_users(self):
        urls = (
            "users:login",
            "users:logout",
            "users:signup",
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

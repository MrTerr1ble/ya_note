from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    """Класс тестов для проверки контента заметок и функциональности форм."""

    @classmethod
    def setUpTestData(cls):
        """Создает тестовых пользователей и заметки для тестов.

        Этот метод выполняется один раз для всего класса тестов. Он создаёт
        двух пользователей: автора и читателя,
        а также две заметки, принадлежащиесоответствующим пользователям.
        """
        cls.author = User.objects.create_user(
            username="Автор",
            password="password"
        )
        cls.reader = User.objects.create_user(
            username="Читатель",
            password="readerpassword"
        )
        cls.notes = Note.objects.create(
            title="title",
            text="text",
            slug="slug",
            author=cls.author
        )
        cls.other_notes = Note.objects.create(
            title="other_title",
            text="other_text",
            slug="other_slug",
            author=cls.reader
        )

    def setUp(self):
        """Авторизует тестового пользователя (автора) перед каждым тестом."""
        self.client.force_login(self.author)

    def test_note_redirect_object_list_in_context(self):
        """Проверяет наличие заметки автора на странице списка заметок.

        Убеждается, что заметка текущего авторизованного пользователя
        отображается на странице со списком заметок и
        содержится в context под ключом 'object_list'.
        """
        url = reverse("notes:list")
        response = self.client.get(url)
        self.assertIn("object_list", response.context)
        self.assertIn(self.notes, response.context["object_list"])

    def test_only_users_notes(self):
        """Проверяет отображение только заметок текущего пользователя.

        Убеждается, что в списке заметок отображаются
        только заметки текущего залогиненного пользователя,
        а заметки других пользователей не отображаются.
        """
        self.client.logout()
        self.client.force_login(self.reader)
        url = reverse("notes:list")
        response = self.client.get(url)
        self.assertIn(self.other_notes, response.context["object_list"])
        self.assertNotIn(self.notes, response.context["object_list"])

    def test_client_has_form(self):
        """Проверяет наличие формы для создания и редактирования заметок.

        Убеждается, что страницы создания и редактирования заметок содержат в
        context объект формы для ввода данных.
        """
        urls_with_forms = [
            ("notes:add", None),
            ("notes:edit", (self.notes.slug,)),
        ]

        for view_name, args in urls_with_forms:
            with self.subTest(view_name=view_name):
                url = reverse(view_name, args=args)
                response = self.client.get(url)
                self.assertIn("form", response.context)
                self.assertIsInstance(response.context["form"], NoteForm)

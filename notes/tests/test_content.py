from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):
    @classmethod
    def setUpTestData(cls):
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
        self.client.force_login(self.author)

    """Проверка, что отдельная заметка передаётся
    на страницу со списком заметок в списке object_list в словаре context"""

    def test_note_redirect_object_list_in_context(self):
        url = reverse("notes:list")
        response = self.client.get(url)
        self.assertIn("object_list", response.context)
        self.assertIn(self.notes, response.context["object_list"])

    """Проверка, что в список заметок одного пользователя
    не попадают заметки другого пользователя"""

    def test_only_users_notes(self):
        self.client.logout()
        self.client.force_login(self.reader)
        url = reverse("notes:list")
        response = self.client.get(url)
        self.assertIn(self.other_notes, response.context["object_list"])
        self.assertNotIn(self.notes, response.context["object_list"])

    """Проверка, что на страницы создания и редактирования
    заметки передаются формы."""

    def test_client_has_form(self):
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

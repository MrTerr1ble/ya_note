from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class TestLogic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username="Автор",
            password="password"
        )
        cls.create_url = reverse("notes:add")
        cls.success_url = reverse("notes:success")
        cls.form_data = {
            "title": "New Title",
            "text": "New Text",
            "slug": "new-slug",
        }

    def setUp(self):
        self.client.force_login(self.author)

    def create_note_as_authenticated_user(self):
        return self.client.post(self.create_url, data=self.form_data)

    """Проверка, что залогиненный пользователь может создать заметку."""

    def test_authenticated_user_can_create_note(self):
        initial_note_count = Note.objects.count()
        response = self.create_note_as_authenticated_user()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Note.objects.count(), initial_note_count + 1)

    """Проверка, что анонимный не пользователь может создать заметку."""

    def test_anonymous_user_cannot_create_note(self):
        self.client.logout()
        initial_note_count = Note.objects.count()
        response = self.client.post(self.create_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Note.objects.count(), initial_note_count)

    """Проверка, что при создании заметки не заполнен slug,
    то он формируется автоматически."""

    def test_empty_slug(self):
        self.form_data.pop("slug")
        response = self.create_note_as_authenticated_user()
        self.assertRedirects(response, self.success_url)
        new_note = Note.objects.latest("id")
        self.assertEqual(new_note.slug, slugify(self.form_data["title"]))

    """Проверка, что невозможно создать две заметки с одинаковым slug."""

    def test_unique_slug_for_note(self):
        self.create_note_as_authenticated_user()
        response = self.create_note_as_authenticated_user()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        note_count = Note.objects.filter(slug=self.form_data["slug"]).count()
        self.assertEqual(note_count, 1)


"""Класс для проверки, что пользователь может редактировать и удалять
свои заметки, но не может редактировать или удалять чужие."""


class TestNoteEditDelete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username="Автор новости", password="password"
        )
        cls.reader = User.objects.create_user(
            username="Читатель",
            password="password"
        )
        cls.notes = Note.objects.create(
            title="Заголовок", text="text", author=cls.author
        )
        cls.edit_url = reverse("notes:edit", args=(cls.notes.slug,))
        cls.delete_url = reverse("notes:delete", args=(cls.notes.slug,))
        cls.success_url = reverse("notes:success")
        cls.form_data = {
            "title": "New Title",
            "text": "New Text",
            "slug": slugify("New Title"),
        }

    def setUp(self):
        self.author_client = self.client
        self.author_client.force_login(self.author)
        self.reader_client = Client()
        self.reader_client.force_login(self.reader)

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, self.form_data["text"])

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, "text")

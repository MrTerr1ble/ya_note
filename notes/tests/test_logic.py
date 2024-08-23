from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):
    """Класс тестов для проверки логики создания заметок."""

    @classmethod
    def setUpTestData(cls):
        """Создает тестового пользователя и данные для формы.

        Метод создаёт пользователя (автора), URL для создания и успешного
        добавления заметки, а также данные формы для создания новой заметки.
        """
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
        """Авторизует тестового пользователя (автора) перед каждым тестом."""
        self.client.force_login(self.author)

    def create_note_as_authenticated_user(self):
        """Создает заметку от имени авторизованного пользователя.

        Returns:
            HttpResponse: Ответ на запрос создания заметки.
        """
        return self.client.post(self.create_url, data=self.form_data)

    def test_authenticated_user_can_create_note(self):
        """Проверяет, что авторизованный пользователь может создать заметку.

        Убеждается, что после создания заметки
        статус ответа равен HTTP 302 (FOUND),
        а количество заметок увеличивается на единицу.
        """
        initial_note_count = Note.objects.count()
        response = self.create_note_as_authenticated_user()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Note.objects.count(), initial_note_count + 1)

    def test_anonymous_user_cannot_create_note(self):
        """Проверяет, что анонимный пользователь не может создать заметку.

        Убеждается, что попытка создания заметки анонимным пользователем
        возвращает статус ответа HTTP 302 (FOUND),
        а количество заметок остаётся неизменным.
        """
        self.client.logout()
        initial_note_count = Note.objects.count()
        response = self.client.post(self.create_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Note.objects.count(), initial_note_count)

    def test_empty_slug(self):
        """Проверяет автоматическую генерацию slug, если он не заполнен.

        Убеждается, что если при создании заметки не был указан slug, то он
        автоматически формируется на основе заголовка заметки.
        """
        self.form_data.pop("slug")
        response = self.create_note_as_authenticated_user()
        self.assertRedirects(response, self.success_url)
        new_note = Note.objects.latest("id")
        self.assertEqual(new_note.slug, slugify(self.form_data["title"]))

    def test_unique_slug_for_note(self):
        """Проверяет уникальность slug при создании заметок.

        Убеждается, что невозможно создать две заметки с одинаковым slug, и
        что в случае попытки создать заметку с повторяющимся slug статус ответа
        будет HTTP 200 (OK).
        """
        self.create_note_as_authenticated_user()
        response = self.create_note_as_authenticated_user()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        note_count = Note.objects.filter(slug=self.form_data["slug"]).count()
        self.assertEqual(note_count, 1)


class TestNoteEditDelete(TestCase):
    """Класс тестов для проверки прав на редактирование и удаление заметок."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт тестовых пользователей и заметку для тестов.

        Метод создаёт автора заметки и читателя, а также заметку,
        принадлежащую автору. Определяет URL для редактирования и удаления
        заметки.
        """
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
        """Авторизует тестовых пользователей перед каждым тестом."""
        self.author_client = self.client
        self.author_client.force_login(self.author)
        self.reader_client = Client()
        self.reader_client.force_login(self.reader)

    def test_author_can_delete_note(self):
        """Проверяет, что автор может удалить свою заметку.

        Убеждается, что после удаления заметки автором происходит редирект
        на страницу успеха, и количество заметок уменьшается до нуля.
        """
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cant_delete_note_of_another_user(self):
        """Проверяет, что пользователь не может удалить чужую заметку.

        Убеждается, что попытка удаления чужой заметки возвращает статус ответа
        HTTP 404 (NOT FOUND), а количество заметок остаётся неизменным.
        """
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        """Проверяет, что автор может редактировать свою заметку.

        Убеждается, что после редактирования заметки автором
        происходит редирект на страницу успеха,
        а содержимое заметки обновляется.
        """
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, self.form_data["text"])

    def test_user_cant_edit_note_of_another_user(self):
        """Проверяет, что пользователь не может редактировать чужую заметку.

        Убеждается, что попытка редактирования чужой заметки возвращает статус
        ответа HTTP 404 (NOT FOUND), а содержимое заметки остаётся неизменным.
        """
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, "text")

from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_post_str = post.text[:15]
        self.assertEqual(expected_post_str, str(post))

        group = PostModelTest.group
        expected_group_str = group.title
        self.assertEqual(expected_group_str, str(group))

    def test_verbose_name(self):
        """verbose_name полей text и group совпадают с ожидаемыми."""
        post = PostModelTest.post

        text_verbose = post._meta.get_field('text').verbose_name
        self.assertEqual(text_verbose, 'Текст поста')

        group_verbose = post._meta.get_field('group').verbose_name
        self.assertEqual(group_verbose, 'Group')

    def test_help_text(self):
        """help_text полей text и group совпадают с ожидаемыми."""
        post = PostModelTest.post

        text_help_text = post._meta.get_field('text').help_text
        self.assertEqual(text_help_text, 'Текст нового поста')

        group_help_text = post._meta.get_field('group').help_text
        self.assertEqual(group_help_text,
                         'Группа, к которой будет относиться пост')

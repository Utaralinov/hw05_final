from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Описание',
            slug='test_slug',
        )
        for i in range(1, 16):
            Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginators(self):
        second_page_size = Post.objects.count() - settings.PAGE_SIZE
        pages_posts_count = {
            reverse('posts:index'): settings.PAGE_SIZE,
            reverse('posts:index') + '?page=2': second_page_size,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): settings.PAGE_SIZE,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2':
                        second_page_size,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
                        settings.PAGE_SIZE,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2':
                        second_page_size,
        }

        for reverse_name, expected in pages_posts_count.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), expected)

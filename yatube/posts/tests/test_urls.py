from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        self.not_author = User.objects.create(username='NotAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.not_author)

    def test_unexisting_url(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_url_exist(self):
        urls = ['/',
                f'/group/{self.group.slug}/',
                # f'/profile/{self.user.username}/',
                f'/posts/{self.post.pk}/']

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_exists_authorized(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirects_unauthorized_on_login(self):
        response = self.client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_url_exists_for_author(self):
        path = f'/posts/{self.post.pk}/edit/'
        response = self.authorized_client_author.get(path)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_redirects_non_author_on_post_detail(self):
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_edit_url_redirects_unauthorized_on_login(self):
        response = self.client.get(f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.pk}/edit/')

    def test_comment_url_redirects_unauthorized_on_login(self):
        path = f'/posts/{self.post.pk}/comment/'
        response = self.client.post(path, data={}, follow=True)
        redirect_path = f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        self.assertRedirects(response, redirect_path)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

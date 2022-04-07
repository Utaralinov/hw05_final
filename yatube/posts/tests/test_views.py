import shutil
import tempfile

from django import forms
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.old_author = User.objects.create_user(username='OldAuthor')
        cls.author = User.objects.create_user(username='author')
        Follow.objects.create(
            user=cls.user,
            author=cls.old_author
        )
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Описание',
            slug='test_slug',
        )
        cls.empty_group = Group.objects.create(
            title='Пусто',
            description='Пустая группа',
            slug='no_posts',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.post_image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.post_image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.unsubscribed_client = Client()
        self.unsubscribed_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.pk}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'pid': self.post.pk}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_group_list_show_correct_context(self):
        path = reverse('posts:group_list',
                       kwargs={'slug': self.empty_group.slug})
        response = self.authorized_client.get(path)
        posts_list = response.context['page_obj']
        self.assertEqual(len(posts_list), 0)

    def test_index_page_cache(self):
        path = reverse('posts:index')
        response = self.authorized_client.get(path)
        content_before_delete = response.content
        Post.objects.last().delete()
        response = self.authorized_client.get(path)
        content_after_delete = response.content
        self.assertEqual(content_before_delete, content_after_delete)
        cache.clear()
        response = self.authorized_client.get(path)
        content_after_cache_clear = response.content
        self.assertNotEqual(content_after_cache_clear, content_before_delete)

    def test_post_list_pages_show_correct_context(self):
        paths = [reverse('posts:index'),
                 reverse('posts:group_list', kwargs={'slug': self.group.slug}),
                 reverse('posts:profile',
                         kwargs={'username': self.user.username})]

        for path in paths:
            with self.subTest(path=path):
                response = self.authorized_client.get(path)
                first_object = response.context['page_obj'][0]
                self.check_post_detail(first_object)

    def test_post_detail(self):
        path = reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        response = self.authorized_client.get(path)
        test_post = response.context['post']
        self.check_post_detail(test_post)

    def check_post_detail(self, post):
        self.assertEqual(post.pk, self.post.pk)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.user.username)
        self.assertEqual(post.group.slug, self.group.slug)
        self.assertEqual(post.image, f'posts/{self.post_image.name}')

    def test_create_form_show_correct_context(self):
        path = reverse('posts:post_create')
        self.form_show_correct_context(path)

    def test_edit_form_show_correct_context(self):
        path = reverse('posts:post_edit', kwargs={'pid': self.post.pk})
        self.form_show_correct_context(path)

    def form_show_correct_context(self, path):
        response = self.authorized_client.get(path)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_follow(self):
        following_count = Follow.objects.filter(user=self.user).count()
        path = reverse('posts:profile_follow',
                       kwargs={'username': self.author.username})
        response = self.authorized_client.get(path)
        redirect_path = reverse('posts:profile',
                                kwargs={'username': self.author.username})
        self.assertRedirects(response, redirect_path)
        self.assertEqual(following_count + 1,
                         Follow.objects.filter(user=self.user).count())
        self.assertTrue(Follow.objects.filter(user=self.user,
                        author=self.author).exists())

    def test_unfollow(self):
        following_count = Follow.objects.filter(user=self.user).count()
        path = reverse('posts:profile_unfollow',
                       kwargs={'username': self.old_author.username})
        response = self.authorized_client.get(path)
        redirect_path = reverse('posts:profile',
                                kwargs={'username': self.old_author.username})
        self.assertRedirects(response, redirect_path)
        self.assertEqual(following_count - 1,
                         Follow.objects.filter(user=self.user).count())
        self.assertFalse(Follow.objects.filter(user=self.user,
                         author=self.old_author).exists())

    def test_follower_follow_page(self):
        path = reverse('posts:follow_index')
        response = self.authorized_client.get(path)
        posts_count_before = len(response.context['page_obj'])
        new_post = Post.objects.create(author=self.old_author,
                                       text='Пост для подписчиков')
        response = self.authorized_client.get(path)
        first_post = response.context['page_obj'][0]
        posts_count_after = len(response.context['page_obj'])
        self.assertEqual(posts_count_before + 1, posts_count_after)
        self.assertEqual(new_post, first_post)

    def test_nonfollower_follow_page(self):
        path = reverse('posts:follow_index')
        response = self.unsubscribed_client.get(path)
        posts_count_before = len(response.context['page_obj'])
        Post.objects.create(author=self.old_author,
                            text='Пост для подписчиков')
        response = self.authorized_client.get(path)
        posts_count_after = len(response.context['page_obj'])
        self.assertEqual(posts_count_before + 1, posts_count_after)

    def test_follow_self(self):
        follower_count_before = self.user.follower.count()
        path = reverse('posts:profile_follow',
                       kwargs={'username': self.user.username})
        self.authorized_client.get(path)
        test_user = User.objects.get(username=self.user.username)
        self.assertEqual(test_user.follower.count(), follower_count_before)

    def test_follow_twice(self):
        path = reverse('posts:profile_follow',
                       kwargs={'username': self.old_author.username})
        with transaction.atomic():
            response = self.authorized_client.get(path)
        redirect_path = reverse('posts:profile',
                                kwargs={'username': self.old_author.username})
        self.assertRedirects(response, redirect_path)

import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        post_image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.pk,
            'image': post_image
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        path = reverse('posts:profile',
                       kwargs={'username': self.user.username})
        self.assertRedirects(response, path)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.all().order_by('pk').last()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.group, self.group)
        self.assertEqual(last_post.image, f'posts/{post_image.name}')

    def test_edit_post(self):
        path = reverse(('posts:post_detail'), kwargs={'post_id': self.post.pk})
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'pid': self.post.pk}),
            data=form_data,
            follow=True
        )
        edited_post = get_object_or_404(Post, pk=self.post.pk)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, path)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group, self.group)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Author')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        comments_count = Comment.objects.count()
        path = reverse('posts:add_comment', kwargs={'post_id': self.post.pk})
        form_data = {
            'text': 'Текст коментария'
        }
        response = self.authorized_client.post(path,
                                               data=form_data,
                                               follow=True)
        redirect_path = reverse('posts:post_detail',
                                kwargs={'post_id': self.post.pk})
        self.assertRedirects(response, redirect_path)
        self.assertEqual(Comment.objects.count(), comments_count + 1)

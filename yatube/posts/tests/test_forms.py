import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Test_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
        )
        cls.form = PostForm()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.uploaded1 = SimpleUploadedFile(
            name='small1.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form_comment_data = {
            'text': 'Текст комментария',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)

    def test_create_post(self):
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст2',
            'group': self.group.id,
            'image': self.uploaded
        }
        response = self.authorized_author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image=f'posts/{self.uploaded.name}'
            ).exists()
        )

    def test_edit_post(self):
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'image': self.uploaded1
        }
        response = self.authorized_author_client.post(
            reverse('posts:post_edit', args=(1,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', args=(1,)
            )
        )
        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image=f'posts/{self.uploaded1.name}'
            ).exists()
        )

    def test_cant_comment_guest_user(self):
        response = self.guest_client.post(
            reverse('posts:add_comment', args=(1,)),
            data=self.form_comment_data,
            follow=True
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=/posts/1/comment/'
        )

    def test_comment_for_athorized(self):
        response = self.authorized_author_client.post(
            reverse('posts:add_comment', args=(1,)),
            data=self.form_comment_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', args=(1,)
            )
        )
        response = self.authorized_author_client.get(
            reverse('posts:post_detail', args=(1,))
        )
        comment = response.context.get('comments')[0].text
        self.assertEqual(comment, self.form_comment_data['text'])

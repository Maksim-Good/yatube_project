from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Test_name_author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )
        cls.post_url = f'/posts/{cls.post.id}/'
        cls.public_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.author.username}/', 'posts/profile.html'),
            (cls.post_url, 'posts/post_detail.html'),
        )
        cls.authorized_urls = (
            ('/create/', 'posts/create_post.html'),
        )
        cls.private_urls = (
            (f'{cls.post_url}edit/', 'posts/create_post.html'),
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)
        cache.clear()

    def test_urls_uses_correct_template_for_authorized_author(self):
        self.all_urls = (
            self.public_urls
            + self.authorized_urls
            + self.private_urls
        )
        for url in self.all_urls:
            address, template = url
            with self.subTest(address=address):
                response = self.authorized_author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_authorized_user(self):
        self.all_urls = (
            self.public_urls
            + self.authorized_urls
        )
        for url in self.all_urls:
            address, template = url
            with self.subTest(address=address):
                response = self.authorized_author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_guest_client(self):
        for url in self.public_urls:
            address, template = url
            with self.subTest(address=address):
                response = self.authorized_author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_redirect_for_usernotauthor_on_detail(self):
        response = self.authorized_client.get(
            self.private_urls[0][0], follow=True
        )
        self.assertRedirects(response, self.post_url)

    def test_create_and_edit_redirect_anonymous_on_login(self):
        response = self.guest_client.get(
            self.authorized_urls[0][0], follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
        response = self.guest_client.get(self.private_urls[0][0], follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/'
        )

    def test_access_to_nonexistent_page_for_all_clients(self):
        clients = (
            self.guest_client,
            self.authorized_client,
            self.authorized_author_client
        )
        for client in clients:
            with self.subTest(client=client):
                self.my_client = client
                response = self.my_client.get('/nonexistent_page/')
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, 'core/404.html')

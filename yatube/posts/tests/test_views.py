import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()

POSTS_ON_PAGE = 10
NUMBER_ONE = 1


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author1 = User.objects.create_user(username='Test_name_author1')
        cls.author2 = User.objects.create_user(username='Test_name_author2')
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        Post.objects.bulk_create(
            (
                Post(
                    author=cls.author1,
                    text=f'Test {i}',
                    group=cls.group,
                    image=cls.uploaded,
                ) for i in range(13)
            ), 13
        )
        Post.objects.bulk_create(
            (
                Post(
                    author=cls.author2,
                    text=f'Testos {i}',
                    image=cls.uploaded,
                ) for i in range(13)
            ), 13
        )
        cls.follower = User.objects.create_user(username='HasNoName')
        Follow.objects.create(user=cls.follower, author=cls.author1)
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        cls.url_templates = (
            (reverse('posts:index'), 'posts/index.html'),
            (reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ), 'posts/group_list.html'),
            (reverse(
                'posts:profile', kwargs={'username': cls.author1.username}
            ), 'posts/profile.html'),
            (reverse(
                'posts:post_detail', kwargs={'post_id': NUMBER_ONE}
            ), 'posts/post_detail.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse(
                'posts:post_edit', kwargs={'post_id': NUMBER_ONE}
            ), 'posts/create_post.html'),
            (reverse(
                'posts:profile', kwargs={'username': cls.author2.username}
            ), 'posts/profile.html'),
            (reverse('posts:follow_index'), 'posts/follow.html'),
        )
        cls.index = cls.url_templates[0][0]
        cls.group_list = cls.url_templates[1][0]
        cls.profile1 = cls.url_templates[2][0]
        cls.post_detail = cls.url_templates[3][0]
        cls.post_create = cls.url_templates[4][0]
        cls.post_edit = cls.url_templates[5][0]
        cls.profile2 = cls.url_templates[6][0]
        cls.follow_index = cls.url_templates[7][0]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author1)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        cache.clear()

    def paginator_test(self, url, objs):
        for page in range(objs // POSTS_ON_PAGE + NUMBER_ONE):
            with self.subTest(page=page):
                response = self.client.get(url + f'?page={NUMBER_ONE + page}')
                if objs > POSTS_ON_PAGE:
                    pages = POSTS_ON_PAGE
                else:
                    pages = objs
                self.assertEqual(len(response.context['page_obj']), pages)
                objs -= POSTS_ON_PAGE

    def test_pages_uses_correct_template_for_author(self):
        for url in self.url_templates:
            reverse_name, template = url
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        self.paginator_test(self.index, 26)

    def test_group_posts_show_correct_context(self):
        self.paginator_test(self.group_list, 13)
        response = self.client.get(self.group_list)
        for post in range(POSTS_ON_PAGE):
            group_title = response.context.get('page_obj')[post].group.title
            self.assertEqual(group_title, self.group.title)

    def test_profile_posts_show_correct_context(self):
        self.paginator_test(self.profile1, 13)
        response = self.client.get(self.profile1)
        for post in range(POSTS_ON_PAGE):
            author = response.context.get('page_obj')[post].author.username
            self.assertEqual(author, self.author1.username)

    def test_detail_page_show_correct_context(self):
        response = self.client.get(self.post_detail)
        post_number = response.context.get('post').id
        self.assertEqual(post_number, NUMBER_ONE)

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_author_client.get(self.post_create)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        response = self.authorized_author_client.get(self.post_edit)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        form_fields_received = {
            'text': 'Test 0',
            'group': self.group.id,
        }
        for value, expected in form_fields_received.items():
            with self.subTest(value=value):
                form_field = response.context.get('form')[value].initial
                self.assertEqual(expected, form_field)

    def post_on_page(self, url, text, equal=True):
        response = self.client.get(url)
        new_text = response.context.get('page_obj')[0].text
        if equal:
            self.assertEqual(new_text, text)
        else:
            self.assertNotEqual(new_text, text)

    def test_new_post_appears_on_index_group_profile_pages(self):
        new_group = Group.objects.create(
            title='Новая группа',
            slug='cats',
            description='Новое тестовое описание'
        )
        new_post = Post.objects.create(
            author=self.author2,
            text='Новый пост',
            group=new_group
        )
        self.post_on_page(self.index, new_post.text)
        self.post_on_page(
            reverse('posts:group_list', kwargs={'slug': new_group.slug}),
            new_post.text
        )
        self.post_on_page(self.profile2, new_post.text)
        self.post_on_page(self.group_list, new_post.text, False)

    def image_test(self, url, obj_context, is_collable=True):
        response = self.client.get(url)
        if is_collable:
            image = response.context.get(obj_context)[0].image
            self.assertTrue(image)
        else:
            image = response.context.get(obj_context).image
            self.assertTrue(image)

    def test_a_image_in_context(self):
        self.image_test(self.index, 'page_obj')
        self.image_test(self.profile2, 'page_obj')
        self.image_test(self.group_list, 'page_obj')
        self.image_test(self.post_detail, 'post', False)

    def test_cache(self):
        response1 = self.client.get(self.index).content
        Post.objects.create(
            author=self.author2,
            text='Пост для кеша',
        )
        response2 = self.client.get(self.index).content
        self.assertEqual(response1, response2)
        cache.clear()
        response3 = self.client.get(self.index).content
        self.assertNotEqual(response1, response3)

    def post_for_follower(self):
        return self.follower_client.get(
            self.follow_index
        ).context.get('page_obj')[0].text

    def not_follower_get(self, url):
        return self.authorized_author_client.get(url)

    def test_subscribe_post_available(self):
        post1 = Post.objects.create(
            author=self.author1,
            text='Пост фоловера',
        )
        self.assertEqual(post1.text, self.post_for_follower())
        post2 = Post.objects.create(
            author=self.author2,
            text='Пост не для фоловера',
        )
        self.assertNotEqual(post2.text, self.post_for_follower())
        self.assertNotContains(
            self.authorized_author_client.get(self.follow_index),
            post1.text
        )

    def note_in_follow_db(self, user1, author):
        return Follow.objects.filter(
            user=user1,
            author=author
        ).exists()

    def test_follow_create_note_in_db(self):
        self.assertFalse(
            self.note_in_follow_db(self.follower, self.author2)
        )
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author2.username}
            )
        )
        self.assertTrue(
            self.note_in_follow_db(self.follower, self.author2)
        )

    def test_unfollow_delete_note_in_db(self):
        self.assertTrue(
            self.note_in_follow_db(self.follower, self.author1)
        )
        self.follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author1.username}
            )
        )
        self.assertFalse(
            self.note_in_follow_db(self.follower, self.author1)
        )

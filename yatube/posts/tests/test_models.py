from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длиннее 15 символов',
        )
        cls.post_spec = [
            {
                'field_name': 'text',
                'verbose_name': 'Текст',
                'help_text': 'Здесь нужно ввести основной текст поста.'
            },
            {
                'field_name': 'author',
                'verbose_name': 'Автор',
                'help_text': 'Здесь нужно ввести имя автора поста.'
            },
            {
                'field_name': 'group',
                'verbose_name': 'Группа',
                'help_text': 'Здесь можно ввести имя группы.'
            },
            {
                'field_name': 'image',
                'verbose_name': 'Картинка',
                'help_text': 'Здесь можно добавить картинку.'
            }
        ]
        cls.group_spec = [
            {
                'field_name': 'title',
                'verbose_name': 'Название группы',
                'help_text': 'Здесь нужно ввести имя группы.'
            },
            {
                'field_name': 'slug',
                'verbose_name': 'Тэг',
                'help_text': 'Здесь нужно задать Тэг (уникальное имя).'
            },
            {
                'field_name': 'description',
                'verbose_name': 'Описание группы',
                'help_text': 'Здесь должно быть описание группы.'
            }
        ]

    def fields(self, model, model_spec):
        for i in model_spec:
            with self.subTest(i=i):
                field = i['field_name']
                verbose = i['verbose_name']
                help_text = i['help_text']
                self.assertEqual(
                    model._meta.get_field(field).verbose_name, verbose
                )
                self.assertEqual(
                    model._meta.get_field(field).help_text, help_text
                )

    def test_models_have_correct_object_names(self):
        self.assertEqual(PostModelTest.post.text[:15], str(PostModelTest.post))
        group = PostModelTest.group
        self.assertEqual(group.title, str(self.group))

    def test_post_verbose_name_and_help_text(self):
        post = PostModelTest.post
        self.fields(post, self.post_spec)

    def test_post_verbose_name_and_help_text(self):
        group = PostModelTest.group
        self.fields(group, self.group_spec)

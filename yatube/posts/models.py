from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Здесь нужно ввести основной текст поста.',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text='Здесь нужно ввести имя автора поста.',
    )
    group = models.ForeignKey(
        'Group',
        related_name='posts',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        help_text='Здесь можно ввести имя группы.',
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Здесь можно добавить картинку.',
    )

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Здесь нужно ввести имя группы.',
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Тэг',
        help_text='Здесь нужно задать Тэг (уникальное имя).',
    )
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Здесь должно быть описание группы.'
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['title']

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Коментарий для поста',
        help_text='Здесь нужно выбрать пост к которому комментарий',

    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
        help_text='Здесь нужно ввести имя автора комментария.',
    )
    text = models.TextField(
        verbose_name='Комментарий',
        help_text='Здесь нужно ввести Ваш комментарий.',
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации поста.',
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created']

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Блогер',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follows'
            ),
            models.CheckConstraint(
                name="self_follow",
                check=~models.Q(user=models.F("author")),
            ),
        ]

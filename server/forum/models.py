from django.db import models
from django.conf import settings


class Post(models.Model):
    CATEGORY_CHOICES = [
        ('experience', '飞行心得'),
        ('debug', '调试求助'),
        ('showcase', '作品展示'),
        ('trade', '二手交流'),
        ('news', '行业资讯'),
        ('qa', '技术问答'),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField('标题', max_length=200)
    category = models.CharField('分类', max_length=30, choices=CATEGORY_CHOICES, db_index=True)
    content = models.TextField('内容')
    view_count = models.PositiveIntegerField('浏览数', default=0)
    like_count = models.PositiveIntegerField('点赞数', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '帖子'
        verbose_name_plural = '帖子'

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField('评论内容')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '评论'
        verbose_name_plural = '评论'

    def __str__(self):
        return f'{self.author} on {self.post}'


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

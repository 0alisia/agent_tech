from django.contrib.auth.models import AbstractUser
from django.db import models


class AppUser(AbstractUser):
    api_token = models.CharField('接口Token', max_length=64, blank=True, db_index=True)
    nickname = models.CharField('昵称', max_length=50, blank=True)
    bio = models.CharField('个人简介', max_length=255, blank=True)
    phone = models.CharField('手机号', max_length=20, blank=True)

    def display_name(self):
        return self.nickname or self.username

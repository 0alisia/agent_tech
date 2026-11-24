from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AppUser


@admin.register(AppUser)
class AppUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("扩展信息", {"fields": ("api_token", "nickname", "bio", "phone")}),)
    list_display = ('username', 'nickname', 'email', 'is_staff', 'date_joined')

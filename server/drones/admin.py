from django.contrib import admin
from .models import DroneDoc

@admin.register(DroneDoc)
class DroneDocAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'model_name', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'model_name', 'content')

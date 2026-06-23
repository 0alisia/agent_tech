from django.urls import path
from . import views

urlpatterns = [
    path('ask/', views.ask),
    path('weather/', views.weather_ask),
    path('history/', views.history),
    path('build-index/', views.build_index),
    path('search-preview/', views.search_preview),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list),
    path('create/', views.post_create),
    path('categories/', views.categories),
    path('<int:pk>/', views.post_detail),
    path('<int:pk>/edit/', views.post_update),
    path('<int:pk>/comment/', views.comment_create),
    path('<int:pk>/like/', views.post_like),
]

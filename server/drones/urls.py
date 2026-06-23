from django.urls import path
from . import views

urlpatterns = [
    path('', views.doc_list),
    path('create/', views.doc_create),
    path('categories/', views.categories),
    path('<int:pk>/', views.doc_detail),
    path('<int:pk>/edit/', views.doc_update),
]

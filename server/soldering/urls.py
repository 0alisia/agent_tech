from django.urls import path

from . import views


urlpatterns = [
    path('inspect/', views.inspect, name='soldering_inspect'),
    path('inspect-pcb/', views.inspect_pcb, name='pcb_defect_inspect'),
]

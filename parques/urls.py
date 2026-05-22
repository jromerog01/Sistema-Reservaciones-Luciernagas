from django.contrib import admin
from django.urls import path
from parques import views

urlpatterns = [
    path('', views.listado_parques, name='listado_parques'),
    path('<int:parque_id>/', views.detalle_parque, name='detalle_parque'),
]

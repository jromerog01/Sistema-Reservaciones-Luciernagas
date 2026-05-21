from django.contrib import admin
from django.urls import path
from parques import views

urlpatterns = [
    path('prueba/', views.prueba),
]

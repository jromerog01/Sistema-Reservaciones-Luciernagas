from django.contrib import admin
from django.urls import path
from usuarios import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro_view, name = 'registro'),
    path('login/', views.login_view, name = 'login'),
    path('logout/', views.logout_view, name = 'logout'),
]
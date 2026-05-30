from django.urls import path
from usuarios import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('admins/', views.lista_admins_view, name='lista_admins'),
    path('admins/nuevo/', views.crear_admin_view, name='crear_admin'),
]

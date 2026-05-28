from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

from .forms import RegistroForm, LoginForm, CrearAdminForm, EditarPerfilForm
from .models import Usuario

def es_staff(user):
    return user.is_authenticated and user.is_staff

# ── Registro / Login / Logout ──────────────────────────────────────────────

def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, 'Usuario registrado correctamente')
            return redirect('inicio')
    else:
        form = RegistroForm()
    return render(request, 'registration/registro.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            identificador = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            usuario = authenticate(
                request,
                username=identificador,
                password=password
            )
            if usuario is not None:
                login(request, usuario)
                if usuario.is_staff:
                    return redirect('/admin/')
                return redirect('inicio')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('usuarios:login')


# ── Perfil de cuenta ───────────────────────────────────────────────────────

@login_required(login_url='usuarios:login')
def perfil_view(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('usuarios:perfil')
    else:
        form = EditarPerfilForm(instance=request.user)
    return render(request, 'usuarios/perfil.html', {'form': form})


# ── Crear admin (solo staff) ───────────────────────────────────────────────

@user_passes_test(es_staff, login_url='usuarios:login')
def crear_admin_view(request):
    if request.method == 'POST':
        form = CrearAdminForm(request.POST)
        if form.is_valid():
            nuevo_admin = form.save()
            messages.success(
                request,
                f'Administrador "{nuevo_admin.get_username()}" creado correctamente'
            )
            return redirect('usuarios:lista_admins')
    else:
        form = CrearAdminForm()
    return render(request, 'usuarios/crear_admin.html', {'form': form})


@user_passes_test(es_staff, login_url='usuarios:login')
def lista_admins_view(request):
    admins = Usuario.objects.filter(is_staff=True).order_by('username')
    return render(request, 'usuarios/lista_admins.html', {'admins': admins})

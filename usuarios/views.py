from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

from .forms import RegistroForm, LoginForm, CrearAdminForm, EditarPerfilForm
from .models import Usuario

from django.conf import settings
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

def es_staff(user):
    return user.is_authenticated and user.is_staff

def _next_url(request):
    """Obtiene una URL de regreso segura para login local y social."""
    next_url = request.GET.get('next') or request.POST.get('next')

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return next_url

    return reverse('inicio')


def _google_oauth_context(request):
    return {
        'next': _next_url(request),
        'google_oauth_enabled': getattr(settings, 'GOOGLE_OAUTH_ENABLED', False),
    }

# ── Registro / Login / Logout ──────────────────────────────────────────────

def registro_view(request):
    next_url = _next_url(request)
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Usuario registrado correctamente')
            return redirect(next_url)
    else:
        form = RegistroForm()

    context = _google_oauth_context(request)
    context['form'] = form
    return render(request, 'registration/registro.html', context)


def login_view(request):
    next_url = _next_url(request)
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
                if usuario.is_staff and next_url == reverse('inicio'):
                    return redirect('inicio')
                return redirect(next_url)
    else:
        form = LoginForm()

    context = _google_oauth_context(request)
    context['form'] = form
    return render(request, 'registration/login.html', context)


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
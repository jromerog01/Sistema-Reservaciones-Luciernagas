from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
# Importamos el modelo User de Django (vine por defecto no tienes que hacer algo)
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import RegistroForm, LoginForm

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


def registro_view(request):
    """Registra un cliente y lo deja autenticado para continuar su flujo."""
    next_url = _next_url(request)

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, 'Usuario registrado correctamente')
            return redirect(next_url)
    else:
        form = RegistroForm()
    context = _google_oauth_context(request)
    context['form'] = form
    return render(request, 'registration/registro.html', context)

def login_view(request):
    """Autentica al usuario y respeta el parametro next cuando existe."""
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
                    return redirect('/admin/')
                return redirect(next_url)
    else:
        form = LoginForm()
    context = _google_oauth_context(request)
    context['form'] = form
    return render(request, 'registration/login.html', context)

def logout_view(request):
    """Cierra la sesion actual y regresa al inicio publico."""
    logout(request)
    return redirect('inicio')

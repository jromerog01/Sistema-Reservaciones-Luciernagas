from django.shortcuts import render, redirect
from django.contrib import messages
# Importamos el modelo User de Django (vine por defecto no tienes que hacer algo)
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from .forms import RegistroForm, LoginForm

def registro_view(request):
    """Registra un cliente y lo deja autenticado para continuar su flujo."""

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, 'Usuario registrado correctamente')
            return redirect('inicio')
    else:
        form = RegistroForm()
    return render(request, 'registration/registro.html', {
        'form': form
    })

def login_view(request):
    """Autentica al usuario y respeta el parametro next cuando existe."""
    next_url = request.GET.get('next') or request.POST.get('next') or 'inicio'

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
                if usuario.is_staff and next_url == 'inicio':
                    return redirect('/admin/')
                return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {
        'form': form,
        'next': next_url,
    })

def logout_view(request):
    """Cierra la sesion actual y regresa al inicio publico."""
    logout(request)
    return redirect('inicio')

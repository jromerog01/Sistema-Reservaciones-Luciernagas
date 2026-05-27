from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from .forms import RegistroForm, LoginForm

def registro_view(request):
    """Registra un usuario cliente e inicia sesion automaticamente."""

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
    """Autentica por usuario/correo y redirige segun permisos."""

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
    return render(request, 'registration/login.html', {
        'form': form
    })

def logout_view(request):
    """Cierra la sesion actual y regresa a la pagina de inicio."""

    logout(request)
    return redirect('inicio')

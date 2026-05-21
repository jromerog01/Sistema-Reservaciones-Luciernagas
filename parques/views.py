from django.shortcuts import render

def prueba(request):
    return render(request, "parques/prototipo_reservaciones.html")

# Create your views here.

from django.urls import path
from reservaciones import views

urlpatterns = [
    path("nueva/<int:hospedaje_id>/", views.crear_reservacion, name="crear_reservacion"),
    path("<int:reservacion_id>/cancelar/", views.cancelar_reservacion, name="cancelar_reservacion"),
    path("mis-reservaciones/", views.mis_reservaciones, name="mis_reservaciones"),
    path("todas/",views.todas_las_reservaciones, name="todas_las_reservaciones"),
    path("<int:reservacion_id>/", views.detalle_reservacion, name="detalle_reservacion"),
    #path("seleccionar-hospedaje/", views.seleccionar_hospedaje, name="seleccionar_hospedaje"),
]

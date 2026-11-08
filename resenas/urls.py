from django.urls import path

from . import views

app_name = 'resenas'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('registro/', views.registro, name='registro'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('usuarios/<str:username>/', views.perfil, name='perfil'),
    path('usuarios/<str:username>/resenas/', views.resenas_usuario, name='resenas_usuario'),
    path('usuarios/<str:username>/comentarios/', views.comentarios_usuario, name='comentarios_usuario'),
    path('juegos/', views.lista_juegos, name='lista_juegos'),
    path('juegos/<int:pk>/', views.detalle_juego, name='detalle_juego'),
    path('juegos/<int:juego_pk>/calificar/', views.calificar_juego, name='calificar_juego'),
    path('juegos/<int:juego_pk>/resena/nueva/', views.crear_resena, name='crear_resena'),
    path('resenas/', views.lista_resenas, name='lista_resenas'),
    path('resenas/<int:pk>/', views.detalle_resena, name='detalle_resena'),
    path('resenas/<int:pk>/editar/', views.editar_resena, name='editar_resena'),
    path('resenas/<int:pk>/eliminar/', views.eliminar_resena, name='eliminar_resena'),
]

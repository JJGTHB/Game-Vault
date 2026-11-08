from django import forms
from django.contrib import admin
from django.db import models
from django.utils.html import format_html

from .models import Calificacion, Comentario, Genero, Juego, Plataforma, Resena

admin.site.site_header = 'GameVault · Administración'
admin.site.site_title = 'GameVault'
admin.site.index_title = 'Panel del administrador'


@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    search_fields = ['nombre']


@admin.register(Plataforma)
class PlataformaAdmin(admin.ModelAdmin):
    search_fields = ['nombre']


@admin.action(description='Prohibir los juegos seleccionados (ocultar del sistema de reseñas)')
def prohibir_juegos(modeladmin, request, queryset):
    queryset.update(prohibido=True)


@admin.action(description='Permitir de nuevo los juegos seleccionados')
def permitir_juegos(modeladmin, request, queryset):
    queryset.update(prohibido=False)


@admin.register(Juego)
class JuegoAdmin(admin.ModelAdmin):
    """CRUD 1: catálogo oficial. Aquí el admin también asigna la clasificación
    por edad y puede prohibir juegos (capacidades exclusivas)."""

    list_display = ['miniatura', 'titulo', 'lista_plataformas', 'anio_lanzamiento', 'clasificacion_edad', 'prohibido', 'total_resenas']
    list_display_links = ['miniatura', 'titulo']
    list_editable = ['clasificacion_edad', 'prohibido']
    list_filter = ['plataformas', 'clasificacion_edad', 'prohibido']
    search_fields = ['titulo']
    filter_horizontal = ['generos']
    actions = [prohibir_juegos, permitir_juegos]
    # El selector de archivos de la portada solo muestra imágenes.
    formfield_overrides = {models.FileField: {'widget': forms.ClearableFileInput(attrs={'accept': 'image/*'})}}

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Casillas para marcar varias plataformas a la vez.
        if db_field.name == 'plataformas':
            kwargs['widget'] = forms.CheckboxSelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description='Plataformas')
    def lista_plataformas(self, obj):
        return ', '.join(p.nombre for p in obj.plataformas.all()) or '—'

    @admin.display(description='Portada')
    def miniatura(self, obj):
        if obj.portada:
            return format_html('<img src="{}" style="height:48px;border-radius:4px;">', obj.portada.url)
        return '—'


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    """Reseñas expertas: las publicadas por el admin se destacan en el sitio."""

    list_display = ['titulo', 'juego', 'autor', 'puntuacion', 'fecha_creacion']
    list_filter = ['juego']
    search_fields = ['titulo', 'contenido', 'autor__username']
    exclude = ['autor']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'titulo':      # el título es de una sola línea
            kwargs['widget'] = forms.TextInput(attrs={'style': 'width: 40em'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.autor = request.user
        super().save_model(request, obj, form, change)


@admin.action(description='Censurar los comentarios seleccionados')
def censurar_comentarios(modeladmin, request, queryset):
    queryset.update(censurado=True)


@admin.action(description='Quitar la censura a los comentarios seleccionados')
def descensurar_comentarios(modeladmin, request, queryset):
    queryset.update(censurado=False)


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ['autor', 'resena', 'censurado', 'fecha_creacion']
    list_editable = ['censurado']
    list_filter = ['censurado']
    search_fields = ['contenido', 'autor__username']
    actions = [censurar_comentarios, descensurar_comentarios]


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ['juego', 'usuario', 'estrellas', 'fecha_actualizacion']
    list_filter = ['estrellas']

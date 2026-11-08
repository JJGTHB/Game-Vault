import unicodedata

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Calificacion, Comentario, Genero, Juego, Perfil, Resena

MAX_TAGS = 10          # tags de género que se pueden añadir en un solo envío
MAX_LARGO_TAG = 40     # largo máximo de un tag (el nombre de Genero admite 40)


def opciones_estrellas():
    """'1-★', '2-★★', ... con una opción vacía para obligar a elegir."""
    return [('', 'Elige una calificación')] + [(i, f'{i}-' + '★' * i) for i in range(1, 6)]


def _clave(texto):
    """Clave para comparar tags sin importar mayúsculas ni tildes ('Acción' == 'accion')."""
    sin_tildes = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return sin_tildes.casefold()


class RegistroForm(UserCreationForm):
    """Registro de usuarios normales (los administradores usan /admin)."""

    email = forms.EmailField(required=False, label='Correo (opcional)')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ResenaForm(forms.ModelForm):
    """ModelForm para crear y editar reseñas (sin límite de caracteres en título ni contenido)."""

    generos = forms.CharField(
        required=False,
        label='Tags de género para este juego',
        help_text='Opcional: géneros separados por comas (ej: acción, terror). Se añaden al juego.',
    )

    class Meta:
        model = Resena
        fields = ['titulo', 'contenido', 'puntuacion']
        widgets = {
            'titulo': forms.TextInput(),
            'contenido': forms.Textarea(attrs={'rows': 8}),
            'puntuacion': forms.Select(choices=opciones_estrellas()),
        }
        labels = {'puntuacion': 'Calificación (1 a 5 estrellas)'}

    def clean_generos(self):
        """Devuelve una lista de tags limpios, sin repetidos y validados."""
        nombres, vistos = [], set()
        for bruto in self.cleaned_data.get('generos', '').split(','):
            nombre = ' '.join(bruto.split())
            if not nombre or _clave(nombre) in vistos:
                continue
            if len(nombre) > MAX_LARGO_TAG:
                raise forms.ValidationError(f'Cada tag puede tener hasta {MAX_LARGO_TAG} caracteres.')
            vistos.add(_clave(nombre))
            nombres.append(nombre)
        if len(nombres) > MAX_TAGS:
            raise forms.ValidationError(f'Puedes añadir hasta {MAX_TAGS} tags a la vez.')
        return nombres

    def guardar_generos(self, juego):
        """Añade los tags al juego reutilizando los existentes (sin duplicar por mayúsculas/tildes)."""
        existentes = {}
        for genero in Genero.objects.all():
            existentes.setdefault(_clave(genero.nombre), genero)
        for nombre in self.cleaned_data.get('generos', []):
            genero = existentes.get(_clave(nombre))
            if genero is None:
                genero = Genero.objects.create(nombre=nombre)
                existentes[_clave(nombre)] = genero
            juego.generos.add(genero)


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escribe un comentario...'}),
        }
        labels = {'contenido': ''}


class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ['estrellas']
        widgets = {'estrellas': forms.Select(choices=opciones_estrellas())}
        labels = {'estrellas': 'Tu calificación'}


class PerfilForm(forms.ModelForm):
    """Descripción libre (sin límite de caracteres) y lista de juegos favoritos."""

    class Meta:
        model = Perfil
        fields = ['descripcion', 'juegos_favoritos']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 6}),
            'juegos_favoritos': forms.CheckboxSelectMultiple,
        }
        labels = {
            'descripcion': 'Cuéntanos sobre ti',
            'juegos_favoritos': 'Tus juegos favoritos',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['juegos_favoritos'].queryset = Juego.objects.filter(prohibido=False)

    def save(self, commit=True):
        # Los juegos prohibidos no aparecen en el formulario; se conservan para
        # que no se pierdan si el administrador los vuelve a permitir.
        baneados = list(self.instance.juegos_favoritos.filter(prohibido=True)) if self.instance.pk else []
        perfil = super().save(commit=commit)
        if commit and baneados:
            perfil.juegos_favoritos.add(*baneados)
        return perfil

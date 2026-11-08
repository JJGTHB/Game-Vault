from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Genero(models.Model):
    """Etiqueta de género (acción, RPG, plataformas, etc.)."""
    nombre = models.CharField(max_length=40, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'género'
        verbose_name_plural = 'géneros'

    def __str__(self):
        return self.nombre


class Plataforma(models.Model):
    """Plataforma en la que está disponible un juego (PC, PlayStation, Nintendo, Xbox...)."""
    nombre = models.CharField(max_length=40, unique=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Juego(models.Model):
    """Videojuego del catálogo oficial (solo el administrador lo gestiona en /admin)."""

    class ClasificacionEdad(models.TextChoices):
        SIN_CLASIFICAR = 'SC', 'Sin clasificar'
        E = 'E', 'E - Para todo público'
        E10 = 'E10+', 'E10+ - Mayores de 10 años'
        T = 'T', 'T - Adolescentes'
        M = 'M', 'M - Maduro (17+)'
        AO = 'AO', 'AO - Solo adultos (18+)'

    titulo = models.CharField('título', max_length=150, unique=True)
    descripcion = models.TextField('descripción')
    anio_lanzamiento = models.PositiveSmallIntegerField(
        'año de lanzamiento',
        validators=[MinValueValidator(1950), MaxValueValidator(2100)],
    )
    plataformas = models.ManyToManyField(Plataforma, related_name='juegos')
    portada = models.FileField(
        'portada', upload_to='portadas/', max_length=255, blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp', 'gif'])],
        help_text='Imagen JPG, PNG, WEBP o GIF (recomendado vertical 3:4, por ejemplo 600x800 px).',
    )
    generos = models.ManyToManyField(Genero, blank=True, related_name='juegos')
    clasificacion_edad = models.CharField(
        'clasificación por edad',
        max_length=5,
        choices=ClasificacionEdad.choices,
        default=ClasificacionEdad.SIN_CLASIFICAR,
    )
    prohibido = models.BooleanField(
        default=False,
        help_text='Si está marcado, el juego se oculta del sistema de reseñas.',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['titulo']

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('resenas:detalle_juego', args=[self.pk])

    @property
    def puntuacion_promedio(self):
        promedio = self.calificaciones.aggregate(models.Avg('estrellas'))['estrellas__avg']
        return round(promedio, 1) if promedio is not None else None

    @property
    def total_calificaciones(self):
        return self.calificaciones.count()

    @property
    def total_resenas(self):
        return self.resenas.count()


class Resena(models.Model):
    """Reseña de un juego. Las del administrador se muestran como reseñas expertas."""

    juego = models.ForeignKey(Juego, on_delete=models.CASCADE, related_name='resenas')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resenas')
    titulo = models.TextField('título')  # sin límite de caracteres
    contenido = models.TextField()
    puntuacion = models.PositiveSmallIntegerField(
        'puntuación',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Calificación de 1 a 5 estrellas.',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.titulo} ({self.juego})'

    def get_absolute_url(self):
        return reverse('resenas:detalle_resena', args=[self.pk])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Las estrellas de la reseña son también la calificación del autor al juego.
        Calificacion.objects.update_or_create(
            juego=self.juego, usuario=self.autor, defaults={'estrellas': self.puntuacion}
        )


class Calificacion(models.Model):
    """Estrellas (1 a 5) que un usuario da a un juego; una por usuario y juego.
    El promedio del juego se calcula con estas calificaciones."""

    juego = models.ForeignKey(Juego, on_delete=models.CASCADE, related_name='calificaciones')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calificaciones')
    estrellas = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['juego', 'usuario'], name='una_calificacion_por_usuario_y_juego'),
        ]
        verbose_name = 'calificación'
        verbose_name_plural = 'calificaciones'

    def __str__(self):
        return f'{self.usuario} → {self.juego}: {self.estrellas}★'


class Comentario(models.Model):
    """Comentario de un usuario en la reseña de otro usuario."""

    resena = models.ForeignKey(Resena, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comentarios')
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    censurado = models.BooleanField(default=False)

    class Meta:
        ordering = ['fecha_creacion']

    def __str__(self):
        return f'Comentario de {self.autor} en «{self.resena.titulo}»'


class Perfil(models.Model):
    """Perfil personalizable de cada usuario: descripción y juegos favoritos."""

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    descripcion = models.TextField('descripción', blank=True)  # sin límite de caracteres
    juegos_favoritos = models.ManyToManyField(Juego, blank=True, related_name='favorito_de')

    def __str__(self):
        return f'Perfil de {self.usuario}'

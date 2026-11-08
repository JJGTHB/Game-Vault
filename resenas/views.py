from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, ExpressionWrapper, F, FloatField
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CalificacionForm, ComentarioForm, PerfilForm, RegistroForm, ResenaForm
from .models import Calificacion, Genero, Juego, Perfil, Resena


def juegos_mas_activos(limite=10):
    """Top de juegos por actividad = promedio entre nº de reseñas,
    nº de calificaciones por estrellas y nº de comentarios."""
    return (
        Juego.objects.filter(prohibido=False)
        .annotate(
            n_resenas=Count('resenas', distinct=True),
            n_calificaciones=Count('calificaciones', distinct=True),
            n_comentarios=Count('resenas__comentarios', distinct=True),
        )
        .annotate(actividad=ExpressionWrapper(
            (F('n_resenas') + F('n_calificaciones') + F('n_comentarios')) / 3.0,
            output_field=FloatField(),
        ))
        .order_by('-actividad', 'titulo')[:limite]
    )


def inicio(request):
    """Portada pública. Las últimas reseñas solo se muestran a usuarios registrados."""
    ultimas, top = [], []
    if request.user.is_authenticated:
        top = juegos_mas_activos()
        ultimas = (
            Resena.objects.filter(juego__prohibido=False)
            .select_related('juego', 'autor')[:5]
        )
    return render(request, 'resenas/inicio.html', {'top_juegos': top, 'ultimas_resenas': ultimas})


def registro(request):
    """Registro de usuarios normales. Los administradores entran por /admin."""
    if request.user.is_authenticated:
        return redirect('resenas:inicio')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, f'¡Bienvenido a GameVault, {usuario.username}!')
            return redirect('resenas:inicio')
    else:
        form = RegistroForm()
    return render(request, 'registration/registro.html', {'form': form})


@login_required
def lista_juegos(request):
    juegos = Juego.objects.filter(prohibido=False).prefetch_related('generos', 'plataformas')
    return render(request, 'resenas/lista_juegos.html', {'juegos': juegos})


@login_required
def detalle_juego(request, pk):
    """Ficha técnica del juego, reseñas expertas (admin) y reseñas de la comunidad."""
    juego = get_object_or_404(Juego, pk=pk, prohibido=False)
    resenas = juego.resenas.select_related('autor')
    mia = Calificacion.objects.filter(juego=juego, usuario=request.user).first()
    form_calificacion = CalificacionForm(initial={'estrellas': mia.estrellas} if mia else None)
    return render(request, 'resenas/detalle_juego.html', {
        'juego': juego,
        'form_calificacion': form_calificacion,
        'resenas_expertas': resenas.filter(autor__is_staff=True),
        'resenas_comunidad': resenas.filter(autor__is_staff=False),
    })


@login_required
@require_POST
def calificar_juego(request, juego_pk):
    """Un usuario califica un juego con 1 a 5 estrellas (puede cambiarla después)."""
    juego = get_object_or_404(Juego, pk=juego_pk, prohibido=False)
    form = CalificacionForm(request.POST)
    if form.is_valid():
        Calificacion.objects.update_or_create(
            juego=juego, usuario=request.user,
            defaults={'estrellas': form.cleaned_data['estrellas']},
        )
        messages.success(request, 'Tu calificación se guardó.')
    else:
        messages.error(request, 'La calificación debe ser de 1 a 5 estrellas.')
    return redirect('resenas:detalle_juego', pk=juego.pk)


@login_required
def lista_resenas(request):
    resenas = Resena.objects.filter(juego__prohibido=False).select_related('juego', 'autor')
    genero_id = request.GET.get('genero', '')
    if not genero_id.isdigit():      # ignora valores inválidos (p. ej. ?genero=abc)
        genero_id = ''
    if genero_id:
        resenas = resenas.filter(juego__generos__id=int(genero_id))
    return render(request, 'resenas/lista_resenas.html', {
        'resenas': resenas,
        'generos': Genero.objects.all(),
        'genero_seleccionado': genero_id,
    })


@login_required
def detalle_resena(request, pk):
    resena = get_object_or_404(
        Resena.objects.select_related('juego', 'autor'), pk=pk, juego__prohibido=False
    )
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.resena = resena
            comentario.autor = request.user
            comentario.save()
            messages.success(request, 'Tu comentario se publicó correctamente.')
            return redirect('resenas:detalle_resena', pk=resena.pk)
    else:
        form = ComentarioForm()
    return render(request, 'resenas/detalle_resena.html', {
        'resena': resena,
        'comentarios': resena.comentarios.select_related('autor'),
        'form': form,
    })


@login_required
def crear_resena(request, juego_pk):
    juego = get_object_or_404(Juego, pk=juego_pk, prohibido=False)
    if request.method == 'POST':
        form = ResenaForm(request.POST)
        if form.is_valid():
            resena = form.save(commit=False)
            resena.juego = juego
            resena.autor = request.user
            resena.save()
            form.guardar_generos(juego)
            messages.success(request, 'Tu reseña se publicó correctamente.')
            return redirect('resenas:detalle_resena', pk=resena.pk)
    else:
        # Si el usuario ya calificó este juego, el selector parte de esa calificación
        # (así no la pisa sin querer); si no, debe elegir una explícitamente.
        previa = Calificacion.objects.filter(juego=juego, usuario=request.user).first()
        form = ResenaForm(initial={'puntuacion': previa.estrellas} if previa else None)
    return render(request, 'resenas/form_resena.html', {'form': form, 'juego': juego, 'editando': False})


@login_required
def editar_resena(request, pk):
    """Solo el creador de la reseña puede editarla."""
    resena = get_object_or_404(Resena, pk=pk, juego__prohibido=False)
    if resena.autor != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        form = ResenaForm(request.POST, instance=resena)
        if form.is_valid():
            form.save()
            form.guardar_generos(resena.juego)
            messages.success(request, 'Tu reseña se actualizó correctamente.')
            return redirect('resenas:detalle_resena', pk=resena.pk)
    else:
        form = ResenaForm(instance=resena)
    return render(request, 'resenas/form_resena.html', {'form': form, 'juego': resena.juego, 'editando': True})


@login_required
def eliminar_resena(request, pk):
    """Solo el creador de la reseña puede eliminarla (con confirmación por POST)."""
    resena = get_object_or_404(Resena, pk=pk)
    if resena.autor != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        juego_pk = resena.juego.pk
        resena.delete()
        messages.success(request, 'Tu reseña fue eliminada.')
        return redirect('resenas:detalle_juego', pk=juego_pk)
    return render(request, 'resenas/confirmar_eliminar.html', {'resena': resena})


# ---------------------------------------------------------------- Perfiles

def _perfil_de(usuario):
    """Devuelve el perfil del usuario, creándolo vacío la primera vez."""
    perfil, _ = Perfil.objects.get_or_create(usuario=usuario)
    return perfil


@login_required
def perfil(request, username):
    """Perfil público: descripción, juegos favoritos y enlaces a sus reseñas y comentarios."""
    usuario = get_object_or_404(User, username=username)
    perfil = _perfil_de(usuario)
    return render(request, 'resenas/perfil.html', {
        'usuario': usuario,
        'perfil': perfil,
        'favoritos': perfil.juegos_favoritos.filter(prohibido=False).prefetch_related('plataformas'),
        'total_resenas': usuario.resenas.filter(juego__prohibido=False).count(),
        'total_comentarios': usuario.comentarios.filter(resena__juego__prohibido=False).count(),
    })


@login_required
def editar_perfil(request):
    """Cada usuario edita únicamente su propio perfil."""
    perfil = _perfil_de(request.user)
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil se actualizó correctamente.')
            return redirect('resenas:perfil', username=request.user.username)
    else:
        form = PerfilForm(instance=perfil)
    return render(request, 'resenas/form_perfil.html', {'form': form})


@login_required
def resenas_usuario(request, username):
    usuario = get_object_or_404(User, username=username)
    resenas = usuario.resenas.filter(juego__prohibido=False).select_related('juego')
    return render(request, 'resenas/resenas_usuario.html', {'usuario': usuario, 'resenas': resenas})


@login_required
def comentarios_usuario(request, username):
    usuario = get_object_or_404(User, username=username)
    comentarios = (
        usuario.comentarios.filter(resena__juego__prohibido=False)
        .select_related('resena', 'resena__juego')
        .order_by('-fecha_creacion')
    )
    return render(request, 'resenas/comentarios_usuario.html', {'usuario': usuario, 'comentarios': comentarios})

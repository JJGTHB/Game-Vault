# GameVault — Portal de reseñas de videojuegos

Proyecto final de Laboratorio de Software III (Django + SQLite).

## Roles
- **Administrador** (`/admin/`): CRUD del catálogo de juegos (título, descripción,
  plataformas —puede marcar varias—, año de lanzamiento, portada, géneros), reseñas
  expertas, clasificación por edad, prohibir juegos y censurar comentarios.
- **Usuario registrado**: explora el catálogo, califica juegos con 1 a 5 estrellas
  (el juego muestra el promedio con decimales), crea/edita/elimina sus propias
  reseñas, asigna tags de género, comenta reseñas ajenas y personaliza su perfil
  (descripción y juegos favoritos, con enlaces a sus reseñas y comentarios).
  Perfiles, reseñas y comentarios no tienen límite de caracteres.
- **Inicio**: top 10 de juegos con más actividad (promedio de reseñas, calificaciones
  y comentarios) y, debajo, las reseñas más recientes.

## Ejecutar (Windows)
Requisitos: Python 3.12 o superior. La única dependencia es Django.

```bash
git clone <URL-del-repositorio>
cd <nombre-del-repositorio>
python -m venv venv
venv\Scripts\activate
python -m pip install django
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
En Linux/Mac, el cuarto comando es `source venv/bin/activate`.

- Sitio: http://127.0.0.1:8000/
- Administración: http://127.0.0.1:8000/admin/

`migrate` crea la base de datos SQLite (con las plataformas PC, PlayStation,
Nintendo y Xbox). El administrador registra los juegos desde `/admin/`.

### Si el proyecto no arranca
- Borra las carpetas `venv` y `.venv` de intentos anteriores y vuelve a crear **una sola**.
- No renombres ni muevas la carpeta del proyecto después de crear el entorno virtual
  (el entorno guarda rutas absolutas): si lo haces, bórralo y créalo otra vez.
- No ejecutes `python -m venv` con otro entorno activo; corre antes `deactivate`.
- Instala con `python -m pip install django` (no con el comando `pip` a secas).
- Ejecuta los comandos dentro de la carpeta donde está `manage.py`.

## Portadas de los juegos
En `/admin/` → **Juegos** → abrir un juego → campo **Portada** → *Elegir archivo* →
**Guardar**. Las imágenes (JPG, PNG, WEBP o GIF) se guardan en `media/portadas/`.
Recomendado: imagen vertical 3:4 (por ejemplo 600×800 px).

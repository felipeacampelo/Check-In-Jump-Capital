import os
from django import template
from django.conf import settings

register = template.Library()

def _is_cloud_storage():
    """Verifica se está usando storage na nuvem (Cloudinary)."""
    return getattr(settings, 'DEFAULT_FILE_STORAGE', '').startswith('cloudinary')

def _file_available(file_field):
    """Verifica se o arquivo está disponível (local ou cloud)."""
    if not file_field or not file_field.name:
        return False
    if _is_cloud_storage():
        return True
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
        return os.path.exists(file_path)
    except (ValueError, AttributeError):
        return False

@register.filter
def file_exists(file_field):
    """
    Verifica se o arquivo referenciado pelo campo existe.
    Funciona com storage local e Cloudinary.
    """
    return _file_available(file_field)

@register.filter
def safe_image_url(file_field):
    """
    Retorna a URL da imagem se o arquivo existe, caso contrário retorna None.
    Funciona com storage local e Cloudinary.
    """
    if not _file_available(file_field):
        return None
    try:
        return file_field.url
    except (ValueError, AttributeError):
        return None

@register.simple_tag
def image_or_placeholder(file_field, placeholder_class="avatar-initials", initials=""):
    """
    Retorna HTML para imagem se existe, ou placeholder com iniciais se não existe.
    Funciona com storage local e Cloudinary.
    """
    if _file_available(file_field):
        try:
            return f'<img src="{file_field.url}" class="avatar avatar-sm" alt="Foto">'
        except (ValueError, AttributeError):
            pass
    return f'<span class="avatar avatar-sm {placeholder_class}">{initials}</span>'

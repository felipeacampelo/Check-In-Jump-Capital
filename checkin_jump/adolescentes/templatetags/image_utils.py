import os
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def file_exists(file_field):
    """
    Verifica se o arquivo referenciado pelo campo existe fisicamente no sistema.
    Retorna True se existe, False caso contrário.
    """
    if not file_field:
        return False
    
    try:
        # Caminho completo do arquivo
        file_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
        return os.path.exists(file_path)
    except (ValueError, AttributeError):
        return False

@register.filter
def safe_image_url(file_field):
    """
    Retorna a URL da imagem se o arquivo existe, caso contrário retorna None.
    Evita erros 404 para imagens faltantes.
    """
    if not file_field:
        return None
    
    try:
        # Verifica se o arquivo existe fisicamente
        file_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
        if os.path.exists(file_path):
            return file_field.url
        else:
            return None
    except (ValueError, AttributeError):
        return None

@register.simple_tag
def image_or_placeholder(file_field, placeholder_class="avatar-initials", initials=""):
    """
    Retorna HTML para imagem se existe, ou placeholder com iniciais se não existe.
    """
    if not file_field:
        return f'<span class="avatar avatar-sm {placeholder_class}">{initials}</span>'
    
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
        if os.path.exists(file_path):
            return f'<img src="{file_field.url}" class="avatar avatar-sm" alt="Foto">'
        else:
            return f'<span class="avatar avatar-sm {placeholder_class}">{initials}</span>'
    except (ValueError, AttributeError):
        return f'<span class="avatar avatar-sm {placeholder_class}">{initials}</span>'

from django import template
from urllib.parse import urlencode, urlparse, parse_qs

register = template.Library()

@register.simple_tag(takes_context=True)
def url_with_ano(context, url_name, *args, **kwargs):
    """
    Gera URL preservando o parâmetro 'ano' da request atual.
    Uso: {% url_with_ano 'nome_da_url' %}
    """
    from django.urls import reverse
    request = context.get('request')
    
    # Gera a URL base
    url = reverse(url_name, args=args, kwargs=kwargs)
    
    # Adiciona parâmetro ano se existir na request
    if request and request.GET.get('ano'):
        params = {'ano': request.GET.get('ano')}
        url = f"{url}?{urlencode(params)}"
    
    return url

@register.simple_tag(takes_context=True)
def add_ano_param(context, url):
    """
    Adiciona o parâmetro 'ano' a uma URL existente.
    Uso: {% add_ano_param '/alguma/url/' %}
    """
    request = context.get('request')
    
    if not request or not request.GET.get('ano'):
        return url
    
    ano = request.GET.get('ano')
    separator = '&' if '?' in url else '?'
    return f"{url}{separator}ano={ano}"

@register.simple_tag(takes_context=True)
def current_ano(context):
    """
    Retorna o ano atual da request.
    Uso: {% current_ano %}
    """
    request = context.get('request')
    if request and request.GET.get('ano'):
        return request.GET.get('ano')
    return context.get('ano_selecionado', 2026)

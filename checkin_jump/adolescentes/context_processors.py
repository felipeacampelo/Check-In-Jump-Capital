def theme_context(request):
    """
    Context processor para detectar o tema preferido do usuário.
    Verifica cookies para determinar se deve aplicar modo escuro no servidor.
    """
    # Verifica se há um cookie indicando modo escuro
    dark_mode_enabled = request.COOKIES.get('dark-mode') == 'enabled'
    
    return {
        'dark_mode_enabled': dark_mode_enabled,
        'html_class': 'dark-mode' if dark_mode_enabled else '',
        'body_class': 'dark-mode' if dark_mode_enabled else '',
    }

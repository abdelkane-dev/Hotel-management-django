from .models import ClientSettings


def user_settings(request):
    """Ajoute les paramètres du client connecté au contexte des templates.
    Utilisation: dans les templates -> {{ user_settings }}
    """
    settings_obj = None
    try:
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile:
                settings_obj = getattr(profile, 'settings', None)
    except Exception:
        settings_obj = None

    return {'user_settings': settings_obj}

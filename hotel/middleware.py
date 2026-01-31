from django.utils import timezone
from django.utils import translation


class UserSettingsMiddleware:
    """Middleware pour activer le fuseau horaire et la langue choisis par l'utilisateur authentifié.
    Doit être ajouté après AuthenticationMiddleware et SessionMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.user.is_authenticated:
                profile = getattr(request.user, 'profile', None)
                settings_obj = getattr(profile, 'settings', None) if profile else None
                if settings_obj:
                    # Timezone
                    try:
                        timezone.activate(settings_obj.timezone)
                    except Exception:
                        pass
                    # Langue
                    try:
                        translation.activate(settings_obj.language)
                        request.LANGUAGE_CODE = settings_obj.language
                    except Exception:
                        pass
        except Exception:
            pass

        response = self.get_response(request)
        return response

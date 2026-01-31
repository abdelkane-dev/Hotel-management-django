from django.apps import AppConfig


class HotelConfig(AppConfig):
    name = 'hotel'
    
    def ready(self):
        """Importer les signaux pour l'automatisation comptable"""
        import hotel.signals

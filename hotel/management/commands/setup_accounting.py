# -*- coding: utf-8 -*-
"""
Management command pour configurer le système comptable
Crée les migrations initiales et configure les signaux
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Configure le système comptable et crée les migrations nécessaires'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Configuration du système comptable...')
        
        # Vérifier si les modèles comptables existent
        try:
            from hotel.models import Facture, FichePaie, ChargeComptable, Maintenance
            self.stdout.write('✅ Modèles comptables importés avec succès')
        except ImportError as e:
            self.stdout.write(f'❌ Erreur d\'importation des modèles: {e}')
            return
        
        # Créer les migrations si nécessaire
        self.stdout.write('📝 Vérification des migrations...')
        
        # Vérifier si la table des factures existe
        table_names = connection.introspection.table_names()
        
        if 'hotel_facture' not in table_names:
            self.stdout.write('⚠️  Les tables comptables n\'existent pas encore.')
            self.stdout.write('🔄 Veuillez exécuter: python manage.py makemigrations hotel')
            self.stdout.write('🔄 Puis: python manage.py migrate')
        else:
            self.stdout.write('✅ Tables comptables déjà existantes')
        
        # Configuration des signaux
        self.stdout.write('📡 Configuration des signaux...')
        
        try:
            from hotel import signals
            self.stdout.write('✅ Signaux importés avec succès')
        except ImportError as e:
            self.stdout.write(f'❌ Erreur d\'importation des signaux: {e}')
        
        # Instructions finales
        self.stdout.write('\n🎯 Configuration terminée!')
        self.stdout.write('\n📋 Étapes suivantes:')
        self.stdout.write('1. Exécutez: python manage.py makemigrations hotel')
        self.stdout.write('2. Exécutez: python manage.py migrate')
        self.stdout.write('3. Redémarrez le serveur Django')
        self.stdout.write('4. Accédez à /billing/ pour voir le nouveau tableau de bord comptable')
        
        self.stdout.write('\n🔗 Fonctionnalités disponibles:')
        self.stdout.write('• Facturation automatique des réservations')
        self.stdout.write('• Gestion des fiches de paie')
        self.stdout.write('• Suivi des charges comptables')
        self.stdout.write('• Tableau de bord avec graphiques')
        self.stdout.write('• Export CSV et PDF')
        self.stdout.write('• API pour les statistiques')

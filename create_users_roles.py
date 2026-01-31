#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour créer les utilisateurs de test avec différents rôles
IMPORTANT : Exécuter ce script APRÈS create_sample_data.py

Usage : python create_users_roles.py
"""

import os
import django
from datetime import datetime

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_management.settings')
django.setup()

from django.contrib.auth.models import User
from hotel.models import Client, UserProfile

def create_users_with_roles():
    """
    Crée 3 utilisateurs de test pour les 3 rôles
    """
    print("🚀 Création des utilisateurs de test avec rôles...\n")
    
    # ==========================================
    # 1. ADMINISTRATEUR
    # ==========================================
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@hotel.com',
            password='admin123',
            first_name='Admin',
            last_name='Système'
        )
        print("✅ ADMINISTRATEUR créé :")
        print(f"   👤 Username : admin")
        print(f"   🔑 Password : admin123")
        print(f"   📧 Email : admin@hotel.com")
        print(f"   🎭 Rôle : Administrateur (is_superuser=True)\n")
    else:
        print("ℹ️  ADMINISTRATEUR déjà existant (admin / admin123)\n")
    
    # ==========================================
    # 2. EMPLOYÉ
    # ==========================================
    if not User.objects.filter(username='employe').exists():
        employe_user = User.objects.create_user(
            username='employe',
            email='employe@hotel.com',
            password='employe123',
            first_name='Marie',
            last_name='Réceptionniste'
        )
        # Définir is_staff=True pour en faire un employé
        employe_user.is_staff = True
        employe_user.save()
        
        # Créer le profil
        UserProfile.objects.create(user=employe_user)
        
        print("✅ EMPLOYÉ créé :")
        print(f"   👤 Username : employe")
        print(f"   🔑 Password : employe123")
        print(f"   📧 Email : employe@hotel.com")
        print(f"   🎭 Rôle : Employé (is_staff=True, is_superuser=False)\n")
    else:
        print("ℹ️  EMPLOYÉ déjà existant (employe / employe123)\n")
    
    # ==========================================
    # 3. CLIENT
    # ==========================================
    if not User.objects.filter(username='client').exists():
        # Créer l'utilisateur client
        client_user = User.objects.create_user(
            username='client',
            email='client@hotel.com',
            password='client123',
            first_name='Jean',
            last_name='Dupont'
        )
        # Le client ne doit pas être staff ni superuser
        client_user.is_staff = False
        client_user.is_superuser = False
        client_user.save()
        
        # Chercher ou créer le profil Client correspondant
        try:
            client_profile = Client.objects.get(email='jean.dupont@email.com')
        except Client.DoesNotExist:
            # Créer un nouveau client si n'existe pas
            client_profile = Client.objects.create(
                nom='Dupont',
                prenom='Jean',
                email='client@hotel.com',
                telephone='0601020304',
                numero_piece_identite='CLIENT123456',
                adresse='12 Rue de la Paix',
                ville='Paris',
                pays='France'
            )
        
        # Créer le UserProfile qui lie User et Client
        UserProfile.objects.create(
            user=client_user,
            client=client_profile
        )
        
        print("✅ CLIENT créé :")
        print(f"   👤 Username : client")
        print(f"   🔑 Password : client123")
        print(f"   📧 Email : client@hotel.com")
        print(f"   🎭 Rôle : Client (is_staff=False, is_superuser=False)")
        print(f"   🔗 Lié au profil client : {client_profile.nom_complet}\n")
    else:
        print("ℹ️  CLIENT déjà existant (client / client123)\n")
    
    # ==========================================
    # RÉSUMÉ
    # ==========================================
    print("\n" + "="*70)
    print("🎉 CRÉATION TERMINÉE ! Voici les identifiants de test :")
    print("="*70)
    print("\n📋 TABLEAU RÉCAPITULATIF :")
    print("-" * 70)
    print(f"{'RÔLE':<20} {'USERNAME':<15} {'PASSWORD':<15} {'ACCÈS':<20}")
    print("-" * 70)
    print(f"{'👑 Administrateur':<20} {'admin':<15} {'admin123':<15} {'Accès complet':<20}")
    print(f"{'🧑‍💼 Employé':<20} {'employe':<15} {'employe123':<15} {'Gestion courante':<20}")
    print(f"{'👤 Client':<20} {'client':<15} {'client123':<15} {'Espace personnel':<20}")
    print("-" * 70)
    
    print("\n📍 URLS DES DASHBOARDS :")
    print("-" * 70)
    print("🏠 Page de connexion : http://127.0.0.1:8000/")
    print("👑 Dashboard Admin   : http://127.0.0.1:8000/dashboard/admin/")
    print("🧑‍💼 Dashboard Employé : http://127.0.0.1:8000/dashboard/employe/")
    print("👤 Dashboard Client  : http://127.0.0.1:8000/dashboard/client/")
    print("-" * 70)
    
    print("\n🎯 FONCTIONNALITÉS PAR RÔLE :")
    print("-" * 70)
    print("👑 ADMINISTRATEUR :")
    print("   ✅ Accès complet à toutes les fonctionnalités")
    print("   ✅ Créer, modifier, SUPPRIMER clients/chambres/réservations")
    print("   ✅ Accès aux statistiques complètes")
    print("   ✅ Accès à l'interface Django Admin")
    print()
    print("🧑‍💼 EMPLOYÉ :")
    print("   ✅ Consulter les clients")
    print("   ✅ Créer et modifier des clients")
    print("   ✅ Créer et modifier des réservations")
    print("   ✅ Consulter les chambres")
    print("   ❌ PAS de suppression (clients, chambres, réservations)")
    print()
    print("👤 CLIENT :")
    print("   ✅ Voir ses propres réservations")
    print("   ✅ Consulter les chambres disponibles")
    print("   ✅ Historique de ses réservations")
    print("   ❌ PAS d'accès aux autres clients")
    print("   ❌ PAS de création de réservation (doit contacter réception)")
    print("-" * 70)
    
    print("\n💡 CONSEILS D'UTILISATION :")
    print("-" * 70)
    print("1. Testez chaque rôle en vous connectant avec les identifiants ci-dessus")
    print("2. Vérifiez les redirections automatiques après connexion")
    print("3. Essayez d'accéder à des pages non autorisées pour tester les restrictions")
    print("4. Le chatbot IA est disponible pour tous les rôles (icône robot en bas à droite)")
    print("-" * 70)
    
    print("\n✅ Tout est prêt ! Lancez le serveur avec : python manage.py runserver\n")

if __name__ == '__main__':
    create_users_with_roles()

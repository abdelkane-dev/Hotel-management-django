#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour créer des données de test pour l'application de gestion d'hôtel
Exécuter ce script avec : python create_sample_data.py
"""

import os
import django
from datetime import datetime, timedelta

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_management.settings')
django.setup()

from hotel.models import Client, Chambre, Reservation
from django.contrib.auth.models import User

def create_sample_data():
    """
    Crée des données de test pour l'application
    """
    print("🚀 Création des données de test...")
    
    # 1. Créer un utilisateur administrateur si nécessaire
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@hotel.com',
            password='admin123',
            first_name='Administrateur',
            last_name='Système'
        )
        print("✅ Utilisateur administrateur créé : admin / admin123")
    else:
        admin = User.objects.get(username='admin')
        print("ℹ️  Utilisateur administrateur déjà existant")
    
    # 2. Créer des clients
    clients_data = [
        {
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'jean.dupont@email.com',
            'telephone': '0601020304',
            'numero_piece_identite': 'FR123456789',
            'adresse': '12 Rue de la Paix',
            'ville': 'Paris',
            'pays': 'France'
        },
        {
            'nom': 'Martin',
            'prenom': 'Marie',
            'email': 'marie.martin@email.com',
            'telephone': '0602030405',
            'numero_piece_identite': 'FR987654321',
            'adresse': '45 Avenue des Champs',
            'ville': 'Lyon',
            'pays': 'France'
        },
        {
            'nom': 'Bernard',
            'prenom': 'Pierre',
            'email': 'pierre.bernard@email.com',
            'telephone': '0603040506',
            'numero_piece_identite': 'FR456789123',
            'adresse': '78 Boulevard Victor Hugo',
            'ville': 'Marseille',
            'pays': 'France'
        },
        {
            'nom': 'Dubois',
            'prenom': 'Sophie',
            'email': 'sophie.dubois@email.com',
            'telephone': '0604050607',
            'numero_piece_identite': 'FR321654987',
            'adresse': '23 Rue Nationale',
            'ville': 'Toulouse',
            'pays': 'France'
        }
    ]
    
    clients = []
    for data in clients_data:
        client, created = Client.objects.get_or_create(
            email=data['email'],
            defaults=data
        )
        if created:
            print(f"✅ Client créé : {client.nom_complet}")
        clients.append(client)
    
    # 3. Créer des chambres
    chambres_data = [
        # Chambres simples
        {'numero': '101', 'type_chambre': 'simple', 'prix_par_nuit': 50.00, 'capacite': 1},
        {'numero': '102', 'type_chambre': 'simple', 'prix_par_nuit': 55.00, 'capacite': 1},
        {'numero': '103', 'type_chambre': 'simple', 'prix_par_nuit': 50.00, 'capacite': 1},
        
        # Chambres doubles
        {'numero': '201', 'type_chambre': 'double', 'prix_par_nuit': 80.00, 'capacite': 2},
        {'numero': '202', 'type_chambre': 'double', 'prix_par_nuit': 85.00, 'capacite': 2},
        {'numero': '203', 'type_chambre': 'double', 'prix_par_nuit': 80.00, 'capacite': 2},
        {'numero': '204', 'type_chambre': 'double', 'prix_par_nuit': 90.00, 'capacite': 2},
        
        # Suites
        {'numero': '301', 'type_chambre': 'suite', 'prix_par_nuit': 150.00, 'capacite': 4},
        {'numero': '302', 'type_chambre': 'suite', 'prix_par_nuit': 180.00, 'capacite': 4},
        {'numero': '303', 'type_chambre': 'suite', 'prix_par_nuit': 200.00, 'capacite': 6},
    ]
    
    chambres = []
    for data in chambres_data:
        chambre, created = Chambre.objects.get_or_create(
            numero=data['numero'],
            defaults={
                **data,
                'statut': 'libre',
                'description': f"{data['type_chambre'].capitalize()} spacieuse avec vue",
                'climatisation': True,
                'wifi': True,
                'television': True,
                'minibar': data['type_chambre'] == 'suite'
            }
        )
        if created:
            print(f"✅ Chambre créée : {chambre.numero} ({chambre.get_type_chambre_display()})")
        chambres.append(chambre)
    
    # 4. Créer des réservations
    today = datetime.now().date()
    
    reservations_data = [
        {
            'client': clients[0],
            'chambre': chambres[3],  # Chambre 201
            'date_entree': today + timedelta(days=1),
            'date_sortie': today + timedelta(days=4),
            'nombre_personnes': 2,
            'statut': 'confirmee',
            'remarques': 'Arrivée tardive prévue'
        },
        {
            'client': clients[1],
            'chambre': chambres[7],  # Chambre 301 (suite)
            'date_entree': today + timedelta(days=5),
            'date_sortie': today + timedelta(days=10),
            'nombre_personnes': 3,
            'statut': 'confirmee',
            'remarques': 'Voyage de noces'
        },
        {
            'client': clients[2],
            'chambre': chambres[0],  # Chambre 101
            'date_entree': today - timedelta(days=2),
            'date_sortie': today + timedelta(days=1),
            'nombre_personnes': 1,
            'statut': 'en_cours',
            'remarques': 'Déplacement professionnel'
        }
    ]
    
    for data in reservations_data:
        # Vérifier si une réservation similaire existe déjà
        existing = Reservation.objects.filter(
            client=data['client'],
            chambre=data['chambre'],
            date_entree=data['date_entree']
        ).first()
        
        if not existing:
            reservation = Reservation(
                **data,
                cree_par=admin
            )
            reservation.save()
            
            # Mettre à jour le statut de la chambre si nécessaire
            if data['statut'] in ['confirmee', 'en_cours']:
                data['chambre'].statut = 'occupee'
                data['chambre'].save()
            
            print(f"✅ Réservation créée : {reservation.client.nom_complet} - Chambre {reservation.chambre.numero}")
    
    print("\n🎉 Données de test créées avec succès !")
    print("\n📊 Résumé :")
    print(f"   - {Client.objects.count()} clients")
    print(f"   - {Chambre.objects.count()} chambres")
    print(f"   - {Reservation.objects.count()} réservations")
    print(f"\n🔐 Connexion : admin / admin123")

if __name__ == '__main__':
    create_sample_data()

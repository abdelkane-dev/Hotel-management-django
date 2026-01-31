#!/usr/bin/env python
"""
Script pour créer des factures pour les réservations existantes
À exécuter avec : python manage.py shell < create_factures_existantes.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_management.settings')
django.setup()

from hotel.models import Reservation, Facture

def create_factures_for_existing_reservations():
    """Crée des factures pour toutes les réservations confirmées existantes"""
    
    print("🔍 Recherche des réservations confirmées existantes...")
    
    # Récupérer toutes les réservations confirmées sans facture
    reservations_sans_facture = Reservation.objects.filter(
        statut='confirmee'
    ).exclude(
        id__in=Facture.objects.values_list('reservation_id', flat=True)
    )
    
    count = reservations_sans_facture.count()
    print(f"📊 {count} réservations confirmées trouvées sans facture")
    
    if count == 0:
        print("✅ Toutes les réservations confirmées ont déjà une facture !")
        return
    
    # Créer les factures
    factures_creees = 0
    for reservation in reservations_sans_facture:
        try:
            facture = Facture.objects.create(
                reservation=reservation,
                client=reservation.client,
                montant_ht=reservation.prix_total / 1.20,  # TVA 20%
                cree_par=reservation.cree_par
            )
            factures_creees += 1
            print(f"✅ Facture {facture.numero_facture} créée pour réservation #{reservation.id}")
        except Exception as e:
            print(f"❌ Erreur pour réservation #{reservation.id}: {e}")
    
    print(f"\n🎉 {factures_creees} factures créées avec succès !")
    
    # Afficher le résumé
    total_factures = Facture.objects.count()
    print(f"📈 Total des factures dans le système : {total_factures}")

if __name__ == '__main__':
    create_factures_for_existing_reservations()

# -*- coding: utf-8 -*-
"""
Management command pour créer les factures manquantes
des réservations existantes
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from hotel.models import Reservation, Facture


class Command(BaseCommand):
    help = 'Crée les factures pour toutes les réservations confirmées sans facture'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche seulement ce qui sera fait sans créer de factures',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('🔍 Recherche des réservations confirmées sans facture...')
        
        # Récupérer les réservations confirmées sans facture
        reservations_sans_facture = Reservation.objects.filter(
            statut='confirmee'
        ).exclude(
            id__in=Facture.objects.values_list('reservation_id', flat=True)
        )
        
        count = reservations_sans_facture.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✅ Toutes les réservations confirmées ont déjà une facture !'))
            return
        
        self.stdout.write(f'📊 {count} réservations confirmées trouvées sans facture')
        
        if dry_run:
            self.stdout.write('\n📋 Réservations qui auront une facture (DRY RUN):')
            for res in reservations_sans_facture:
                self.stdout.write(f'  • Réservation #{res.id} - {res.client.nom_complet} - {res.prix_total}€')
            return
        
        # Créer les factures
        factures_creees = 0
        from decimal import Decimal
        for reservation in reservations_sans_facture:
            try:
                montant_ht = (reservation.prix_total / Decimal('1.20')) if reservation.prix_total is not None else Decimal('0')
                facture = Facture.objects.create(
                    reservation=reservation,
                    client=reservation.client,
                    montant_ht=montant_ht,  # TVA 20%
                    cree_par=reservation.cree_par
                )
                factures_creees += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Facture {facture.numero_facture} créée pour réservation #{reservation.id}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur pour réservation #{reservation.id}: {e}')
                )
        
        self.stdout.write(f'\n🎉 {factures_creees} factures créées avec succès !')
        
        # Résumé final
        total_factures = Facture.objects.count()
        total_reservations = Reservation.objects.filter(statut='confirmee').count()
        
        self.stdout.write('\n📈 Résumé:')
        self.stdout.write(f'  • Total des factures : {total_factures}')
        self.stdout.write(f'  • Total des réservations confirmées : {total_reservations}')
        self.stdout.write(f'  • Taux de facturation : {(total_factures/total_reservations*100):.1f}%')

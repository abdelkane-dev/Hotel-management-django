# -*- coding: utf-8 -*-
"""
Commande pour marquer toutes les factures en attente comme payées
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from hotel.models import Facture


class Command(BaseCommand):
    help = 'Marque toutes les factures en attente comme payées'

    def add_arguments(self, parser):
        parser.add_argument(
            '--method',
            type=str,
            default='carte',
            help='Méthode de paiement (carte, especes, virement, cheque, mobile_money)',
        )

    def handle(self, *args, **options):
        method = options['method']
        
        self.stdout.write('💰 Recherche des factures en attente...')
        
        # Récupérer les factures en attente
        factures_en_attente = Facture.objects.filter(statut='en_attente')
        count = factures_en_attente.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✅ Aucune facture en attente à traiter !'))
            return
        
        self.stdout.write(f'📊 {count} factures en attente trouvées')
        
        # Marquer comme payées
        payees = 0
        for facture in factures_en_attente:
            try:
                facture.marquer_comme_payee(method, f'AUTO_{timezone.now().strftime("%Y%m%d%H%M%S")}')
                payees += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Facture {facture.numero_facture} marquée comme payée')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur facture {facture.numero_facture}: {e}')
                )
        
        self.stdout.write(f'\n🎉 {payees} factures marquées comme payées avec succès !')
        
        # Résumé final
        total_factures = Facture.objects.count()
        factures_payees = Facture.objects.filter(statut='payee').count()
        
        self.stdout.write('\n📈 Nouvel état:')
        self.stdout.write(f'  • Total factures: {total_factures}')
        self.stdout.write(f'  • Factures payées: {factures_payees}')
        self.stdout.write(f'  • Taux de paiement: {(factures_payees/total_factures*100):.1f}%')
        
        self.stdout.write('\n🌐 Actualisez la page: http://127.0.0.1:8000/billing/')

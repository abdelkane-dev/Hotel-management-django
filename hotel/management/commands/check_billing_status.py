# -*- coding: utf-8 -*-
"""
Commande pour vérifier l'état des factures et déboguer le tableau de bord
"""

from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from hotel.models import Facture, FichePaie, ChargeComptable, Reservation
from django.utils import timezone


class Command(BaseCommand):
    help = 'Vérifie l\'état complet du système de facturation'

    def handle(self, *args, **options):
        self.stdout.write('🔍 DIAGNOSTIC COMPLET DU SYSTÈME DE FACTURATION')
        self.stdout.write('=' * 60)
        
        today = timezone.now().date()
        
        # 1. Vérifier les réservations
        self.stdout.write('\n📋 RÉSERVATIONS:')
        total_reservations = Reservation.objects.count()
        confirmed_reservations = Reservation.objects.filter(statut='confirmee').count()
        self.stdout.write(f'  • Total réservations: {total_reservations}')
        self.stdout.write(f'  • Réservations confirmées: {confirmed_reservations}')
        
        # 2. Vérifier les factures
        self.stdout.write('\n💰 FACTURES:')
        total_factures = Facture.objects.count()
        factures_payees = Facture.objects.filter(statut='payee').count()
        factures_en_attente = Facture.objects.filter(statut='en_attente').count()
        factures_mois_courant = Facture.objects.filter(
            date_emission__month=today.month,
            date_emission__year=today.year
        ).count()
        
        self.stdout.write(f'  • Total factures: {total_factures}')
        self.stdout.write(f'  • Factures payées: {factures_payees}')
        self.stdout.write(f'  • Factures en attente: {factures_en_attente}')
        self.stdout.write(f'  • Factures mois courant: {factures_mois_courant}')
        
        # 3. Calcul des revenus (selon la logique du dashboard)
        monthly_revenue = Facture.objects.filter(
            date_emission__month=today.month,
            date_emission__year=today.year,
            statut='payee'
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        
        total_revenue_all = Facture.objects.filter(
            statut='payee'
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        
        total_revenue_all_status = Facture.objects.aggregate(
            total=Sum('montant_ttc')
        )['total'] or 0
        
        self.stdout.write('\n💹 REVENUS:')
        self.stdout.write(f'  • Revenu mensuel (payées seulement): {monthly_revenue}€')
        self.stdout.write(f'  • Revenu total (payées seulement): {total_revenue_all}€')
        self.stdout.write(f'  • Revenu total (tous statuts): {total_revenue_all_status}€')
        
        # 4. Détail des factures
        self.stdout.write('\n📄 DÉTAIL DES FACTURES:')
        factures = Facture.objects.all().order_by('-date_emission')
        for facture in factures[:5]:  # 5 premières
            self.stdout.write(
                f'  • {facture.numero_facture} - {facture.client.nom_complet} - '
                f'{facture.montant_ttc}€ - {facture.get_statut_display()} - '
                f'{facture.date_emission.strftime("%d/%m/%Y")}'
            )
        
        # 5. Salaires et charges
        self.stdout.write('\n💼 SALAIRES ET CHARGES:')
        total_salaries = FichePaie.objects.filter(
            statut='paye'
        ).aggregate(total=Sum('salaire_net'))['total'] or 0
        
        total_charges = ChargeComptable.objects.filter(
            statut='payee'
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        
        self.stdout.write(f'  • Salaires payés: {total_salaries}€')
        self.stdout.write(f'  • Charges payées: {total_charges}€')
        
        # 6. Diagnostic du problème
        self.stdout.write('\n🔧 DIAGNOSTIC:')
        if total_factures == 0:
            self.stdout.write(self.style.WARNING('  ❌ Aucune facture trouvée - Exécutez create_missing_invoices'))
        elif factures_payees == 0:
            self.stdout.write(self.style.WARNING('  ❌ Toutes les factures sont "en_attente" - Elles doivent être marquées comme "payées"'))
        elif monthly_revenue == 0:
            self.stdout.write(self.style.WARNING('  ❌ Aucune facture payée ce mois-ci'))
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ Le système semble fonctionner'))
        
        # 7. Solution recommandée
        self.stdout.write('\n💡 SOLUTIONS RECOMMANDÉES:')
        if factures_en_attente > 0:
            self.stdout.write('  1. Marquer les factures comme "payées" via l\'interface /billing/')
            self.stdout.write('  2. Ou utiliser la commande: python manage.py pay_all_invoices')
        
        self.stdout.write('\n🌐 ACCÈS RAPIDE:')
        self.stdout.write('  • Tableau de bord: http://127.0.0.1:8000/billing/')
        self.stdout.write('  • Vérifier les factures: http://127.0.0.1:8000/billing/')

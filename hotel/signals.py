# -*- coding: utf-8 -*-
"""
Signaux Django pour l'automatisation comptable et des notifications
Ce fichier contient les signaux qui déclenchent des actions automatiques
lors de certains événements (création de réservation, etc.)
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
from .models import (
    Reservation, Facture, FichePaie, UserProfile, 
    ContactMessage, Maintenance, InventoryItem, Notification
)


@receiver(post_save, sender=Reservation)
def creer_facture_et_notification_automatique(sender, instance, created, **kwargs):
    """
    Crée automatiquement une facture ET une notification lorsqu'une réservation est créée ou confirmée
    """
    # Créer une facture si la réservation est nouvelle ET confirmée
    if created and instance.statut == 'confirmee':
        # Créer la facture automatiquement
        facture = Facture.objects.create(
            reservation=instance,
            client=instance.client,
            montant_ht=instance.prix_total / 1.20,  # TVA 20%
            cree_par=instance.cree_par,
            statut='payee'  # ✅ PAIEMENT AUTOMATIQUE à la réservation
        )
        # Marquer immédiatement comme payée
        facture.date_paiement = timezone.now()
        facture.moyen_paiement = 'carte'  # Par défaut, paiement en ligne
        facture.save()
        
        # Créer notification pour l'admin
        admins = User.objects.filter(is_superuser=True)
        notif = Notification.objects.create(
            type_notification='reservation_nouvelle',
            titre=f"Nouvelle réservation #{instance.id}",
            message=f"Réservation confirmée pour {instance.client.nom_complet} - Chambre {instance.chambre.numero} du {instance.date_entree} au {instance.date_sortie}. Facture {facture.numero_facture} générée et payée automatiquement.",
            priorite='moyenne',
            reservation=instance
        )
        notif.destinataires.set(admins)


@receiver(post_save, sender=Reservation)
def creer_facture_si_confirmee(sender, instance, created, **kwargs):
    """
    Crée une facture si une réservation existante passe au statut 'confirmee'
    """
    if not created and instance.statut == 'confirmee':
        # Vérifier si une facture existe déjà
        if not hasattr(instance, 'facture'):
            # Créer la facture automatiquement
            facture = Facture.objects.create(
                reservation=instance,
                client=instance.client,
                montant_ht=instance.prix_total / 1.20,  # TVA 20%
                cree_par=instance.cree_par,
                statut='payee'  # ✅ PAIEMENT AUTOMATIQUE
            )
            facture.date_paiement = timezone.now()
            facture.moyen_paiement = 'carte'
            facture.save()
            
            # Notification
            admins = User.objects.filter(is_superuser=True)
            notif = Notification.objects.create(
                type_notification='reservation_nouvelle',
                titre=f"Réservation #{instance.id} confirmée",
                message=f"Réservation confirmée pour {instance.client.nom_complet}. Facture {facture.numero_facture} générée et payée.",
                priorite='moyenne',
                reservation=instance
            )
            notif.destinataires.set(admins)


@receiver(pre_save, sender=Reservation)
def mettre_a_jour_statut_facture(sender, instance, **kwargs):
    """
    Met à jour le statut de la facture lorsque le statut de la réservation change
    """
    if instance.pk:  # Seulement lors d'une modification
        try:
            old_instance = Reservation.objects.get(pk=instance.pk)
            # Si la réservation est annulée, annuler aussi la facture
            if old_instance.statut != 'annulee' and instance.statut == 'annulee':
                facture = getattr(instance, 'facture', None)
                if facture and facture.statut != 'payee':
                    facture.statut = 'annulee'
                    facture.save()
        except Reservation.DoesNotExist:
            pass


@receiver(post_save, sender=ContactMessage)
def notifier_nouveau_message_contact(sender, instance, created, **kwargs):
    """
    Crée une notification admin lorsqu'un message client arrive
    """
    if created:
        admins = User.objects.filter(is_superuser=True)
        notif = Notification.objects.create(
            type_notification='message_client',
            titre=f"Nouveau message de {instance.nom}",
            message=f"Sujet: {instance.sujet_complet}\n\nMessage: {instance.message[:200]}{'...' if len(instance.message) > 200 else ''}",
            priorite='haute' if instance.urgence == 'critique' else 'moyenne',
            message_contact=instance
        )
        notif.destinataires.set(admins)


@receiver(post_save, sender=Maintenance)
def notifier_maintenance_urgente(sender, instance, created, **kwargs):
    """
    Crée une notification si une maintenance urgente est créée
    """
    if created and instance.type_maintenance == 'urgence':
        admins = User.objects.filter(is_superuser=True)
        notif = Notification.objects.create(
            type_notification='maintenance_urgente',
            titre=f"Maintenance urgente: {instance.titre}",
            message=f"Maintenance urgente créée: {instance.description[:200]}",
            priorite='critique',
            maintenance=instance
        )
        notif.destinataires.set(admins)


@receiver(post_save, sender=InventoryItem)
def notifier_alerte_stock(sender, instance, created, **kwargs):
    """
    Crée une notification si un article atteint son seuil d'alerte
    """
    if not created and instance.quantite_disponible <= instance.seuil_alerte and instance.quantite_disponible > 0:
        # Vérifier qu'une notification récente n'existe pas déjà pour cet article
        from datetime import timedelta
        recent_notif = Notification.objects.filter(
            type_notification='alerte_stock',
            article_inventaire=instance,
            date_creation__gte=timezone.now() - timedelta(hours=24)
        ).exists()
        
        if not recent_notif:
            admins = User.objects.filter(is_superuser=True)
            notif = Notification.objects.create(
                type_notification='alerte_stock',
                titre=f"Alerte stock: {instance.nom}",
                message=f"L'article '{instance.nom}' a atteint son seuil d'alerte. Quantité disponible: {instance.quantite_disponible}/{instance.seuil_alerte}",
                priorite='haute' if instance.quantite_disponible == 0 else 'moyenne',
                article_inventaire=instance
            )
            notif.destinataires.set(admins)


def generer_fiches_paie_mensuelles():
    """
    Fonction utilitaire pour générer les fiches de paie mensuelles
    À appeler via une tâche cron ou management command
    """
    from datetime import date
    
    # Premier jour du mois courant
    mois_courant = date(date.today().year, date.today().month, 1)
    
    # Récupérer tous les employés actifs
    employes_actifs = User.objects.filter(
        is_staff=True,
        is_active=True,
        profile__statut_employe='actif'
    )
    
    from decimal import Decimal

    for employe in employes_actifs:
        # Vérifier si la fiche de paie existe déjà
        if not FichePaie.objects.filter(employe=employe, mois=mois_courant).exists():
            profile = getattr(employe, 'profile', None)

            # Salaire sécurisé en Decimal
            salaire = Decimal(str(profile.salaire)) if profile and profile.salaire is not None else Decimal('0')

            # Calculer la prime d'ancienneté (1% par année, max 10%) en Decimal
            if profile and profile.date_embauche:
                annees_anciennete = (date.today() - profile.date_embauche).days // 365
                taux = (Decimal(annees_anciennete) * Decimal('0.01'))
                if taux > Decimal('0.10'):
                    taux = Decimal('0.10')
                prime_anciennete = (taux * salaire).quantize(Decimal('0.01'))
            else:
                prime_anciennete = Decimal('0.00')

            cotisations_sociales = (salaire * Decimal('0.22')).quantize(Decimal('0.01'))
            impot_source = (salaire * Decimal('0.15')).quantize(Decimal('0.01'))

            # Créer la fiche de paie
            FichePaie.objects.create(
                employe=employe,
                mois=mois_courant,
                salaire_brut=salaire,
                prime_anciennete=prime_anciennete,
                cotisations_sociales=cotisations_sociales,  # 22% de cotisations
                impot_source=impot_source,  # 15% d'impôt à la source
            )


def creer_charge_maintenance_automatique(maintenance):
    """
    Crée automatiquement une charge comptable lorsqu'une maintenance est terminée
    """
    from .models import ChargeComptable
    
    if maintenance.statut == 'terminee' and maintenance.actual_cost:
        ChargeComptable.objects.create(
            libelle=f"Maintenance - {maintenance.titre}",
            type_charge='maintenance',
            description=maintenance.description,
            montant_ht=maintenance.actual_cost / 1.20,  # TVA 20%
            date_facture=maintenance.date_fin.date() if maintenance.date_fin else timezone.now().date(),
            date_echeance=(maintenance.date_fin.date() if maintenance.date_fin else timezone.now().date()).replace(day=15),
            cree_par=maintenance.cree_par
        )


@receiver(post_save, sender=InventoryItem)
def creer_charge_automatique_inventory(sender, instance, created, **kwargs):
    """Crée automatiquement une charge comptable (type 'inventaire') lors de la création d'un article d'inventaire."""
    if not created:
        return
    try:
        from .models import ChargeComptable
        from datetime import timedelta
        # On ne connaît pas le montant d'achat dans le modèle InventoryItem : créer une charge placeholder à compléter
        ChargeComptable.objects.create(
            libelle=f"Achat inventaire - {instance.nom}",
            type_charge='inventaire',
            description=(f"Création automatique à l'ajout de l'article (réf: {instance.reference}). "
                         f"Quantité: {instance.quantite_totale}, disponible: {instance.quantite_disponible}"),
            montant_ht=0,
            date_facture=timezone.now().date(),
            date_echeance=timezone.now().date() + timedelta(days=30),
            cree_par=None
        )
    except Exception:
        # Ne pas interrompre la création de l'article si la création de la charge échoue
        pass


@receiver(post_save, sender=UserProfile)
def creer_fiche_paie_automatique(sender, instance, created, **kwargs):
    """Crée automatiquement une fiche de paie pour le mois courant lorsqu'un profil employé actif est créé."""
    if not created:
        return
    user = getattr(instance, 'user', None)
    if not user or not user.is_staff:
        return
    # Ne traiter que les profils marqués actifs
    if getattr(instance, 'statut_employe', '') != 'actif':
        return
    try:
        from decimal import Decimal
        from datetime import date
        mois_courant = date(timezone.now().year, timezone.now().month, 1)
        # Si une fiche existe déjà, ne pas en créer
        if FichePaie.objects.filter(employe=user, mois=mois_courant).exists():
            return
        salaire = Decimal(str(instance.salaire)) if instance.salaire is not None else Decimal('0.00')
        # Calcul de la prime d'ancienneté
        if instance.date_embauche:
            annees_anciennete = (timezone.now().date() - instance.date_embauche).days // 365
            taux = Decimal(annees_anciennete) * Decimal('0.01')
            if taux > Decimal('0.10'):
                taux = Decimal('0.10')
            prime_anciennete = (taux * salaire).quantize(Decimal('0.01'))
        else:
            prime_anciennete = Decimal('0.00')

        cotisations_sociales = (salaire * Decimal('0.22')).quantize(Decimal('0.01'))
        impot_source = (salaire * Decimal('0.15')).quantize(Decimal('0.01'))

        FichePaie.objects.create(
            employe=user,
            mois=mois_courant,
            salaire_brut=salaire,
            prime_anciennete=prime_anciennete,
            cotisations_sociales=cotisations_sociales,
            impot_source=impot_source,
            cree_par=None
        )
    except Exception:
        # Tolérer les erreurs ici pour ne pas bloquer la création du profil
        pass

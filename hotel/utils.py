# -*- coding: utf-8 -*-
"""
Fonctions utilitaires pour la gestion des rôles
"""

def get_user_role(user):
    """
    Retourne le rôle d'un utilisateur
    
    Returns:
        str: 'admin', 'employe' ou 'client'
    """
    if user.is_superuser:
        return 'admin'
    elif user.is_staff:
        return 'employe'
    else:
        return 'client'


def get_dashboard_url_for_role(user):
    """
    Retourne l'URL du dashboard approprié selon le rôle
    
    Returns:
        str: nom de l'URL Django (pour reverse() ou redirect())
    """
    role = get_user_role(user)
    
    if role == 'admin':
        return 'dashboard_admin'
    elif role == 'employe':
        return 'dashboard_employe'
    else:
        return 'dashboard_client'


def get_user_display_role(user):
    """
    Retourne le nom français du rôle pour l'affichage
    
    Returns:
        str: 'Administrateur', 'Employé' ou 'Client'
    """
    role = get_user_role(user)
    
    roles_display = {
        'admin': 'Administrateur',
        'employe': 'Employé',
        'client': 'Client'
    }
    
    return roles_display.get(role, 'Utilisateur')


# ============================================
# UTILITAIRES POUR LA DISPONIBILITÉ DES CHAMBRES
# ============================================

def check_chambre_disponibilite(chambre, date_debut, date_fin):
    """
    Vérifie si une chambre est disponible pour une période donnée
    
    Args:
        chambre: Instance de Chambre
        date_debut: Date de début de la réservation
        date_fin: Date de fin de la réservation
    
    Returns:
        tuple: (est_disponible (bool), message (str))
    """
    from django.utils import timezone
    from .models import Reservation
    
    # Vérifier si la chambre est en maintenance
    if chambre.statut == 'maintenance':
        return (False, "Cette chambre est actuellement en maintenance.")
    
    # Vérifier si les dates sont valides
    if date_debut >= date_fin:
        return (False, "La date de fin doit être après la date de début.")
    
    # Vérifier si la date de début est dans le passé
    if date_debut < timezone.now().date():
        return (False, "La date de début ne peut pas être dans le passé.")
    
    # Vérifier les réservations existantes qui se chevauchent
    reservations_conflits = Reservation.objects.filter(
        chambre=chambre,
        statut__in=['confirmee', 'en_cours', 'en_attente']
    ).exclude(
        # Exclure les réservations qui ne se chevauchent pas
        date_sortie__lte=date_debut  # Réservation se termine avant notre début
    ).exclude(
        date_entree__gte=date_fin  # Réservation commence après notre fin
    )
    
    if reservations_conflits.exists():
        return (False, f"Cette chambre est déjà réservée pour cette période. {reservations_conflits.count()} réservation(s) en conflit.")
    
    return (True, "Chambre disponible pour cette période.")


def get_chambres_disponibles(date_debut, date_fin, type_chambre=None, prix_max=None):
    """
    Récupère la liste des chambres disponibles pour une période donnée
    
    Args:
        date_debut: Date de début
        date_fin: Date de fin
        type_chambre: Optionnel, filtrer par type ('simple', 'double', 'suite')
        prix_max: Optionnel, prix maximum par nuit
    
    Returns:
        QuerySet: Chambres disponibles
    """
    from .models import Chambre, Reservation
    
    # Commencer avec toutes les chambres non en maintenance
    chambres = Chambre.objects.exclude(statut='maintenance')
    
    # Filtrer par type si demandé
    if type_chambre:
        chambres = chambres.filter(type_chambre=type_chambre)
    
    # Filtrer par prix si demandé
    if prix_max:
        chambres = chambres.filter(prix_par_nuit__lte=prix_max)
    
    # Exclure les chambres avec des réservations qui se chevauchent
    chambres_indisponibles = Reservation.objects.filter(
        statut__in=['confirmee', 'en_cours', 'en_attente']
    ).exclude(
        date_sortie__lte=date_debut
    ).exclude(
        date_entree__gte=date_fin
    ).values_list('chambre_id', flat=True).distinct()
    
    chambres = chambres.exclude(id__in=chambres_indisponibles)
    
    return chambres.order_by('type_chambre', 'prix_par_nuit', 'numero')


def get_statut_reel_chambre(chambre):
    """
    Détermine le statut réel d'une chambre en tenant compte des réservations actives
    
    Args:
        chambre: Instance de Chambre
    
    Returns:
        str: 'libre', 'occupee' ou 'maintenance'
    """
    from django.utils import timezone
    from .models import Reservation
    
    # Si la chambre est en maintenance, c'est son statut réel
    if chambre.statut == 'maintenance':
        return 'maintenance'
    
    # Vérifier s'il y a des réservations actives aujourd'hui
    aujourd_hui = timezone.now().date()
    
    reservations_actives = Reservation.objects.filter(
        chambre=chambre,
        statut__in=['confirmee', 'en_cours'],
        date_entree__lte=aujourd_hui,
        date_sortie__gt=aujourd_hui
    )
    
    # Si des réservations actives existent, la chambre est occupée
    if reservations_actives.exists():
        return 'occupee'
    
    # Sinon, la chambre est libre
    return 'libre'


def get_chambres_avec_statut_reel():
    """
    Récupère toutes les chambres avec leur statut réel calculé
    
    Returns:
        list: Liste de dictionnaires avec les informations de chambre et statut réel
    """
    from .models import Chambre
    
    chambres = Chambre.objects.all().order_by('type_chambre', 'numero')
    
    chambres_info = []
    for chambre in chambres:
        statut_reel = get_statut_reel_chambre(chambre)
        
        chambres_info.append({
            'chambre': chambre,
            'statut_reel': statut_reel,
            'disponible_maintenant': statut_reel == 'libre',
            'reservable_futur': statut_reel != 'maintenance'
        })
    
    return chambres_info

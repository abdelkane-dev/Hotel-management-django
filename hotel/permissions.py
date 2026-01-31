# -*- coding: utf-8 -*-
"""
Permissions et décorateurs pour la gestion des rôles des employés
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden

def employe_required(view_func):
    """
    Décorateur qui exige que l'utilisateur soit un employé (staff mais pas superuser)
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff or request.user.is_superuser:
            messages.error(request, "Accès réservé aux employés")
            return redirect('dashboard')
        
        # Vérifier que l'employé a un profil valide
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil employé non trouvé")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def permission_required(permission):
    """
    Décorateur qui exige une permission spécifique selon le poste de l'employé
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier que c'est un employé
            if not request.user.is_staff or request.user.is_superuser:
                messages.error(request, "Accès réservé aux employés")
                return redirect('dashboard')
            
            # Vérifier le profil
            if not hasattr(request.user, 'profile'):
                messages.error(request, "Profil employé non trouvé")
                return redirect('dashboard')
            
            # Vérifier la permission
            if not request.user.profile.has_permission(permission):
                messages.error(request, f"Permission '{permission}' requise pour cette action")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def module_access_required(module_name):
    """
    Décorateur qui exige l'accès à un module spécifique
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier que c'est un employé
            if not request.user.is_staff or request.user.is_superuser:
                messages.error(request, "Accès réservé aux employés")
                return redirect('dashboard')
            
            # Vérifier le profil
            if not hasattr(request.user, 'profile'):
                messages.error(request, "Profil employé non trouvé")
                return redirect('dashboard')
            
            # Vérifier l'accès au module
            if not request.user.profile.can_access_module(module_name):
                messages.error(request, f"Accès au module '{module_name}' non autorisé pour votre poste")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def poste_required(poste):
    """
    Décorateur qui exige un poste spécifique
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier que c'est un employé
            if not request.user.is_staff or request.user.is_superuser:
                messages.error(request, "Accès réservé aux employés")
                return redirect('dashboard')
            
            # Vérifier le profil
            if not hasattr(request.user, 'profile'):
                messages.error(request, "Profil employé non trouvé")
                return redirect('dashboard')
            
            # Vérifier le poste
            if request.user.profile.poste != poste:
                messages.error(request, f"Poste '{poste}' requis pour cette action")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def get_user_permissions(user):
    """
    Retourne toutes les permissions d'un utilisateur selon son poste
    """
    if not hasattr(user, 'profile'):
        return []
    
    if not user.profile.is_employe():
        return []
    
    # Retourner la liste des permissions selon le poste
    permissions_map = {
        'receptionniste': [
            'view_clients', 'create_clients', 'edit_clients',
            'view_reservations', 'create_reservations', 'edit_reservations', 'cancel_reservations',
            'view_calendar', 'edit_calendar',
            'view_rooms', 'edit_rooms_status',
            'view_billing', 'create_billing',
            'view_reports_basic'
        ],
        'concierge': [
            'view_clients', 'view_reservations', 'edit_reservations',
            'view_calendar',
            'view_rooms', 'edit_rooms_status',
            'view_services', 'create_services',
            'view_billing'
        ],
        'housekeeping': [
            'view_rooms', 'edit_rooms_status', 'edit_rooms_cleaning',
            'view_reservations', 'view_calendar',
            'view_maintenance_requests', 'create_maintenance_requests'
        ],
        'maintenance': [
            'view_rooms', 'edit_rooms_status',
            'view_maintenance_requests', 'edit_maintenance_requests',
            'view_equipment', 'edit_equipment'
        ],
        'restaurant': [
            'view_reservations', 'view_clients',
            'view_restaurant_orders', 'edit_restaurant_orders',
            'view_billing', 'create_billing'
        ],
        'manager': [
            'view_clients', 'create_clients', 'edit_clients',
            'view_reservations', 'create_reservations', 'edit_reservations', 'cancel_reservations',
            'view_calendar', 'edit_calendar',
            'view_rooms', 'edit_rooms', 'edit_rooms_status',
            'view_billing', 'edit_billing', 'create_billing',
            'view_reports', 'edit_reports',
            'view_employes', 'edit_employes_basic',
            'view_inventory', 'edit_inventory'
        ],
        'directeur': [
            'view_clients', 'create_clients', 'edit_clients', 'delete_clients',
            'view_reservations', 'create_reservations', 'edit_reservations', 'cancel_reservations', 'delete_reservations',
            'view_calendar', 'edit_calendar',
            'view_rooms', 'edit_rooms', 'edit_rooms_status', 'delete_rooms',
            'view_billing', 'edit_billing', 'create_billing', 'delete_billing',
            'view_reports', 'edit_reports', 'export_reports',
            'view_employes', 'create_employes', 'edit_employes', 'delete_employes',
            'view_inventory', 'edit_inventory', 'delete_inventory',
            'view_services', 'create_services', 'edit_services', 'delete_services',
            'view_marketing', 'edit_marketing'
        ]
    }
    
    return permissions_map.get(user.profile.poste, [])

def check_permission(user, permission):
    """
    Vérifie si un utilisateur a une permission spécifique
    """
    return permission in get_user_permissions(user)

def can_access_module(user, module_name):
    """
    Vérifie si un utilisateur peut accéder à un module
    """
    if not hasattr(user, 'profile'):
        return False
    
    accessible_modules = [module['name'] for module in user.profile.get_accessible_modules()]
    return module_name in accessible_modules

def get_accessible_modules_for_user(user):
    """
    Retourne les modules accessibles pour un utilisateur
    """
    if not hasattr(user, 'profile'):
        return []
    
    return user.profile.get_accessible_modules()

# Permissions spécifiques pour faciliter l'utilisation
class Permissions:
    # Clients
    VIEW_CLIENTS = 'view_clients'
    CREATE_CLIENTS = 'create_clients'
    EDIT_CLIENTS = 'edit_clients'
    DELETE_CLIENTS = 'delete_clients'
    
    # Réservations
    VIEW_RESERVATIONS = 'view_reservations'
    CREATE_RESERVATIONS = 'create_reservations'
    EDIT_RESERVATIONS = 'edit_reservations'
    CANCEL_RESERVATIONS = 'cancel_reservations'
    DELETE_RESERVATIONS = 'delete_reservations'
    
    # Calendrier
    VIEW_CALENDAR = 'view_calendar'
    EDIT_CALENDAR = 'edit_calendar'
    
    # Chambres
    VIEW_ROOMS = 'view_rooms'
    EDIT_ROOMS = 'edit_rooms'
    EDIT_ROOMS_STATUS = 'edit_rooms_status'
    EDIT_ROOMS_CLEANING = 'edit_rooms_cleaning'
    DELETE_ROOMS = 'delete_rooms'
    
    # Facturation
    VIEW_BILLING = 'view_billing'
    CREATE_BILLING = 'create_billing'
    EDIT_BILLING = 'edit_billing'
    DELETE_BILLING = 'delete_billing'
    
    # Rapports
    VIEW_REPORTS = 'view_reports'
    VIEW_REPORTS_BASIC = 'view_reports_basic'
    EDIT_REPORTS = 'edit_reports'
    EXPORT_REPORTS = 'export_reports'
    
    # Employés
    VIEW_EMPLOYES = 'view_employes'
    CREATE_EMPLOYES = 'create_employes'
    EDIT_EMPLOYES = 'edit_employes'
    EDIT_EMPLOYES_BASIC = 'edit_employes_basic'
    DELETE_EMPLOYES = 'delete_employes'
    
    # Inventaire
    VIEW_INVENTORY = 'view_inventory'
    EDIT_INVENTORY = 'edit_inventory'
    DELETE_INVENTORY = 'delete_inventory'
    
    # Services
    VIEW_SERVICES = 'view_services'
    CREATE_SERVICES = 'create_services'
    EDIT_SERVICES = 'edit_services'
    DELETE_SERVICES = 'delete_services'
    
    # Maintenance
    VIEW_MAINTENANCE_REQUESTS = 'view_maintenance_requests'
    CREATE_MAINTENANCE_REQUESTS = 'create_maintenance_requests'
    EDIT_MAINTENANCE_REQUESTS = 'edit_maintenance_requests'
    
    # Équipements
    VIEW_EQUIPMENT = 'view_equipment'
    EDIT_EQUIPMENT = 'edit_equipment'
    
    # Marketing
    VIEW_MARKETING = 'view_marketing'
    EDIT_MARKETING = 'edit_marketing'
    
    # Restaurant
    VIEW_RESTAURANT_ORDERS = 'view_restaurant_orders'
    EDIT_RESTAURANT_ORDERS = 'edit_restaurant_orders'

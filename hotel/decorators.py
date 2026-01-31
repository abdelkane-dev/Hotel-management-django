# -*- coding: utf-8 -*-
"""
Décorateurs personnalisés pour la gestion des rôles
Ces décorateurs permettent de protéger les vues selon le rôle de l'utilisateur
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """
    Décorateur pour restreindre l'accès aux administrateurs uniquement
    Usage : @admin_required
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Autoriser soit le superuser, soit un utilisateur staff, soit un utilisateur membre du groupe 'Admin'
        if request.user.is_superuser or request.user.is_staff or request.user.groups.filter(name='Admin').exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "⛔ Accès refusé : Cette page est réservée aux administrateurs.")
            # Rediriger vers le dashboard approprié selon le rôle
            if request.user.is_staff:
                return redirect('dashboard_employe')
            else:
                return redirect('dashboard_client')
    return wrapper


def employe_required(view_func):
    """
    Décorateur pour restreindre l'accès aux employés (et admins)
    Usage : @employe_required
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Autoriser les staff, superuser ou membres du groupe 'Employe' ou 'Admin'
        if request.user.is_staff or request.user.is_superuser or request.user.groups.filter(name='Employe').exists() or request.user.groups.filter(name='Admin').exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "⛔ Accès refusé : Cette page est réservée aux employés.")
            return redirect('dashboard_client')
    return wrapper


def client_required(view_func):
    """
    Décorateur pour restreindre l'accès aux clients authentifiés uniquement
    Usage : @client_required
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Les clients sont les utilisateurs qui ne sont ni staff ni superuser
        # Autoriser les utilisateurs non staff/non superuser ou membres explicites du groupe 'Client'
        if (not request.user.is_staff and not request.user.is_superuser) or request.user.groups.filter(name='Client').exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "⛔ Accès refusé : Cette page est réservée aux clients.")
            if request.user.is_superuser:
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_employe')
    return wrapper


def role_required(*allowed_roles):
    """
    Décorateur générique pour autoriser plusieurs rôles
    Usage : @role_required('admin', 'employe')
    
    Rôles disponibles :
    - 'admin' : Administrateur (is_superuser)
    - 'employe' : Employé (is_staff)
    - 'client' : Client (ni staff ni superuser)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user_role = None
            
            # Déterminer le rôle de l'utilisateur
            if request.user.is_superuser:
                user_role = 'admin'
            elif request.user.is_staff:
                user_role = 'employe'
            else:
                user_role = 'client'
            
            # Vérifier si le rôle est autorisé
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, f"⛔ Accès refusé : Vous n'avez pas les permissions nécessaires.")
                
                # Redirection selon le rôle actuel
                if user_role == 'admin':
                    return redirect('dashboard_admin')
                elif user_role == 'employe':
                    return redirect('dashboard_employe')
                else:
                    return redirect('dashboard_client')
        
        return wrapper
    return decorator

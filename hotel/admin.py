# -*- coding: utf-8 -*-
"""
Configuration de l'interface d'administration Django
"""

from django.contrib import admin
from .models import Client, Chambre, Reservation
from .models import UserProfile, EmployeeHistory, ClientSettings


# ============================================
# ADMINISTRATION DES CLIENTS
# ============================================
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Configuration de l'administration des clients
    """
    list_display = ['id', 'nom', 'prenom', 'email', 'telephone', 'ville', 'pays', 'date_inscription']
    list_filter = ['ville', 'pays', 'date_inscription']
    search_fields = ['nom', 'prenom', 'email', 'telephone', 'numero_piece_identite']
    ordering = ['-date_inscription']
    readonly_fields = ['date_inscription', 'derniere_modification']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'email', 'telephone', 'numero_piece_identite')
        }),
        ('Adresse', {
            'fields': ('adresse', 'ville', 'pays')
        }),
        ('Métadonnées', {
            'fields': ('date_inscription', 'derniere_modification'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# ADMINISTRATION DES CHAMBRES
# ============================================
@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    """
    Configuration de l'administration des chambres
    """
    list_display = ['numero', 'type_chambre', 'prix_par_nuit', 'capacite', 'statut', 'get_equipements_list']
    list_filter = ['type_chambre', 'statut', 'climatisation', 'wifi', 'television', 'minibar']
    search_fields = ['numero', 'description']
    ordering = ['numero']
    readonly_fields = ['date_creation', 'derniere_modification']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('numero', 'type_chambre', 'prix_par_nuit', 'capacite', 'statut')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Équipements', {
            'fields': ('climatisation', 'wifi', 'television', 'minibar')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'derniere_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def get_equipements_list(self, obj):
        """Affiche les équipements sous forme de liste"""
        equipements = obj.get_equipements()
        return ', '.join(equipements) if equipements else 'Aucun'
    get_equipements_list.short_description = 'Équipements'


# ============================================
# ADMINISTRATION DES RÉSERVATIONS
# ============================================
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """
    Configuration de l'administration des réservations
    """
    list_display = ['id', 'client', 'chambre', 'date_entree', 'date_sortie', 'nombre_nuits', 'prix_total', 'statut', 'cree_par']
    list_filter = ['statut', 'date_entree', 'date_sortie', 'date_creation']
    search_fields = ['client__nom', 'client__prenom', 'chambre__numero']
    ordering = ['-date_creation']
    readonly_fields = ['nombre_nuits', 'prix_total', 'date_creation', 'derniere_modification']
    autocomplete_fields = ['client']
    
    fieldsets = (
        ('Réservation', {
            'fields': ('client', 'chambre', 'date_entree', 'date_sortie')
        }),
        ('Détails', {
            'fields': ('nombre_personnes', 'statut', 'remarques')
        }),
        ('Calcul automatique', {
            'fields': ('nombre_nuits', 'prix_total'),
            'description': 'Ces champs sont calculés automatiquement'
        }),
        ('Métadonnées', {
            'fields': ('cree_par', 'date_creation', 'derniere_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Enregistrer l'utilisateur qui a créé la réservation"""
        if not change:  # Si c'est une nouvelle réservation
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'poste', 'salaire', 'date_embauche', 'statut_employe']
    search_fields = ['user__username', 'poste']


@admin.register(EmployeeHistory)
class EmployeeHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'field_changed', 'old_value', 'new_value', 'created_at']
    search_fields = ['user__username', 'action']


@admin.register(ClientSettings)
class ClientSettingsAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'language', 'timezone', 'currency', 'theme', 'date_updated']
    search_fields = ['user_profile__user__username', 'user_profile__user__email']
    readonly_fields = ['date_updated']

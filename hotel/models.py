# -*- coding: utf-8 -*-
"""
Models pour la gestion d'hôtel
Ce fichier contient tous les modèles de données de l'application
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from datetime import datetime, timedelta


# ============================================
# MODÈLE CLIENT
# ============================================
class Client(models.Model):
    """
    Modèle représentant un client de l'hôtel
    Contient toutes les informations nécessaires pour identifier un client
    """
    # Informations personnelles
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(unique=True, verbose_name="Email")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    
    # Informations d'identité
    numero_piece_identite = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Numéro de pièce d'identité"
    )
    
    # Adresse
    adresse = models.TextField(verbose_name="Adresse complète")
    ville = models.CharField(max_length=100, verbose_name="Ville")
    pays = models.CharField(max_length=100, verbose_name="Pays")
    
    # Métadonnées
    date_inscription = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    derniere_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['-date_inscription']  # Trier par date d'inscription décroissante
    
    def __str__(self):
        """Représentation textuelle du client"""
        return f"{self.nom} {self.prenom}"
    
    @property
    def nom_complet(self):
        """Retourne le nom complet du client"""
        return f"{self.prenom} {self.nom}"


# ============================================
# MODÈLE CHAMBRE
# ============================================
class Chambre(models.Model):
    """
    Modèle représentant une chambre d'hôtel
    Contient les informations sur le type, le prix et le statut
    """
    # Choix pour le type de chambre
    TYPE_CHOICES = [
        ('simple', 'Chambre Simple'),
        ('double', 'Chambre Double'),
        ('suite', 'Suite'),
    ]
    
    # Choix pour le statut de la chambre
    STATUT_CHOICES = [
        ('libre', 'Libre'),
        ('occupee', 'Occupée'),
        ('maintenance', 'En maintenance'),
    ]
    
    # Informations de base
    numero = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="Numéro de chambre"
    )
    type_chambre = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        verbose_name="Type de chambre"
    )
    
    # Prix et capacité
    prix_par_nuit = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix par nuit (€)"
    )
    capacite = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Capacité (nombre de personnes)"
    )
    
    # Statut et description
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='libre',
        verbose_name="Statut"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Description"
    )
    
    # Équipements
    climatisation = models.BooleanField(default=True, verbose_name="Climatisation")
    wifi = models.BooleanField(default=True, verbose_name="WiFi")
    television = models.BooleanField(default=True, verbose_name="Télévision")
    minibar = models.BooleanField(default=False, verbose_name="Minibar")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    derniere_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Chambre"
        verbose_name_plural = "Chambres"
        ordering = ['numero']  # Trier par numéro de chambre
    
    def __str__(self):
        """Représentation textuelle de la chambre"""
        return f"Chambre {self.numero} - {self.get_type_chambre_display()}"
    
    def est_disponible(self):
        """Vérifie si la chambre est actuellement disponible"""
        return self.statut == 'libre'
    
    def get_equipements(self):
        """Retourne la liste des équipements disponibles"""
        equipements = []
        if self.climatisation:
            equipements.append("Climatisation")
        if self.wifi:
            equipements.append("WiFi")
        if self.television:
            equipements.append("Télévision")
        if self.minibar:
            equipements.append("Minibar")
        return equipements


class ChambreImage(models.Model):
    """Images associées à une chambre (plusieurs images possibles)"""
    chambre = models.ForeignKey(Chambre, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='chambres/')
    caption = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = 'Image Chambre'
        verbose_name_plural = 'Images Chambres'

    def __str__(self):
        return f"Image chambre {self.chambre.numero} - {self.id}"


# ============================================
# MODÈLE MESSAGES DE CONTACT
# ============================================
class ContactMessage(models.Model):
    """
    Messages de contact des clients
    Permet de sauvegarder et suivre les communications
    """
    STATUT_CHOICES = [
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En cours de traitement'),
        ('repondu', 'Répondu'),
        ('resolu', 'Résolu'),
        ('archive', 'Archivé'),
    ]
    
    URGENCE_CHOICES = [
        ('normal', 'Normal - 24-48h'),
        ('urgent', 'Urgent - 4-8h'),
        ('critique', 'Critique - 1-2h'),
    ]
    
    # Informations sur l'expéditeur
    nom = models.CharField(max_length=100, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Email")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    
    # Client associé (si connecté)
    client = models.ForeignKey(
        'Client', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='messages',
        verbose_name="Client"
    )
    
    # Contenu du message
    sujet = models.CharField(max_length=200, verbose_name="Sujet")
    sujet_autre = models.CharField(max_length=200, blank=True, null=True, verbose_name="Sujet personnalisé")
    message = models.TextField(verbose_name="Message")
    
    # Métadonnées
    urgence = models.CharField(
        max_length=20, 
        choices=URGENCE_CHOICES, 
        default='normal',
        verbose_name="Niveau d'urgence"
    )
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='nouveau',
        verbose_name="Statut du message"
    )
    
    # Suivi
    date_envoi = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    date_traitement = models.DateTimeField(null=True, blank=True, verbose_name="Date de traitement")
    traite_par = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='messages_traites',
        verbose_name="Traité par"
    )
    
    # Réponse
    reponse = models.TextField(blank=True, null=True, verbose_name="Réponse")
    date_reponse = models.DateTimeField(null=True, blank=True, verbose_name="Date de réponse")
    
    # Métadonnées système
    ip_client = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP du client")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    newsletter = models.BooleanField(default=False, verbose_name="Newsletter")
    
    class Meta:
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        ordering = ['-date_envoi']
    
    def __str__(self):
        return f"Message de {self.nom} - {self.sujet}"
    
    @property
    def sujet_complet(self):
        """Retourne le sujet complet (avec sujet_autre si applicable)"""
        if self.sujet == 'autre' and self.sujet_autre:
            return self.sujet_autre
        return self.get_sujet_display()
    
    @property
    def est_recent(self):
        """Vérifie si le message est récent (moins de 24h)"""
        from django.utils import timezone
        return (timezone.now() - self.date_envoi).days == 0
    
    @property
    def delai_reponse(self):
        """Calcule le délai de réponse en heures"""
        if self.date_reponse and self.date_envoi:
            delta = self.date_reponse - self.date_envoi
            return delta.total_seconds() / 3600
        return None


# ============================================
# MODÈLE RÉSERVATION
# ============================================
class Reservation(models.Model):
    """
    Modèle représentant une réservation
    Lie un client à une chambre pour une période donnée
    """
    # Choix pour le statut de réservation
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    
    # Relations
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='reservations',
        verbose_name="Client"
    )
    chambre = models.ForeignKey(
        Chambre, 
        on_delete=models.CASCADE, 
        related_name='reservations',
        verbose_name="Chambre"
    )
    
    # Dates
    date_entree = models.DateField(verbose_name="Date d'entrée")
    date_sortie = models.DateField(verbose_name="Date de sortie")
    
    # Informations financières
    nombre_nuits = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre de nuits"
    )
    prix_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix total (€)"
    )
    
    # Statut et informations complémentaires
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='en_attente',
        verbose_name="Statut"
    )
    nombre_personnes = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre de personnes"
    )
    remarques = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Remarques"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    derniere_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    cree_par = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Créé par"
    )
    
    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-date_creation']  # Trier par date de création décroissante
    
    def __str__(self):
        """Représentation textuelle de la réservation"""
        return f"Réservation #{self.id} - {self.client.nom_complet} - Chambre {self.chambre.numero}"
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour calculer automatiquement:
        - Le nombre de nuits
        - Le prix total
        """
        # Calculer le nombre de nuits
        if self.date_entree and self.date_sortie:
            delta = self.date_sortie - self.date_entree
            self.nombre_nuits = delta.days
            
            # Calculer le prix total
            self.prix_total = self.nombre_nuits * self.chambre.prix_par_nuit
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """
        Validation personnalisée avant la sauvegarde
        """
        from django.core.exceptions import ValidationError
        
        # Vérifier que la date de sortie est après la date d'entrée
        if self.date_sortie <= self.date_entree:
            raise ValidationError("La date de sortie doit être après la date d'entrée")
        
        # Vérifier que le nombre de personnes ne dépasse pas la capacité de la chambre
        if self.nombre_personnes > self.chambre.capacite:
            raise ValidationError(
                f"Le nombre de personnes ({self.nombre_personnes}) dépasse "
                f"la capacité de la chambre ({self.chambre.capacite})"
            )
    
    def duree_sejour(self):
        """Retourne la durée du séjour en jours"""
        return (self.date_sortie - self.date_entree).days
    
    def est_active(self):
        """Vérifie si la réservation est actuellement active"""
        return self.statut in ['confirmee', 'en_cours']
    
    def peut_etre_annulee(self):
        """Vérifie si la réservation peut être annulée"""
        return self.statut not in ['terminee', 'annulee']

    @property
    def prix_par_nuit(self):
        """Retourne le prix moyen par nuit (sécurisé)."""
        try:
            if not self.nombre_nuits:
                return 0
            return self.prix_total / self.nombre_nuits
        except Exception:
            return 0


# ============================================
# MODÈLE PROFIL UTILISATEUR (POUR LES RÔLES)
# ============================================
class UserProfile(models.Model):
    """
    Modèle pour étendre User et lier les clients-utilisateurs
    Permet de gérer les 3 rôles : Admin, Employé, Client
    """
    # Lien avec l'utilisateur Django
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Utilisateur"
    )
    
    # Lien avec le modèle Client (uniquement pour les clients-utilisateurs)
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_profile',
        verbose_name="Profil Client"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création du profil")
    # Informations pour les employés
    POSTE_CHOICES = [
        ('receptionniste', 'Réceptionniste'),
        ('concierge', 'Concierge'),
        ('housekeeping', 'Housekeeping'),
        ('maintenance', 'Maintenance'),
        ('restaurant', 'Restaurant'),
        ('manager', 'Manager'),
        ('directeur', 'Directeur'),
    ]
    poste = models.CharField(
        max_length=20, 
        choices=POSTE_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name="Poste"
    )
    salaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Salaire (€)")
    date_embauche = models.DateField(null=True, blank=True, verbose_name="Date d'embauche")
    STATUT_EMPLOYE_CHOICES = [
        ('actif', 'Actif'),
        ('conge', 'En congé'),
        ('renvoye', 'Renvoyé'),
    ]
    statut_employe = models.CharField(max_length=20, choices=STATUT_EMPLOYE_CHOICES, default='actif')
    
    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"
    
    def __str__(self):
        return f"Profil de {self.user.username}"
    
    def get_role(self):
        """
        Retourne le rôle de l'utilisateur
        Logique :
        - is_superuser = Administrateur
        - is_staff ET NOT is_superuser = Employé
        - Ni l'un ni l'autre = Client
        """
        if self.user.is_superuser:
            return 'admin'
        elif self.user.is_staff:
            return 'employe'
        else:
            return 'client'
    
    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.user.is_superuser
    
    def is_employe(self):
        """Vérifie si l'utilisateur est employé"""
        return self.user.is_staff and not self.user.is_superuser
    
    def is_client(self):
        """Vérifie si l'utilisateur est client"""
        return not self.user.is_staff and not self.user.is_superuser
    
    def get_poste_display(self):
        """Retourne l'affichage du poste"""
        return dict(self.POSTE_CHOICES).get(self.poste, 'Non défini')
    
    def has_permission(self, permission):
        """
        Vérifie si l'employé a une permission spécifique selon son poste
        """
        if not self.is_employe():
            return False
        
        permissions = {
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
                # Le directeur a toutes les permissions sauf la gestion système
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
        
        return permission in permissions.get(self.poste, [])
    
    def get_accessible_modules(self):
        """
        Retourne la liste des modules accessibles selon le poste
        """
        modules = {
            'receptionniste': [
                {'name': 'clients', 'icon': 'fas fa-users', 'label': 'Clients', 'permissions': ['view', 'create', 'edit']},
                {'name': 'reservations', 'icon': 'fas fa-calendar-check', 'label': 'Réservations', 'permissions': ['view', 'create', 'edit', 'cancel']},
                {'name': 'calendar', 'icon': 'fas fa-calendar', 'label': 'Calendrier', 'permissions': ['view', 'edit']},
                {'name': 'rooms', 'icon': 'fas fa-bed', 'label': 'Chambres', 'permissions': ['view', 'edit_status']},
                {'name': 'billing', 'icon': 'fas fa-file-invoice', 'label': 'Facturation', 'permissions': ['view', 'create']},
                {'name': 'reports', 'icon': 'fas fa-chart-bar', 'label': 'Rapports', 'permissions': ['view_basic']}
            ],
            'concierge': [
                {'name': 'clients', 'icon': 'fas fa-users', 'label': 'Clients', 'permissions': ['view']},
                {'name': 'reservations', 'icon': 'fas fa-calendar-check', 'label': 'Réservations', 'permissions': ['view', 'edit']},
                {'name': 'calendar', 'icon': 'fas fa-calendar', 'label': 'Calendrier', 'permissions': ['view']},
                {'name': 'rooms', 'icon': 'fas fa-bed', 'label': 'Chambres', 'permissions': ['view', 'edit_status']},
                {'name': 'services', 'icon': 'fas fa-concierge-bell', 'label': 'Services', 'permissions': ['view', 'create']},
                {'name': 'billing', 'icon': 'fas fa-file-invoice', 'label': 'Facturation', 'permissions': ['view']}
            ],
            'housekeeping': [
                {'name': 'rooms', 'icon': 'fas fa-bed', 'label': 'Chambres', 'permissions': ['view', 'edit_status', 'edit_cleaning']},
                {'name': 'reservations', 'icon': 'fas fa-calendar-check', 'label': 'Réservations', 'permissions': ['view']},
                {'name': 'calendar', 'icon': 'fas fa-calendar', 'label': 'Calendrier', 'permissions': ['view']},
                {'name': 'maintenance', 'icon': 'fas fa-tools', 'label': 'Maintenance', 'permissions': ['view', 'create']}
            ],
            'maintenance': [
                {'name': 'rooms', 'icon': 'fas fa-bed', 'label': 'Chambres', 'permissions': ['view', 'edit_status']},
                {'name': 'maintenance', 'icon': 'fas fa-tools', 'label': 'Maintenance', 'permissions': ['view', 'edit']},
                {'name': 'equipment', 'icon': 'fas fa-cogs', 'label': 'Équipements', 'permissions': ['view', 'edit']}
            ],
            'restaurant': [
                {'name': 'reservations', 'icon': 'fas fa-calendar-check', 'label': 'Réservations', 'permissions': ['view']},
                {'name': 'clients', 'icon': 'fas fa-users', 'label': 'Clients', 'permissions': ['view']},
                {'name': 'orders', 'icon': 'fas fa-utensils', 'label': 'Commandes', 'permissions': ['view', 'edit']},
                {'name': 'billing', 'icon': 'fas fa-file-invoice', 'label': 'Facturation', 'permissions': ['view', 'create']}
            ],
            'manager': [
                {'name': 'clients', 'icon': 'fas fa-users', 'label': 'Clients', 'permissions': ['view', 'create', 'edit']},
                {'name': 'reservations', 'icon': 'fas fa-calendar-check', 'label': 'Réservations', 'permissions': ['view', 'create', 'edit', 'cancel']},
                {'name': 'calendar', 'icon': 'fas fa-calendar', 'label': 'Calendrier', 'permissions': ['view', 'edit']},
                {'name': 'rooms', 'icon': 'fas fa-bed', 'label': 'Chambres', 'permissions': ['view', 'edit']},
                {'name': 'billing', 'icon': 'fas fa-file-invoice', 'label': 'Facturation', 'permissions': ['view', 'edit', 'create']},
                {'name': 'reports', 'icon': 'fas fa-chart-bar', 'label': 'Rapports', 'permissions': ['view', 'edit']},
                {'name': 'employes', 'icon': 'fas fa-user-tie', 'label': 'Employés', 'permissions': ['view', 'edit_basic']},
                {'name': 'inventory', 'icon': 'fas fa-boxes', 'label': 'Inventaire', 'permissions': ['view', 'edit']}
            ],
            'directeur': [
                {'name': 'clients', 'icon': 'fas fa-users', 'label': 'Clients', 'permissions': ['view', 'create', 'edit', 'delete']},
                {'name': 'reservations', 'icon': 'fas fa-calendar-check', 'label': 'Réservations', 'permissions': ['view', 'create', 'edit', 'cancel', 'delete']},
                {'name': 'calendar', 'icon': 'fas fa-calendar', 'label': 'Calendrier', 'permissions': ['view', 'edit']},
                {'name': 'rooms', 'icon': 'fas fa-bed', 'label': 'Chambres', 'permissions': ['view', 'create', 'edit', 'delete']},
                {'name': 'billing', 'icon': 'fas fa-file-invoice', 'label': 'Facturation', 'permissions': ['view', 'edit', 'create', 'delete']},
                {'name': 'reports', 'icon': 'fas fa-chart-bar', 'label': 'Rapports', 'permissions': ['view', 'edit', 'export']},
                {'name': 'employes', 'icon': 'fas fa-user-tie', 'label': 'Employés', 'permissions': ['view', 'create', 'edit', 'delete']},
                {'name': 'inventory', 'icon': 'fas fa-boxes', 'label': 'Inventaire', 'permissions': ['view', 'edit', 'delete']},
                {'name': 'services', 'icon': 'fas fa-concierge-bell', 'label': 'Services', 'permissions': ['view', 'create', 'edit', 'delete']},
                {'name': 'marketing', 'icon': 'fas fa-bullhorn', 'label': 'Marketing', 'permissions': ['view', 'edit']}
            ]
        }
        
        return modules.get(self.poste, [])
    
    def can_access_module(self, module_name):
        """Vérifie si l'employé peut accéder à un module spécifique"""
        accessible_modules = [module['name'] for module in self.get_accessible_modules()]
        return module_name in accessible_modules
    
    def get_dashboard_stats_config(self):
        """
        Retourne la configuration des statistiques du dashboard selon le poste
        """
        configs = {
            'receptionniste': [
                {'name': 'reservations_today', 'label': 'Réservations du jour', 'icon': 'fas fa-calendar-check'},
                {'name': 'arrivals_today', 'label': 'Arrivées aujourd\'hui', 'icon': 'fas fa-sign-in-alt'},
                {'name': 'departures_today', 'label': 'Départs aujourd\'hui', 'icon': 'fas fa-sign-out-alt'},
                {'name': 'rooms_available', 'label': 'Chambres disponibles', 'icon': 'fas fa-bed'},
                {'name': 'pending_checkins', 'label': 'Check-ins en attente', 'icon': 'fas fa-clock'},
                {'name': 'new_clients_today', 'label': 'Nouveaux clients', 'icon': 'fas fa-user-plus'}
            ],
            'concierge': [
                {'name': 'active_reservations', 'label': 'Réservations actives', 'icon': 'fas fa-calendar-check'},
                {'name': 'services_requested', 'label': 'Services demandés', 'icon': 'fas fa-concierge-bell'},
                {'name': 'guest_messages', 'label': 'Messages clients', 'icon': 'fas fa-envelope'},
                {'name': 'transport_requests', 'label': 'Demandes transport', 'icon': 'fas fa-car'},
                {'name': 'special_requests', 'label': 'Demandes spéciales', 'icon': 'fas fa-star'}
            ],
            'housekeeping': [
                {'name': 'rooms_to_clean', 'label': 'Chambres à nettoyer', 'icon': 'fas fa-broom'},
                {'name': 'rooms_cleaned_today', 'label': 'Chambres nettoyées', 'icon': 'fas fa-check-circle'},
                {'name': 'maintenance_requests', 'label': 'Demandes maintenance', 'icon': 'fas fa-tools'},
                {'name': 'linen_changed', 'label': 'Draps changés', 'icon': 'fas fa-soap'},
                {'name': 'rooms_inspected', 'label': 'Chambres inspectées', 'icon': 'fas fa-clipboard-check'}
            ],
            'maintenance': [
                {'name': 'pending_requests', 'label': 'Demandes en attente', 'icon': 'fas fa-wrench'},
                {'name': 'completed_today', 'label': 'Terminées aujourd\'hui', 'icon': 'fas fa-check'},
                {'name': 'urgent_repairs', 'label': 'Réparations urgentes', 'icon': 'fas fa-exclamation-triangle'},
                {'name': 'equipment_status', 'label': 'Statut équipements', 'icon': 'fas fa-cogs'},
                {'name': 'preventive_maintenance', 'label': 'Maintenance préventive', 'icon': 'fas fa-calendar-alt'}
            ],
            'restaurant': [
                {'name': 'orders_today', 'label': 'Commandes du jour', 'icon': 'fas fa-utensils'},
                {'name': 'table_reservations', 'label': 'Réservations tables', 'icon': 'fas fa-table'},
                {'name': 'room_service', 'label': 'Room service', 'icon': 'fas fa-tray'},
                {'name': 'revenue_today', 'label': 'Revenus du jour', 'icon': 'fas fa-euro-sign'},
                {'name': 'special_events', 'label': 'Événements spéciaux', 'icon': 'fas fa-glass-cheers'}
            ],
            'manager': [
                {'name': 'occupancy_rate', 'label': 'Taux d\'occupation', 'icon': 'fas fa-percentage'},
                {'name': 'revenue_month', 'label': 'Revenus du mois', 'icon': 'fas fa-euro-sign'},
                {'name': 'active_reservations', 'label': 'Réservations actives', 'icon': 'fas fa-calendar-check'},
                {'name': 'staff_performance', 'label': 'Performance staff', 'icon': 'fas fa-chart-line'},
                {'name': 'customer_satisfaction', 'label': 'Satisfaction client', 'icon': 'fas fa-smile'},
                {'name': 'expenses_month', 'label': 'Dépenses du mois', 'icon': 'fas fa-money-bill-wave'}
            ],
            'directeur': [
                {'name': 'total_revenue', 'label': 'Revenu total', 'icon': 'fas fa-euro-sign'},
                {'name': 'occupancy_rate', 'label': 'Taux d\'occupation', 'icon': 'fas fa-percentage'},
                {'name': 'total_reservations', 'label': 'Total réservations', 'icon': 'fas fa-calendar-check'},
                {'name': 'staff_count', 'label': 'Effectif staff', 'icon': 'fas fa-users'},
                {'name': 'profit_margin', 'label': 'Marge bénéfice', 'icon': 'fas fa-chart-pie'},
                {'name': 'customer_retention', 'label': 'Rétention client', 'icon': 'fas fa-heart'}
            ]
        }
        
        return configs.get(self.poste, configs['receptionniste'])


class ClientSettings(models.Model):
    """Paramètres personnels et préférences pour un client-utilisateur"""
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name='Profil Utilisateur (paramètres)'
    )

    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
        ('es', 'Español'),
        ('de', 'Deutsch'),
    ]

    THEME_CHOICES = [
        ('light', 'Clair'),
        ('dark', 'Sombre'),
        ('auto', 'Automatique'),
    ]

    FONT_SIZE_CHOICES = [
        ('small', 'Petite'),
        ('medium', 'Moyenne'),
        ('large', 'Grande'),
    ]

    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='fr')
    timezone = models.CharField(max_length=64, default='Europe/Paris')
    currency = models.CharField(max_length=10, default='EUR')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    font_size = models.CharField(max_length=10, choices=FONT_SIZE_CHOICES, default='medium')

    # Sécurité et notifications
    two_factor = models.BooleanField(default=False)
    login_alerts = models.BooleanField(default=True)

    # Notifications par email
    email_reservations = models.BooleanField(default=True)
    email_promotions = models.BooleanField(default=False)
    email_newsletter = models.BooleanField(default=False)

    # Confidentialité
    public_profile = models.BooleanField(default=False)
    data_sharing = models.BooleanField(default=True)

    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paramètres Client'
        verbose_name_plural = 'Paramètres Clients'

    def __str__(self):
        return f"Paramètres de {self.user_profile.user.username}"


class EmployeeHistory(models.Model):
    """Historique des actions sur un employé (promotion, changement de salaire, renvoi, etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=100)
    field_changed = models.CharField(max_length=100, blank=True, null=True)
    old_value = models.CharField(max_length=200, blank=True, null=True)
    new_value = models.CharField(max_length=200, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


# ============================================
# MODÈLES COMPTABLES
# ============================================

class Facture(models.Model):
    """
    Modèle représentant une facture client
    Généré automatiquement lors de la réservation
    """
    STATUT_CHOICES = [
        ('payee', 'Payée'),
        ('en_attente', 'En attente'),
        ('remboursee', 'Remboursée'),
        ('annulee', 'Annulée'),
    ]
    
    MOYEN_PAIEMENT_CHOICES = [
        ('carte', 'Carte bancaire'),
        ('especes', 'Espèces'),
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    # Informations générales
    numero_facture = models.CharField(max_length=50, unique=True, verbose_name="Numéro de facture")
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='facture',
        verbose_name="Réservation associée"
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='factures',
        verbose_name="Client"
    )
    
    # Dates
    date_emission = models.DateTimeField(auto_now_add=True, verbose_name="Date d'émission")
    date_echeance = models.DateField(verbose_name="Date d'échéance")
    date_paiement = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")
    
    # Montants (calculés automatiquement)
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant HT")
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=20.0, verbose_name="Taux TVA (%)")
    montant_tva = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant TVA")
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant TTC")
    
    # Statut et paiement
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name="Statut")
    moyen_paiement = models.CharField(max_length=20, choices=MOYEN_PAIEMENT_CHOICES, blank=True, verbose_name="Moyen de paiement")
    reference_paiement = models.CharField(max_length=100, blank=True, verbose_name="Référence de paiement")
    
    # Métadonnées
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='factures_creees',
        verbose_name="Créée par"
    )
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_emission']
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_emission']),
        ]
    
    def __str__(self):
        return f"Facture {self.numero_facture} - {self.client.nom_complet}"
    
    def save(self, *args, **kwargs):
        # Générer un numéro de facture unique si non défini
        if not self.numero_facture:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_facture = Facture.objects.filter(numero_facture__startswith=f'F{date_str}').order_by('numero_facture').last()
            if last_facture:
                last_num = int(last_facture.numero_facture[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.numero_facture = f'F{date_str}{new_num:04d}'
        
        # Calculer les montants TVA et TTC (en Decimal pour éviter les erreurs float/Decimal)
        from decimal import Decimal
        taux = Decimal(str(self.taux_tva)) if self.taux_tva is not None else Decimal('0')
        montant_ht_dec = Decimal(self.montant_ht) if self.montant_ht is not None else Decimal('0')
        self.montant_tva = (montant_ht_dec * (taux / Decimal('100'))).quantize(Decimal('0.01'))
        self.montant_ttc = (montant_ht_dec + self.montant_tva).quantize(Decimal('0.01'))
        
        # Définir la date d'échéance (30 jours après émission)
        if not self.date_echeance:
            from datetime import timedelta
            from django.utils import timezone
            date_ref = self.date_emission.date() if self.date_emission else timezone.now().date()
            self.date_echeance = date_ref + timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    @property
    def est_en_retard(self):
        """Vérifie si la facture est en retard"""
        from django.utils import timezone
        return self.statut == 'en_attente' and self.date_echeance < timezone.now().date()
    
    def marquer_comme_payee(self, moyen_paiement, reference_paiement=''):
        """Marquer la facture comme payée"""
        from django.utils import timezone
        self.statut = 'payee'
        self.moyen_paiement = moyen_paiement
        self.reference_paiement = reference_paiement
        self.date_paiement = timezone.now()
        self.save()


class FichePaie(models.Model):
    """
    Modèle représentant une fiche de paie mensuelle pour un employé
    """
    STATUT_CHOICES = [
        ('a_payer', 'À payer'),
        ('paye', 'Payé'),
        ('retard', 'En retard'),
    ]
    
    MOYEN_PAIEMENT_CHOICES = [
        ('virement', 'Virement bancaire'),
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
    ]
    
    # Informations générales
    employe = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fiches_paie',
        verbose_name="Employé"
    )
    mois = models.DateField(verbose_name="Mois de paie")  # Premier jour du mois
    numero_fiche = models.CharField(max_length=50, unique=True, verbose_name="Numéro de fiche")
    
    # Salaire de base
    salaire_brut = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salaire brut")
    
    # Primes
    prime_anciennete = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prime d'ancienneté")
    prime_performance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prime de performance")
    prime_autres = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Autres primes")
    
    # Retenues
    cotisations_sociales = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Cotisations sociales")
    impot_source = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Impôt à la source")
    autres_retenu = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Autres retenues")
    
    # Calculs
    total_primes = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total primes")
    total_retenu = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total retenu")
    salaire_net = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salaire net")
    
    # Statut et paiement
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='a_payer', verbose_name="Statut")
    date_paiement = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")
    moyen_paiement = models.CharField(max_length=20, choices=MOYEN_PAIEMENT_CHOICES, blank=True, verbose_name="Moyen de paiement")
    reference_paiement = models.CharField(max_length=100, blank=True, verbose_name="Référence de paiement")
    
    # Métadonnées
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='fiches_paie_creees',
        verbose_name="Créée par"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Fiche de paie"
        verbose_name_plural = "Fiches de paie"
        ordering = ['-mois', 'employe']
        unique_together = ['employe', 'mois']
        indexes = [
            models.Index(fields=['employe', 'mois']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"Fiche paie {self.employe.get_full_name() or self.employe.username} - {self.mois.strftime('%m/%Y')}"
    
    def save(self, *args, **kwargs):
        # Générer un numéro de fiche unique si non défini
        if not self.numero_fiche:
            date_str = self.mois.strftime('%Y%m')
            last_fiche = FichePaie.objects.filter(numero_fiche__startswith=f'FP{date_str}').order_by('numero_fiche').last()
            if last_fiche:
                last_num = int(last_fiche.numero_fiche[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.numero_fiche = f'FP{date_str}{new_num:04d}'
        
        # Calculer les totaux et le salaire net
        self.total_primes = self.prime_anciennete + self.prime_performance + self.prime_autres
        self.total_retenu = self.cotisations_sociales + self.impot_source + self.autres_retenu
        self.salaire_net = self.salaire_brut + self.total_primes - self.total_retenu
        
        super().save(*args, **kwargs)
    
    def marquer_comme_payee(self, moyen_paiement, reference_paiement=''):
        """Marquer la fiche de paie comme payée"""
        from django.utils import timezone
        self.statut = 'paye'
        self.moyen_paiement = moyen_paiement
        self.reference_paiement = reference_paiement
        self.date_paiement = timezone.now()
        self.save()


class ChargeComptable(models.Model):
    """
    Modèle représentant une charge comptable (maintenance, inventaire, etc.)
    """
    TYPE_CHARGE_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('inventaire', 'Achat inventaire'),
        ('personnel', 'Personnel externe'),
        ('energie', 'Énergie (électricité, eau)'),
        ('assurance', 'Assurance'),
        ('marketing', 'Marketing'),
        ('autre', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('payee', 'Payée'),
        ('annulee', 'Annulée'),
    ]
    
    # Informations générales
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    type_charge = models.CharField(max_length=20, choices=TYPE_CHARGE_CHOICES, verbose_name="Type de charge")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Montants
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant HT")
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=20.0, verbose_name="Taux TVA (%)")
    montant_tva = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Montant TVA")
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant TTC")
    
    # Dates
    date_facture = models.DateField(verbose_name="Date de facture")
    date_echeance = models.DateField(verbose_name="Date d'échéance")
    date_paiement = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")
    
    # Statut et paiement
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name="Statut")
    fournisseur = models.CharField(max_length=200, blank=True, verbose_name="Fournisseur")
    reference_facture = models.CharField(max_length=100, blank=True, verbose_name="Référence facture")
    
    # Métadonnées
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='charges_creees',
        verbose_name="Créée par"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Charge comptable"
        verbose_name_plural = "Charges comptables"
        ordering = ['-date_facture']
        indexes = [
            models.Index(fields=['type_charge']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_facture']),
        ]
    
    def __str__(self):
        return f"{self.libelle} - {self.montant_ttc}€"
    
    def save(self, *args, **kwargs):
        from decimal import Decimal, InvalidOperation
        # S'assurer que les valeurs numériques sont des Decimals
        try:
            self.montant_ht = Decimal(str(self.montant_ht))
        except (InvalidOperation, TypeError, ValueError):
            self.montant_ht = Decimal('0.00')
        try:
            self.taux_tva = Decimal(str(self.taux_tva))
        except (InvalidOperation, TypeError, ValueError):
            self.taux_tva = Decimal('0.00')
        # Calculer les montants TVA et TTC avec précision
        self.montant_tva = (self.montant_ht * (self.taux_tva / Decimal('100.00'))).quantize(Decimal('0.01'))
        self.montant_ttc = (self.montant_ht + self.montant_tva).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)
    
    @property
    def est_en_retard(self):
        """Vérifie si la charge est en retard"""
        from django.utils import timezone
        return self.statut == 'en_attente' and self.date_echeance < timezone.now().date()


# ============================================
# MODÈLES POUR LA GESTION DE LA MAINTENANCE
# ============================================

class Maintenance(models.Model):
    """
    Modèle représentant une demande de maintenance
    """
    TYPE_CHOICES = [
        ('corrective', 'Maintenance corrective'),
        ('preventive', 'Maintenance préventive'),
        ('urgence', 'Maintenance d\'urgence'),
    ]
    
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    
    # Informations générales
    titre = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description détaillée")
    type_maintenance = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type de maintenance")
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='moyenne', verbose_name="Priorité")
    
    # Liaison avec les équipements
    chambre = models.ForeignKey(
        Chambre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenances',
        verbose_name="Chambre concernée"
    )
    equipement = models.CharField(max_length=200, blank=True, verbose_name="Équipement concerné")
    
    # Planification
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="Date prévue")
    date_debut = models.DateTimeField(null=True, blank=True, verbose_name="Date de début")
    date_fin = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    
    # Assignation et suivi
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenances_assignees',
        verbose_name="Assigné à"
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name="Statut")
    
    # Coûts
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Coût estimé")
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Coût réel")
    
    # Documents et notes
    notes = models.TextField(blank=True, null=True, verbose_name="Notes internes")
    
    # Métadonnées
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenances_creees',
        verbose_name="Créée par"
    )
    
    class Meta:
        verbose_name = "Maintenance"
        verbose_name_plural = "Maintenances"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['priorite']),
            models.Index(fields=['type_maintenance']),
            models.Index(fields=['date_creation']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.get_statut_display()}"
    
    @property
    def duree_intervention(self):
        """Calcule la durée de l'intervention"""
        if self.date_debut and self.date_fin:
            return self.date_fin - self.date_debut
        return None


# ============================================
# MODÈLES POUR LA GESTION DE L'INVENTAIRE
# ============================================
class InventoryCategory(models.Model):
    """Catégorie d'articles d'inventaire"""
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    derniere_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Catégorie d'inventaire"
        verbose_name_plural = "Catégories d'inventaire"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class InventoryItem(models.Model):
    """Article d'inventaire de l'hôtel"""
    # État de l'article
    ETAT_CHOICES = [
        ('neuf', 'Neuf'),
        ('bon', 'Bon état'),
        ('use', 'Usé'),
        ('hors_service', 'Hors service'),
    ]
    
    # Localisation principale
    LOCALISATION_CHOICES = [
        ('reception', 'Réception'),
        ('cuisine', 'Cuisine'),
        ('menage', 'Service de ménage'),
        ('maintenance', 'Maintenance'),
        ('depot', 'Dépôt'),
        ('autre', 'Autre'),
    ]

    # Informations de base
    nom = models.CharField(max_length=200, verbose_name="Nom de l'article")
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence")
    categorie = models.ForeignKey(
        'InventoryCategory', 
        on_delete=models.PROTECT, 
        related_name='articles',
        verbose_name="Catégorie"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Gestion des stocks
    quantite_totale = models.PositiveIntegerField(default=0, verbose_name="Quantité totale")
    quantite_disponible = models.PositiveIntegerField(default=0, verbose_name="Quantité disponible")
    seuil_alerte = models.PositiveIntegerField(default=5, verbose_name="Seuil d'alerte")
    
    # État et localisation
    etat = models.CharField(
        max_length=20, 
        choices=ETAT_CHOICES, 
        default='neuf',
        verbose_name="État"
    )
    localisation_principale = models.CharField(
        max_length=50, 
        choices=LOCALISATION_CHOICES,
        default='depot',
        verbose_name="Localisation principale"
    )
    localisation_detail = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="Détail de localisation"
    )
    
    # Métadonnées
    date_ajout = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    derniere_maj = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = "Article d'inventaire"
        verbose_name_plural = "Articles d'inventaire"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['categorie']),
            models.Index(fields=['etat']),
            models.Index(fields=['localisation_principale']),
        ]

    def __str__(self):
        return f"{self.nom} ({self.reference})"
    
    @property
    def statut_stock(self):
        """Détermine le statut du stock (normal, alerte, critique)"""
        if self.quantite_disponible == 0:
            return 'epuise'
        elif self.quantite_disponible <= self.seuil_alerte:
            return 'alerte'
        return 'normal'
    
    @property
    def quantite_utilisee(self):
        """Retourne la quantité utilisée (totale - disponible)"""
        return self.quantite_totale - self.quantite_disponible


class InventoryMovement(models.Model):
    """Mouvement d'inventaire (entrée, sortie, affectation, etc.)"""
    TYPE_MOUVEMENT_CHOICES = [
        ('entree', 'Entrée en stock'),
        ('sortie', 'Sortie de stock'),
        ('affectation', 'Affectation'),
        ('retour', 'Retour en stock'),
        ('perte', 'Perte/Vol'),
        ('casse', 'Casse'),
        ('ajustement', 'Ajustement d\'inventaire'),
    ]
    
    # Informations de base
    article = models.ForeignKey(
        InventoryItem, 
        on_delete=models.CASCADE, 
        related_name='mouvements',
        verbose_name="Article"
    )
    type_mouvement = models.CharField(
        max_length=20, 
        choices=TYPE_MOUVEMENT_CHOICES,
        verbose_name="Type de mouvement"
    )
    quantite = models.PositiveIntegerField(verbose_name="Quantité")
    
    # Détails de l'affectation (si applicable)
    chambre = models.ForeignKey(
        'Chambre', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='inventaire_affecte',
        verbose_name="Chambre concernée"
    )
    employe = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='mouvements_inventaire',
        verbose_name="Employé concerné"
    )
    
    # Informations complémentaires
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    effectue_par = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='actions_inventaire',
        verbose_name="Effectué par"
    )
    date_mouvement = models.DateTimeField(auto_now_add=True, verbose_name="Date du mouvement")
    
    class Meta:
        verbose_name = "Mouvement d'inventaire"
        verbose_name_plural = "Mouvements d'inventaire"
        ordering = ['-date_mouvement']
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['type_mouvement']),
            models.Index(fields=['date_mouvement']),
        ]
    
    def __str__(self):
        return f"{self.get_type_mouvement_display()} - {self.article.nom} x{self.quantite}"
    
    def save(self, *args, **kwargs):
        """Met à jour automatiquement les quantités disponibles lors de la sauvegarde"""
        # Si c'est une nouvelle entrée
        if not self.pk:
            if self.type_mouvement in ['entree', 'retour']:
                self.article.quantite_totale += self.quantite
                self.article.quantite_disponible += self.quantite
            elif self.type_mouvement in ['sortie', 'perte', 'casse']:
                self.article.quantite_disponible = max(0, self.article.quantite_disponible - self.quantite)
            elif self.type_mouvement == 'affectation':
                self.article.quantite_disponible = max(0, self.article.quantite_disponible - self.quantite)
            
            self.article.save()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Annule l'effet du mouvement sur les quantités lors de la suppression"""
        if self.type_mouvement in ['entree', 'retour']:
            self.article.quantite_totale = max(0, self.article.quantite_totale - self.quantite)
            self.article.quantite_disponible = max(0, self.article.quantite_disponible - self.quantite)
        elif self.type_mouvement in ['sortie', 'perte', 'casse']:
            self.article.quantite_disponible += self.quantite
        elif self.type_mouvement == 'affectation':
            self.article.quantite_disponible += self.quantite
        
        self.article.save()
        super().delete(*args, **kwargs)


# ============================================
# MODÈLE POUR LES NOTIFICATIONS ADMIN
# ============================================
class Notification(models.Model):
    """
    Modèle représentant une notification admin
    Centralise tous les événements système importants
    """
    TYPE_CHOICES = [
        ('alerte_stock', 'Alerte de stock'),
        ('maintenance_urgente', 'Maintenance urgente'),
        ('message_client', 'Message client'),
        ('reservation_nouvelle', 'Nouvelle réservation'),
        ('facture_impayee', 'Facture impayée'),
        ('employe_absent', 'Employé absent'),
        ('systeme', 'Alerte système'),
    ]
    
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]
    
    # Informations générales
    type_notification = models.CharField(max_length=30, choices=TYPE_CHOICES, verbose_name="Type")
    titre = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='moyenne', verbose_name="Priorité")
    
    # Données liées (optionnel)
    reservation = models.ForeignKey('Reservation', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    message_contact = models.ForeignKey('ContactMessage', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    maintenance = models.ForeignKey('Maintenance', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    article_inventaire = models.ForeignKey('InventoryItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    # Statut
    lue = models.BooleanField(default=False, verbose_name="Lue")
    traitee = models.BooleanField(default=False, verbose_name="Traitée")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_lecture = models.DateTimeField(null=True, blank=True, verbose_name="Date de lecture")
    date_traitement = models.DateTimeField(null=True, blank=True, verbose_name="Date de traitement")
    
    # Utilisateurs concernés
    destinataires = models.ManyToManyField(User, related_name='notifications_recues', blank=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['type_notification']),
            models.Index(fields=['priorite']),
            models.Index(fields=['lue']),
            models.Index(fields=['date_creation']),
        ]
    
    def __str__(self):
        return f"{self.get_type_notification_display()} - {self.titre}"
    
    def marquer_comme_lue(self, user=None):
        """Marque la notification comme lue"""
        from django.utils import timezone
        self.lue = True
        self.date_lecture = timezone.now()
        self.save()
    
    def marquer_comme_traitee(self):
        """Marque la notification comme traitée"""
        from django.utils import timezone
        self.traitee = True
        self.date_traitement = timezone.now()
        self.save()


# ============================================
# MODÈLE POUR LA CONFIGURATION DE L'AGENT IA
# ============================================
class AgentIAConfig(models.Model):
    """
    Configuration de l'agent IA pour l'administrateur
    Permet de contrôler le comportement et les limites de l'agent
    """
    # Activation
    actif = models.BooleanField(default=True, verbose_name="Agent IA actif")
    
    # Configuration générale
    nom_agent = models.CharField(max_length=100, default="Assistant Hôtel", verbose_name="Nom de l'agent")
    description = models.TextField(default="Assistant intelligent pour la gestion hôtelière", verbose_name="Description")
    
    # Périmètre fonctionnel
    peut_repondre_clients = models.BooleanField(default=True, verbose_name="Peut répondre aux clients")
    peut_consulter_donnees = models.BooleanField(default=True, verbose_name="Peut consulter les données")
    peut_suggerer_actions = models.BooleanField(default=True, verbose_name="Peut suggérer des actions")
    peut_generer_rapports = models.BooleanField(default=False, verbose_name="Peut générer des rapports")
    
    # Limitations
    max_requetes_jour = models.IntegerField(default=1000, verbose_name="Requêtes max par jour")
    requetes_aujourd_hui = models.IntegerField(default=0, verbose_name="Requêtes aujourd'hui")
    derniere_reinitialisation = models.DateField(auto_now_add=True, verbose_name="Dernière réinitialisation")
    
    # Logs et historique
    total_interactions = models.IntegerField(default=0, verbose_name="Total interactions")
    derniere_interaction = models.DateTimeField(null=True, blank=True, verbose_name="Dernière interaction")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    derniere_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    modifie_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Modifié par")
    
    class Meta:
        verbose_name = "Configuration Agent IA"
        verbose_name_plural = "Configurations Agent IA"
    
    def __str__(self):
        return f"Config Agent IA - {'Actif' if self.actif else 'Inactif'}"
    
    def incrementer_requete(self):
        """Incrémente le compteur de requêtes et gère la réinitialisation quotidienne"""
        from django.utils import timezone
        aujourd_hui = timezone.now().date()
        
        if self.derniere_reinitialisation < aujourd_hui:
            self.requetes_aujourd_hui = 0
            self.derniere_reinitialisation = aujourd_hui
        
        self.requetes_aujourd_hui += 1
        self.total_interactions += 1
        self.derniere_interaction = timezone.now()
        self.save()
    
    def peut_traiter_requete(self):
        """Vérifie si l'agent peut traiter une nouvelle requête"""
        from django.utils import timezone
        aujourd_hui = timezone.now().date()
        
        if self.derniere_reinitialisation < aujourd_hui:
            return self.actif
        
        return self.actif and self.requetes_aujourd_hui < self.max_requetes_jour
    
    @classmethod
    def get_config(cls):
        """Récupère ou crée la configuration unique"""
        config, created = cls.objects.get_or_create(id=1)
        return config


class AgentIAInteraction(models.Model):
    """
    Historique des interactions avec l'agent IA
    Permet de suivre et analyser les utilisations
    """
    config = models.ForeignKey(AgentIAConfig, on_delete=models.CASCADE, related_name='interactions')
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contenu de l'interaction
    question = models.TextField(verbose_name="Question")
    reponse = models.TextField(verbose_name="Réponse")
    
    # Contexte
    page_contexte = models.CharField(max_length=100, blank=True, verbose_name="Page de contexte")
    role_utilisateur = models.CharField(max_length=20, blank=True, verbose_name="Rôle utilisateur")
    
    # Métadonnées
    date_interaction = models.DateTimeField(auto_now_add=True, verbose_name="Date interaction")
    duree_traitement = models.FloatField(null=True, blank=True, verbose_name="Durée traitement (s)")
    
    # Feedback (optionnel)
    utile = models.BooleanField(null=True, blank=True, verbose_name="Réponse utile")
    
    class Meta:
        verbose_name = "Interaction Agent IA"
        verbose_name_plural = "Interactions Agent IA"
        ordering = ['-date_interaction']
    
    def __str__(self):
        return f"Interaction {self.id} - {self.utilisateur or 'Anonyme'} - {self.date_interaction.strftime('%d/%m/%Y %H:%M')}"

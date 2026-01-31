from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import InventoryItem, InventoryCategory, InventoryMovement, Chambre, Maintenance


class ClientSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)
    telephone = forms.CharField(max_length=20)
    numero_piece_identite = forms.CharField(max_length=50)
    adresse = forms.CharField(widget=forms.Textarea)
    ville = forms.CharField(max_length=100)
    pays = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "nom",
            "prenom",
            "telephone",
            "numero_piece_identite",
            "adresse",
            "ville",
            "pays",
        )


# ============================================
# FORMULAIRES POUR LA GESTION DE L'INVENTAIRE
# ============================================

class InventoryItemForm(forms.ModelForm):
    """Formulaire pour la création et la modification d'un article d'inventaire"""
    class Meta:
        model = InventoryItem
        fields = [
            'nom', 'reference', 'categorie', 'description',
            'quantite_totale', 'quantite_disponible', 'seuil_alerte',
            'etat', 'localisation_principale', 'localisation_detail'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'localisation_detail': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'quantite_totale': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantite_disponible': forms.NumberInput(attrs={'class': 'form-control'}),
            'seuil_alerte': forms.NumberInput(attrs={'class': 'form-control'}),
            'etat': forms.Select(attrs={'class': 'form-control'}),
            'localisation_principale': forms.Select(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # S'assurer que la catégorie est requise
        self.fields['categorie'].required = True
        # Ordonner les catégories par nom
        self.fields['categorie'].queryset = InventoryCategory.objects.all().order_by('nom')


class InventoryMovementForm(forms.ModelForm):
    """Formulaire pour enregistrer un mouvement d'inventaire"""
    class Meta:
        model = InventoryMovement
        fields = ['type_mouvement', 'quantite', 'chambre', 'employe', 'notes']
        widgets = {
            'type_mouvement': forms.Select(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control'}),
            'chambre': forms.Select(attrs={'class': 'form-control'}),
            'employe': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs optionnels
        self.fields['chambre'].required = False
        self.fields['employe'].required = False
        self.fields['notes'].required = False
        
        # Filtrer les chambres disponibles
        self.fields['chambre'].queryset = Chambre.objects.all().order_by('numero')
        # Filtrer les employés (utilisateurs avec is_staff=True)
        self.fields['employe'].queryset = User.objects.filter(is_staff=True).order_by('username')


class InventoryCategoryForm(forms.ModelForm):
    """Formulaire pour la création et la modification d'une catégorie d'inventaire"""
    class Meta:
        model = InventoryCategory
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class MaintenanceForm(forms.ModelForm):
    """Formulaire pour créer/éditer une maintenance"""
    class Meta:
        model = Maintenance
        # Use the model's field names
        fields = [
            'titre', 'description', 'type_maintenance', 'priorite',
            'chambre', 'equipement', 'scheduled_date', 'assigned_to', 'statut',
            'estimated_cost', 'notes'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Fuite d\'eau dans la salle de bain'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': "Décrivez en détail le problème ou l\'intervention nécessaire..."}),
            'type_maintenance': forms.Select(attrs={'class': 'form-select'}),
            'priorite': forms.Select(attrs={'class': 'form-select'}),
            'chambre': forms.Select(attrs={'class': 'form-select'}),
            'equipement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Climatiseur, Télévision, etc.'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre certains champs optionnels
        self.fields['chambre'].required = False
        self.fields['equipement'].required = False
        self.fields['assigned_to'].required = False
        self.fields['estimated_cost'].required = False


from .models import ClientSettings


class ClientSettingsForm(forms.ModelForm):
    """Formulaire pour éditer les paramètres utilisateur côté client"""
    class Meta:
        model = ClientSettings
        fields = [
            'language', 'timezone', 'currency', 'theme', 'font_size',
            'two_factor', 'login_alerts',
            'email_reservations', 'email_promotions', 'email_newsletter',
            'public_profile', 'data_sharing'
        ]
        widgets = {
            'language': forms.Select(attrs={'class': 'form-control'}),
            'timezone': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'font_size': forms.Select(attrs={'class': 'form-control'}),
            'two_factor': forms.CheckboxInput(attrs={'class': ''}),
            'login_alerts': forms.CheckboxInput(attrs={'class': ''}),
            'email_reservations': forms.CheckboxInput(attrs={'class': ''}),
            'email_promotions': forms.CheckboxInput(attrs={'class': ''}),
            'email_newsletter': forms.CheckboxInput(attrs={'class': ''}),
            'public_profile': forms.CheckboxInput(attrs={'class': ''}),
            'data_sharing': forms.CheckboxInput(attrs={'class': ''}),
        }

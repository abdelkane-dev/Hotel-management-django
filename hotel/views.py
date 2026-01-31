# -*- coding: utf-8 -*-
"""
Views pour la gestion d'hôtel
Ce fichier contient toutes les vues (contrôleurs) de l'application
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from datetime import datetime, date, timedelta

from .models import Client, Chambre, Reservation, UserProfile, ChambreImage
from .permissions import get_user_permissions
# ============================================
# API Chambres Disponibles
# ============================================
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
@csrf_exempt
def chambres_disponibles_api(request):
    """
    Retourne la liste des chambres disponibles selon les critères de recherche (POST) ou toutes les chambres disponibles (GET)
    """
    import json
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            check_in_str = data.get('check_in')
            check_out_str = data.get('check_out')
            room_type = data.get('room_type')
            adults = int(data.get('adults', 1))
            children = int(data.get('children', 0))
            from datetime import datetime
            check_in = datetime.strptime(check_in_str, '%d/%m/%Y').date()
            check_out = datetime.strptime(check_out_str, '%d/%m/%Y').date()
            chambres_query = Chambre.objects.filter(statut='libre')
            if room_type and room_type != 'all':
                chambres_query = chambres_query.filter(type_chambre=room_type)
            total_persons = adults + children
            chambres_query = chambres_query.filter(capacite__gte=total_persons)
            chambres_reservees = Reservation.objects.filter(
                statut__in=['confirmee', 'en_cours']
            ).filter(
                Q(date_entree__lte=check_out, date_sortie__gte=check_in)
            ).values_list('chambre_id', flat=True)
            chambres_disponibles = chambres_query.exclude(id__in=chambres_reservees)
        else:
            # GET: retourne toutes les chambres libres et non réservées aujourd'hui
            today = timezone.now().date()
            chambres_libres = Chambre.objects.filter(statut='libre')
            chambres_reservees = Reservation.objects.filter(
                date_sortie__gte=today,
                statut__in=['confirmee', 'en_cours']
            ).values_list('chambre_id', flat=True)
            chambres_disponibles = chambres_libres.exclude(id__in=chambres_reservees)

        data = []
        for chambre in chambres_disponibles:
            try:
                images = list(chambre.images.values_list('image', flat=True))
                data.append({
                    'id': chambre.id,
                    'numero': chambre.numero,
                    'type_chambre': chambre.get_type_chambre_display(),
                    'prix_par_nuit': float(chambre.prix_par_nuit),
                    'capacite': chambre.capacite,
                    'description': chambre.description or '',
                    'equipements': chambre.get_equipements(),
                    'images': images,
                })
            except Exception as e:
                print(f'Erreur chambre {chambre.id}: {e}')
                continue
        return JsonResponse(data, safe=False)
    except Exception as e:
        import traceback
        print('Erreur API chambres_disponibles:', str(e))
        print(traceback.format_exc())
        return JsonResponse({'error': f"{str(e)} (voir logs serveur)"}, status=400)

# ============================================
# API Créer Réservation
# ============================================
@require_http_methods(["POST"])
@csrf_exempt
def creer_reservation_api(request):
    """
    Crée une réservation réelle dans la base de données
    """
    import json
    
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Utilisateur non authentifié'}, status=401)
        
        data = json.loads(request.body)
        chambre_id = data.get('chambre_id')
        check_in_str = data.get('check_in')
        check_out_str = data.get('check_out')
        adults = int(data.get('adults', 1))
        children = int(data.get('children', 0))
        
        # Récupérer le client connecté
        try:
            # Essayer d'abord via le profil
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'client'):
                client = request.user.profile.client
            else:
                # Alternative: chercher un client avec le même email que l'utilisateur
                try:
                    client = Client.objects.get(email=request.user.email)
                except Client.DoesNotExist:
                    return JsonResponse({'error': 'Aucun profil client trouvé pour cet utilisateur'}, status=400)
            
            print(f'Client utilisé pour réservation: {client.nom_complet if client else "None"}')  # Debug
                
        except Exception as e:
            return JsonResponse({'error': f'Erreur lors de la récupération du client: {str(e)}'}, status=400)
        
        # Convertir les dates
        from datetime import datetime
        check_in = datetime.strptime(check_in_str, '%d/%m/%Y').date()
        check_out = datetime.strptime(check_out_str, '%d/%m/%Y').date()
        
        # Récupérer la chambre
        try:
            chambre = Chambre.objects.get(id=chambre_id, statut='libre')
        except Chambre.DoesNotExist:
            return JsonResponse({'error': 'Chambre non disponible'}, status=400)
        
        # Vérifier à nouveau la disponibilité (double check)
        existing_reservation = Reservation.objects.filter(
            chambre=chambre,
            statut__in=['confirmee', 'en_cours']
        ).filter(
            Q(date_entree__lte=check_out, date_sortie__gte=check_in)
        ).exists()
        
        if existing_reservation:
            return JsonResponse({'error': 'Chambre plus disponible pour ces dates'}, status=400)
        
        # Calculer le nombre de nuits et le prix total
        from datetime import timedelta
        nombre_nuits = (check_out - check_in).days
        if nombre_nuits <= 0:
            return JsonResponse({'error': 'Dates invalides'}, status=400)
        
        prix_total = float(chambre.prix_par_nuit) * nombre_nuits
        
        # Créer la réservation
        reservation = Reservation.objects.create(
            client=client,
            chambre=chambre,
            date_entree=check_in,
            date_sortie=check_out,
            nombre_nuits=nombre_nuits,
            prix_total=prix_total,
            nombre_personnes=adults + children,  # Ajout du champ manquant
            statut='en_attente'
        )
        
        return JsonResponse({
            'success': True,
            'reservation_id': reservation.id,
            'message': f'Réservation confirmée pour la chambre {chambre.numero}',
            'details': {
                'chambre': f'Chambre {chambre.numero}',
                'dates': f'{check_in_str} - {check_out_str}',
                'nuits': nombre_nuits,
                'total': f'{prix_total:.2f} €'
            }
        })
        
    except Exception as e:
        import traceback
        print('Erreur API creer_reservation:', str(e))
        print(traceback.format_exc())
        return JsonResponse({'error': f"{str(e)} (voir logs serveur)"}, status=400)
from .decorators import admin_required, employe_required, client_required, role_required
from .utils import get_user_role, get_dashboard_url_for_role
from .forms import ClientSignUpForm
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods
from django.db.models import Sum

# Simple inventory & maintenance models will be created as lightweight classes
from django.shortcuts import render



# ============================================
# VUES D'AUTHENTIFICATION
# ============================================

def login_view(request):
    """
    Vue pour la page de connexion
    Gère l'authentification et redirige selon le rôle
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authentifier l'utilisateur
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Connexion réussie
            login(request, user)
            
            # Déterminer le rôle et rediriger vers le dashboard approprié
            role = get_user_role(user)
            dashboard_url = get_dashboard_url_for_role(user)
            
            role_display = {
                'admin': 'Administrateur',
                'employe': 'Employé',
                'client': 'Client'
            }.get(role, 'Utilisateur')
            
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username} ({role_display}) !')
            return redirect(dashboard_url)
        else:
            # Échec de connexion
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'hotel/login.html')


def logout_view(request):
    """
    Vue pour la déconnexion
    """
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')


def client_signup(request):
    """
    Inscription publique pour les clients : crée User + Client + UserProfile
    """
    if request.method == 'POST':
        form = ClientSignUpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.email = form.cleaned_data.get('email')
                user.is_staff = False
                user.save()

                # créer le client lié
                client = Client.objects.create(
                    nom=form.cleaned_data.get('nom'),
                    prenom=form.cleaned_data.get('prenom'),
                    email=form.cleaned_data.get('email'),
                    telephone=form.cleaned_data.get('telephone'),
                    numero_piece_identite=form.cleaned_data.get('numero_piece_identite'),
                    adresse=form.cleaned_data.get('adresse'),
                    ville=form.cleaned_data.get('ville'),
                    pays=form.cleaned_data.get('pays'),
                )

                # créer le profil utilisateur lié (UserProfile import via models)
                from .models import UserProfile
                UserProfile.objects.create(user=user, client=client)

                # connexion automatique
                login(request, user)
                messages.success(request, 'Compte client créé et connecté.')
                return redirect('dashboard_client')
    else:
        form = ClientSignUpForm()
    return render(request, 'hotel/signup.html', {'form': form})


# ----------------------
# New Pages: Calendar, Billing, Inventory, Maintenance, Reports
# ----------------------

@login_required
def calendar_view(request):
    """Vue calendrier améliorée : affiche mois courant (ou date fournie), filtres et droits d'accès.

    - Admin/Employé : voit toutes les réservations
    - Client : voit uniquement ses réservations
    Les filtres sont passés en GET : date, chambre, client, statut, search
    """
    user = request.user
    today = timezone.now().date()

    # GET filters
    date_filter = request.GET.get('date') or today.isoformat()
    chambre_filter = request.GET.get('chambre')
    client_filter = request.GET.get('client')
    statut_filter = request.GET.get('statut')
    search = request.GET.get('search', '').strip()

    # Base queryset selon droits
    if user.is_superuser or user.is_staff:
        reservations = Reservation.objects.all()
    else:
        # client lié via champ `client` with une relation vers User (client.user)
        reservations = Reservation.objects.filter(client__user=user)

    # Apply simple filters
    try:
        if date_filter:
            dt = datetime.strptime(date_filter, '%Y-%m-%d').date() if isinstance(date_filter, str) else date_filter
            reservations = reservations.filter(date_entree__lte=dt, date_sortie__gte=dt)
    except Exception:
        # ignore invalid date
        pass

    if chambre_filter:
        reservations = reservations.filter(chambre__numero__icontains=chambre_filter)

    if client_filter:
        reservations = reservations.filter(Q(client__nom__icontains=client_filter) | Q(client__prenom__icontains=client_filter))

    if statut_filter:
        reservations = reservations.filter(statut__iexact=statut_filter)

    if search:
        reservations = reservations.filter(
            Q(client__nom__icontains=search) | Q(client__prenom__icontains=search) | Q(chambre__numero__icontains=search)
        )

    # Prepare month range for calendar display (start -> end of month)
    try:
        view_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
    except Exception:
        view_date = today

    start_month = view_date.replace(day=1)
    # end of month: move to next month's first day then -1 day
    next_month = (start_month + timedelta(days=32)).replace(day=1)
    end_month = next_month - timedelta(days=1)
    days_in_month = []
    cur = start_month
    while cur <= end_month:
        days_in_month.append(cur)
        cur = cur + timedelta(days=1)

    chambres = Chambre.objects.all().order_by('numero')
    clients = Client.objects.all().order_by('nom')

    context = {
        'reservations': reservations.order_by('date_entree'),
        'days_in_month': days_in_month,
        'chambres': chambres,
        'clients': clients,
        'today': today,
        'date_filter': view_date.isoformat(),
        'chambre_filter': chambre_filter or '',
        'client_filter': client_filter or '',
        'statut_filter': statut_filter or '',
        'search': search,
    }
    return render(request, 'hotel/calendar.html', context)


@role_required('admin', 'employe')
def billing_list(request):
    """List of invoices derived from reservations (simple billing list)"""
    invoices = Reservation.objects.filter(statut__in=['confirmee','terminee','en_cours']).order_by('-date_creation')
    total_revenue = invoices.aggregate(total=Sum('prix_total'))['total'] or 0
    return render(request, 'hotel/billing_list.html', {'invoices': invoices, 'total_revenue': total_revenue})


@role_required('admin', 'employe')
def billing_invoice(request, pk):
    """
    Affiche le détail d'une facture avec les informations de paiement
    """
    reservation = get_object_or_404(Reservation, pk=pk)
    
    # Calculer le montant TTC (TVA 20%)
    tva = Decimal('0.20')
    montant_ht = reservation.prix_total
    montant_tva = montant_ht * tva
    montant_ttc = montant_ht + montant_tva
    
    # Vérifier si la facture est en retard
    est_en_retard = reservation.statut == 'confirmee' and reservation.date_sortie < timezone.now().date()
    
    context = {
        'reservation': reservation,
        'montant_ht': montant_ht,
        'tva': tva * 100,  # Pourcentage
        'montant_tva': montant_tva,
        'montant_ttc': montant_ttc,
        'est_en_retard': est_en_retard,
    }
    
    return render(request, 'hotel/billing_invoice.html', context)


@role_required('admin', 'employe')
@require_http_methods(["POST"])
def record_payment(request, invoice_id):
    """
    Enregistre un paiement pour une facture
    """
    try:
        # Récupérer la réservation (facture)
        reservation = get_object_or_404(Reservation, pk=invoice_id)
        
        # Récupérer les données du formulaire
        amount = Decimal(request.POST.get('amount', '0'))
        payment_method = request.POST.get('payment_method', 'especes')
        payment_date = request.POST.get('payment_date', timezone.now().date())
        
        # Vérifier que le montant est valide
        if amount <= 0:
            messages.error(request, "Le montant doit être supérieur à zéro.")
            return redirect('billing_invoice', pk=invoice_id)
            
        # Créer un enregistrement de paiement (à adapter selon votre modèle de paiement)
        # Exemple: Payment.objects.create(...)
        
        # Mettre à jour le statut de la réservation si nécessaire
        if amount >= reservation.prix_total * Decimal('0.9'):  # 90% du montant pour considérer comme payé
            reservation.statut = 'terminee'
            reservation.save()
            messages.success(request, f"Paiement de {amount}€ enregistré avec succès. La réservation est marquée comme terminée.")
        else:
            messages.warning(request, f"Paiement partiel de {amount}€ enregistré. Le solde reste à payer.")
        
        return redirect('billing_invoice', pk=invoice_id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'enregistrement du paiement: {str(e)}")
        return redirect('billing_invoice', pk=invoice_id)


@role_required('admin', 'employe')
def inventory_list(request):
    """
    Affiche la liste des articles d'inventaire avec des options de filtrage et de recherche.
    Accessible par : Admin et Employé
    """
    from .models import InventoryItem, InventoryCategory
    from django.db.models import Q
    
    # Récupérer les paramètres de filtrage
    category_id = request.GET.get('categorie')
    status = request.GET.get('statut')
    search_query = request.GET.get('q', '')
    
    # Filtrer les articles
    items = InventoryItem.objects.select_related('categorie').all()
    
    # Appliquer les filtres
    if category_id:
        items = items.filter(categorie_id=category_id)
        
    if status == 'alerte':
        items = [item for item in items if item.quantite_disponible <= item.seuil_alerte and item.quantite_disponible > 0]
    elif status == 'rupture':
        items = items.filter(quantite_disponible=0)
    
    # Recherche par nom, référence ou description
    if search_query:
        items = items.filter(
            Q(nom__icontains=search_query) |
            Q(reference__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Récupérer les catégories pour le filtre
    categories = InventoryCategory.objects.all().order_by('nom')
    
    context = {
        'object_list': items,
        'categories': categories,
        'search_query': search_query,
        'selected_category': int(category_id) if category_id else None,
        'selected_status': status,
    }
    
    return render(request, 'hotel/inventory_list.html', context)


@role_required('admin', 'employe')
def inventory_create(request):
    """
    Vue pour créer un nouvel article d'inventaire
    Accessible par : Admin et Employé
    """
    from .forms import InventoryItemForm
    
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            # S'assurer que la quantité disponible ne dépasse pas la quantité totale
            if item.quantite_disponible > item.quantite_totale:
                item.quantite_disponible = item.quantite_totale
            item.save()
            messages.success(request, 'L\'article a été ajouté avec succès.')
            return redirect('inventory_detail', pk=item.pk)
    else:
        form = InventoryItemForm()
    
    return render(request, 'hotel/inventory_form.html', {'form': form, 'title': 'Ajouter un article'})


@role_required('admin', 'employe')
def maintenance_list(request):
    """Liste des interventions de maintenance
    Cette vue prépare le contexte attendu par le template `maintenance_list.html` qui utilise
    des clés en anglais (par ex. `maintenances`, `stats`, `rooms`). Pour rester compatible
    avec le modèle `Maintenance` (qui utilise des champs en français), on mappe les champs
    et on construit des objets légers attendus par le template.
    """
    from types import SimpleNamespace
    from django.db.models import Sum
    from .models import Maintenance, Chambre

    qs = Maintenance.objects.select_related('chambre', 'assigned_to').order_by('-date_creation')

    # Mappings entre codes FR (modèle) -> EN (template)
    TYPE_MAP = {'urgence': 'emergency', 'corrective': 'corrective', 'preventive': 'preventive'}
    PRIORITY_MAP = {'haute': 'high', 'moyenne': 'medium', 'basse': 'low', 'critique': 'high'}
    STATUS_MAP = {
        'en_attente': 'pending',
        'en_cours': 'in_progress',
        'terminee': 'completed',
        'annulee': 'cancelled',
    }

    maintenances = []
    for m in qs:
        # room object compatible with template (number, type)
        if m.chambre:
            room_obj = SimpleNamespace(id=m.chambre.id, number=m.chambre.numero, type=m.chambre.get_type_chambre_display())
        else:
            room_obj = None

        mapped = SimpleNamespace(
            id=m.id,
            room=room_obj,
            equipment=m.equipement,
            maintenance_type=TYPE_MAP.get(m.type_maintenance, 'preventive'),
            priority=PRIORITY_MAP.get(m.priorite, 'medium'),
            description=m.description,
            assigned_to=m.assigned_to,
            created_at=m.date_creation,
            scheduled_date=m.scheduled_date,
            estimated_cost=m.estimated_cost,
            status=STATUS_MAP.get(m.statut, 'pending'),
            original=m,  # conservar referencia si besoin dans templates/actions
        )
        maintenances.append(mapped)

    # Statistiques
    from django.utils import timezone
    now = timezone.now()

    stats = {
        'pending_count': qs.filter(statut='en_attente').count(),
        'in_progress_count': qs.filter(statut='en_cours').count(),
        'completed_count': qs.filter(statut='terminee').count(),
        'monthly_cost': qs.filter(date_creation__year=now.year, date_creation__month=now.month).aggregate(total=Sum('estimated_cost'))['total'] or 0,
    }

    # Rooms pour le filtre
    rooms_qs = Chambre.objects.all().order_by('numero')
    rooms = [SimpleNamespace(id=r.id, number=r.numero, type=r.get_type_chambre_display()) for r in rooms_qs]

    context = {
        'maintenances': maintenances,
        'stats': stats,
        'rooms': rooms,
    }

    return render(request, 'hotel/maintenance_list.html', context)


@role_required('admin', 'employe')
def inventory_detail(request, pk):
    """
    Affiche les détails d'un article d'inventaire
    Accessible par : Admin et Employé
    """
    from .models import InventoryItem, InventoryMovement
    
    try:
        item = InventoryItem.objects.select_related('categorie').get(pk=pk)
        mouvements = InventoryMovement.objects.filter(article=item).order_by('-date_mouvement')[:20]
        
        context = {
            'item': item,
            'mouvements': mouvements,
        }
        return render(request, 'hotel/inventory_detail.html', context)
    except InventoryItem.DoesNotExist:
        messages.error(request, "L'article demandé n'existe pas.")
        return redirect('inventory_list')


@role_required('admin', 'employe')
def inventory_update(request, pk):
    """
    Vue pour modifier un article d'inventaire existant
    Accessible par : Admin et Employé
    """
    from .models import InventoryItem
    from .forms import InventoryItemForm
    
    try:
        item = InventoryItem.objects.get(pk=pk)
        
        if request.method == 'POST':
            form = InventoryItemForm(request.POST, instance=item)
            if form.is_valid():
                updated_item = form.save(commit=False)
                # S'assurer que la quantité disponible ne dépasse pas la quantité totale
                if updated_item.quantite_disponible > updated_item.quantite_totale:
                    updated_item.quantite_disponible = updated_item.quantite_totale
                updated_item.save()
                messages.success(request, 'Les modifications ont été enregistrées avec succès.')
                return redirect('inventory_detail', pk=item.pk)
        else:
            form = InventoryItemForm(instance=item)
        
        return render(request, 'hotel/inventory_form.html', {
            'form': form,
            'title': f'Modifier {item.nom}',
            'item': item
        })
    except InventoryItem.DoesNotExist:
        messages.error(request, "L'article demandé n'existe pas.")
        return redirect('inventory_list')


@role_required('admin')
def inventory_delete(request, pk):
    """
    Vue pour supprimer un article d'inventaire
    Accessible par : Admin UNIQUEMENT
    """
    from .models import InventoryItem
    
    try:
        item = InventoryItem.objects.get(pk=pk)
        
        if request.method == 'POST':
            nom_article = item.nom
            item.delete()
            messages.success(request, f'L\'article "{nom_article}" a été supprimé avec succès.')
            return redirect('inventory_list')
            
        return render(request, 'hotel/inventory_confirm_delete.html', {'item': item})
    except InventoryItem.DoesNotExist:
        messages.error(request, "L'article demandé n'existe pas.")
        return redirect('inventory_list')


@role_required('admin', 'employe')
def inventory_movement(request, pk):
    """
    Vue pour gérer les mouvements d'inventaire (entrée, sortie, affectation, etc.)
    Accessible par : Admin et Employé
    """
    from .models import InventoryItem, InventoryMovement
    from .forms import InventoryMovementForm
    
    try:
        item = InventoryItem.objects.get(pk=pk)
        
        if request.method == 'POST':
            form = InventoryMovementForm(request.POST)
            if form.is_valid():
                mouvement = form.save(commit=False)
                mouvement.article = item
                mouvement.effectue_par = request.user
                
                # Vérifier la quantité disponible pour les sorties et affectations
                if mouvement.type_mouvement in ['sortie', 'affectation', 'perte', 'casse']:
                    if mouvement.quantite > item.quantite_disponible:
                        messages.error(request, f'Quantité insuffisante en stock. Disponible : {item.quantite_disponible}')
                        return render(request, 'hotel/inventory_movement.html', {
                            'form': form,
                            'item': item
                        })
                
                mouvement.save()  # La méthode save() du modèle gère la mise à jour des quantités
                
                messages.success(request, f'Le mouvement a été enregistré. Stock disponible : {item.quantite_disponible}')
                return redirect('inventory_detail', pk=item.pk)
        else:
            form = InventoryMovementForm(initial={
                'type_mouvement': 'entree',
                'quantite': 1,
            })
        
        # Récupérer l'historique des mouvements
        mouvements = InventoryMovement.objects.filter(article=item).order_by('-date_mouvement')[:20]
        
        return render(request, 'hotel/inventory_movement.html', {
            'form': form,
            'item': item,
            'mouvements': mouvements
        })
    except InventoryItem.DoesNotExist:
        messages.error(request, "L'article demandé n'existe pas.")
        return redirect('inventory_list')


@role_required('admin', 'employe')
def maintenance_create(request):
    from .forms import MaintenanceForm
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.cree_par = request.user
            maintenance.save()
            messages.success(request, 'Demande de maintenance créée.')
            return redirect('maintenance_list')
        else:
            messages.error(request, 'Impossible de créer la demande: Vérifiez le formulaire.')
    else:
        form = MaintenanceForm()
    return render(request, 'hotel/maintenance_form.html', {'form': form})


@role_required('admin', 'employe')
def maintenance_detail(request, pk):
    """Affiche les détails d'une intervention de maintenance"""
    from .models import Maintenance
    maintenance = get_object_or_404(Maintenance.objects.select_related('chambre', 'assigned_to'), pk=pk)
    return render(request, 'hotel/maintenance_detail.html', {'maintenance': maintenance})


@role_required('admin', 'employe')
def maintenance_edit(request, pk):
    """Modifier une maintenance existante"""
    from .models import Maintenance
    from .forms import MaintenanceForm

    maintenance = get_object_or_404(Maintenance, pk=pk)

    if request.method == 'POST':
        form = MaintenanceForm(request.POST, instance=maintenance)
        if form.is_valid():
            m = form.save(commit=False)
            m.save()
            messages.success(request, 'Maintenance mise à jour.')
            return redirect('maintenance_detail', pk=m.id)
        else:
            messages.error(request, 'Erreur : veuillez vérifier le formulaire.')
    else:
        form = MaintenanceForm(instance=maintenance)

    return render(request, 'hotel/maintenance_form.html', {'form': form})


@role_required('admin', 'employe')
@require_http_methods(["POST"])
def maintenance_complete(request, pk):
    """Marque une maintenance comme terminée (POST uniquement)"""
    from .models import Maintenance
    from django.utils import timezone

    maintenance = get_object_or_404(Maintenance, pk=pk)
    maintenance.statut = 'terminee'
    maintenance.date_fin = timezone.now()
    maintenance.save()
    messages.success(request, 'Intervention clôturée.')
    return redirect('maintenance_detail', pk=pk)


@role_required('admin', 'employe')
def reports_view(request):
    """
    Tableau de bord de performance hôtel
    KPIs commerciaux, financiers et opérationnels
    """
    from django.db.models import Sum, Count, Q, Avg, F
    from django.utils import timezone
    from datetime import datetime, timedelta
    from decimal import Decimal
    import calendar
    
    try:
        today = timezone.now().date()
        current_month = today.replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        # Filtres de période
        period = request.GET.get('period', 'month')  # day, month, year
        
        # ============== PERFORMANCE COMMERCIALE ==============
        
        # Réservations totales
        total_reservations = Reservation.objects.count()
        
        # Réservations par statut
        reservations_stats = {
            'total': total_reservations,
            'confirmee': Reservation.objects.filter(statut='confirmee').count(),
            'en_cours': Reservation.objects.filter(statut='en_cours').count(),
            'terminee': Reservation.objects.filter(statut='terminee').count(),
            'annulee': Reservation.objects.filter(statut='annulee').count(),
        }
        
        # Taux d'occupation (période actuelle)
        if period == 'month':
            period_start = current_month
            period_end = today
        elif period == 'year':
            period_start = today.replace(month=1, day=1)
            period_end = today
        else:  # day
            period_start = today
            period_end = today
        
        # Chambres occupées vs total
        chambres_total = Chambre.objects.count()
        chambres_occupees = Reservation.objects.filter(
            statut__in=['confirmee', 'en_cours'],
            date_entree__lte=period_end,
            date_sortie__gte=period_start
        ).values('chambre').distinct().count()
        
        taux_occupation = (chambres_occupees / chambres_total * 100) if chambres_total > 0 else 0
        
        # RevPAR (Revenue Per Available Room)
        total_revenue_period = Reservation.objects.filter(
            statut__in=['confirmee', 'en_cours', 'terminee'],
            date_entree__lte=period_end,
            date_sortie__gte=period_start
        ).aggregate(total=Sum('prix_total'))['total'] or 0
        
        days_in_period = (period_end - period_start).days + 1
        revpar = (total_revenue_period / (chambres_total * days_in_period)) if chambres_total > 0 and days_in_period > 0 else 0
        
        # ============== PERFORMANCE FINANCIÈRE ==============
        
        # Revenus réels (basés sur les paiements enregistrés dans les factures)
        paiements_confirms = Facture.objects.filter(
            statut='payee',
            date_paiement__date__gte=period_start,
            date_paiement__date__lte=period_end
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        
        # Revenus estimés (basés sur les réservations)
        revenue_estimee = Reservation.objects.filter(
            statut__in=['confirmee', 'en_cours', 'terminee'],
            date_entree__lte=period_end,
            date_sortie__gte=period_start
        ).aggregate(total=Sum('prix_total'))['total'] or 0
        
        # Charges du mois (salaires + maintenance + autres)
        from .models import FichePaie, ChargeComptable
        
        salaires_mois = FichePaie.objects.filter(
            mois__year=today.year,
            mois__month=today.month,
            statut='paye'
        ).aggregate(total=Sum('salaire_net'))['total'] or 0
        
        maintenance_mois = ChargeComptable.objects.filter(
            type_charge='maintenance',
            date_facture__year=today.year,
            date_facture__month=today.month
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        
        autres_charges_mois = ChargeComptable.objects.filter(
            type_charge__in=['inventaire', 'autre'],
            date_facture__year=today.year,
            date_facture__month=today.month
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        
        total_charges_mois = salaires_mois + maintenance_mois + autres_charges_mois
        
        # Bénéfice estimé
        benefice_estime = revenue_estimee - total_charges_mois
        
        # ============== PERFORMANCE OPÉRATIONNELLE ==============
        
        # Clients
        total_clients = Client.objects.count()
        nouveaux_clients_mois = Client.objects.filter(
            date_creation__year=today.year,
            date_creation__month=today.month
        ).count()
        
        # Maintenance
        maintenance_stats = {
            'total': Maintenance.objects.count(),
            'en_attente': Maintenance.objects.filter(statut='en_attente').count(),
            'en_cours': Maintenance.objects.filter(statut='en_cours').count(),
            'terminee': Maintenance.objects.filter(statut='terminee').count(),
            'cout_mois': maintenance_mois,
        }
        
        # Employés
        total_employes = User.objects.filter(is_staff=True, is_active=True).count()
        
        # ============== INDICATEURS CLÉS ==============
        
        # Performance commerciale
        performance_commerciale = {
            'total_reservations': reservations_stats,
            'taux_occupation': round(taux_occupation, 1),
            'revpar': round(revpar, 2),
            'revenue_period': round(total_revenue_period, 2),
            'chambres_total': chambres_total,
            'chambres_occupees': chambres_occupees,
        }
        
        # Performance financière
        performance_financiere = {
            'revenus_reels': round(paiements_confirms, 2),
            'revenus_estimes': round(revenue_estimee, 2),
            'charges_totales': round(total_charges_mois, 2),
            'salaires': round(salaires_mois, 2),
            'maintenance': round(maintenance_mois, 2),
            'autres_charges': round(autres_charges_mois, 2),
            'benefice_estime': round(benefice_estime, 2),
        }
        
        # Performance opérationnelle
        performance_operationnelle = {
            'total_clients': total_clients,
            'nouveaux_clients_mois': nouveaux_clients_mois,
            'maintenance': maintenance_stats,
            'total_employes': total_employes,
        }
        
        # Droits d'accès
        is_admin = request.user.is_superuser or request.user.is_staff
        
        context = {
            'period': period,
            'performance_commerciale': performance_commerciale,
            'performance_financiere': performance_financiere if is_admin else None,  # Limité aux admins
            'performance_operationnelle': performance_operationnelle,
            'is_admin': is_admin,
            'today': today,
            'period_start': period_start,
            'period_end': period_end,
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception('Erreur lors du calcul des metrics pour reports_view')
        from django.contrib import messages
        messages.error(request, f"Erreur calcul rapport: {str(e)}")
        # Fournir un contexte minimal pour éviter l'erreur 500
        context = {
            'period': request.GET.get('period', 'month'),
            'performance_commerciale': {},
            'performance_financiere': {},
            'performance_operationnelle': {},
            'is_admin': request.user.is_superuser or request.user.is_staff,
            'today': timezone.now().date(),
            'period_start': request.GET.get('period_start', timezone.now().date()),
            'period_end': request.GET.get('period_end', timezone.now().date()),
        }
    
    return render(request, 'hotel/reports.html', context)


@admin_required
def create_employee(request):
    """Formulaire simple accessible uniquement aux admins pour créer un employé (is_staff=True)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        if not username or not password:
            messages.error(request, 'Veuillez renseigner un nom d\'utilisateur et un mot de passe.')
        else:
            user = User.objects.create_user(username=username, password=password, email=email)
            user.is_staff = True
            user.save()

            # Créer ou mettre à jour le profil employé avec les champs complémentaires
            from .models import UserProfile
            poste = request.POST.get('poste')
            salaire = request.POST.get('salaire')
            date_embauche = request.POST.get('date_embauche')
            statut_employe = request.POST.get('statut_employe') or 'actif'

            # conversion salaire
            try:
                salaire_val = float(salaire) if salaire else None
            except Exception:
                salaire_val = None

            profile = UserProfile.objects.create(
                user=user,
                poste=poste or '',
                salaire=salaire_val,
                date_embauche=parse_date(date_embauche) if date_embauche else None,
                statut_employe=statut_employe,
            )

            messages.success(request, f"Employé '{username}' créé avec succès.")
            return redirect('employee_list')
    # fournir la liste des postes existants pour le select
    from .models import UserProfile as _UP
    from .constants import STANDARD_POSITIONS
    postes_qs = _UP.objects.exclude(poste__isnull=True).exclude(poste__exact='').values_list('poste', flat=True).distinct()
    postes_set = set([p for p in postes_qs if p]) | set(STANDARD_POSITIONS)
    postes_choices = sorted(postes_set)
    return render(request, 'hotel/create_employee.html', {'postes_choices': postes_choices})


@admin_required
def employee_list(request):
    """Liste des employés (is_staff=True, non superusers)"""
    # Récupérer les paramètres de recherche/filtrage (via GET)
    q = request.GET.get('q', '').strip()
    poste = request.GET.get('poste', '').strip()
    is_active = request.GET.get('is_active', '')

    # Base queryset : employés (staff) sans superusers
    employees = User.objects.filter(is_staff=True).exclude(is_superuser=True).order_by('username')

    # Joindre sur le profil pour filtres basés sur le profil
    from .models import UserProfile

    # Appliquer recherche textuelle
    if q:
        employees = employees.filter(
            Q(username__icontains=q) | Q(email__icontains=q) | Q(profile__poste__icontains=q)
        )

    # Filtrer par poste (si fourni)
    if poste:
        employees = employees.filter(profile__poste__icontains=poste)

    # Filtrer par statut actif (attendu '1' pour actif, '0' pour inactif)
    if is_active == '1':
        employees = employees.filter(is_active=True)
    elif is_active == '0':
        employees = employees.filter(is_active=False)

    # s'assurer que chaque employé a un profil associé
    for u in employees:
        UserProfile.objects.get_or_create(user=u)
    # Construire la liste des postes disponibles (issus des profils existants)
    from .constants import STANDARD_POSITIONS
    postes_qs = UserProfile.objects.exclude(poste__isnull=True).exclude(poste__exact='').values_list('poste', flat=True).distinct()
    postes_set = set([p for p in postes_qs if p]) | set(STANDARD_POSITIONS)
    postes_choices = sorted(postes_set)

    # Passer les valeurs GET au template pour préserver l'état du formulaire
    context = {
        'employees': employees,
        'q': q,
        'poste_filter': poste,
        'is_active_filter': is_active,
        'postes_choices': postes_choices,
    }
    return render(request, 'hotel/employee_list.html', context)


@admin_required
def employee_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    # Récupérer ou créer le profil étendu
    from .models import UserProfile, EmployeeHistory
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        is_active = bool(request.POST.get('is_active'))
        is_staff = bool(request.POST.get('is_staff'))
        password = request.POST.get('password')
        # champs employé
        poste = request.POST.get('poste')
        salaire = request.POST.get('salaire')
        date_embauche = request.POST.get('date_embauche')
        statut_employe = request.POST.get('statut_employe')

        if username:
            user.username = username
        user.email = email
        user.is_active = is_active
        user.is_staff = is_staff
        if password:
            user.password = make_password(password)
        user.save()
        # Mettre à jour le profil employé et historiser les changements
        changed = False
        if poste != (profile.poste or ''):
            EmployeeHistory.objects.create(user=user, action='Changement de poste', field_changed='poste', old_value=profile.poste or '', new_value=poste or '')
            profile.poste = poste
            changed = True
        # salaire
        old_salaire = str(profile.salaire) if profile.salaire is not None else ''
        if salaire:
            try:
                s_val = float(salaire)
            except Exception:
                s_val = None
        else:
            s_val = None
        new_salaire_str = str(s_val) if s_val is not None else ''
        if new_salaire_str != old_salaire:
            EmployeeHistory.objects.create(user=user, action='Changement de salaire', field_changed='salaire', old_value=old_salaire, new_value=new_salaire_str)
            profile.salaire = s_val
            changed = True
        # date embauche
        old_date_emb = profile.date_embauche.isoformat() if profile.date_embauche else ''
        new_date = parse_date(date_embauche) if date_embauche else None
        if (new_date and new_date.isoformat()) != old_date_emb:
            EmployeeHistory.objects.create(user=user, action='Mise à jour date embauche', field_changed='date_embauche', old_value=old_date_emb, new_value=new_date.isoformat() if new_date else '')
            profile.date_embauche = new_date
            changed = True
        # statut
        if statut_employe and statut_employe != profile.statut_employe:
            EmployeeHistory.objects.create(user=user, action='Changement de statut', field_changed='statut_employe', old_value=profile.statut_employe, new_value=statut_employe)
            profile.statut_employe = statut_employe
            changed = True
        if changed:
            profile.save()
        messages.success(request, f"Profil employé '{user.username}' mis à jour.")
        return redirect('employee_list')

    return render(request, 'hotel/employee_form.html', {'employee': user})


@admin_required
def employee_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f"Employé '{username}' supprimé.")
        return redirect('employee_list')
    return render(request, 'hotel/employee_confirm_delete.html', {'employee': user})


@admin_required
def employee_promote(request, pk):
    """Promouvoir / changer le poste d'un employé"""
    user = get_object_or_404(User, pk=pk)
    from .models import UserProfile, EmployeeHistory
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        new_poste = request.POST.get('poste')
        note = request.POST.get('note')
        old = profile.poste or ''
        profile.poste = new_poste
        profile.save()
        EmployeeHistory.objects.create(user=user, action='Promotion / changement poste', field_changed='poste', old_value=old, new_value=new_poste or '', note=note)
        messages.success(request, f"Poste mis à jour pour {user.username} → {new_poste}")
        return redirect('employee_list')
    return render(request, 'hotel/employee_promote.html', {'employee': user, 'profile': profile})


@admin_required
def employee_change_salary(request, pk):
    """Changer le salaire d'un employé"""
    user = get_object_or_404(User, pk=pk)
    from .models import UserProfile, EmployeeHistory
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        new_salary = request.POST.get('salaire')
        note = request.POST.get('note')
        old = str(profile.salaire) if profile.salaire is not None else ''
        try:
            s_val = float(new_salary) if new_salary else None
        except Exception:
            s_val = None
        profile.salaire = s_val
        profile.save()
        EmployeeHistory.objects.create(user=user, action='Changement de salaire', field_changed='salaire', old_value=old, new_value=str(s_val) if s_val is not None else '', note=note)
        messages.success(request, f"Salaire mis à jour pour {user.username} → {profile.salaire}")
        return redirect('employee_list')
    return render(request, 'hotel/employee_change_salary.html', {'employee': user, 'profile': profile})


@admin_required
def employee_change_role(request, pk):
    """Changer le rôle (is_staff / is_superuser) d'un employé"""
    user = get_object_or_404(User, pk=pk)
    from .models import EmployeeHistory
    if request.method == 'POST':
        is_staff = bool(request.POST.get('is_staff'))
        is_superuser = bool(request.POST.get('is_superuser'))
        old = f"staff={user.is_staff}, super={user.is_superuser}"
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
        new = f"staff={user.is_staff}, super={user.is_superuser}"
        EmployeeHistory.objects.create(user=user, action='Changement de rôle', field_changed='role', old_value=old, new_value=new)
        messages.success(request, f"Rôle mis à jour pour {user.username}")
        return redirect('employee_list')
    return render(request, 'hotel/employee_change_role.html', {'employee': user})


@admin_required
def employee_terminate(request, pk):
    """Licencier / désactiver un employé"""
    user = get_object_or_404(User, pk=pk)
    from .models import UserProfile, EmployeeHistory
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        profile.statut_employe = 'renvoye'
        profile.save()
        user.is_active = False
        user.save()
        EmployeeHistory.objects.create(user=user, action='Licenciement', note=reason, old_value=profile.poste or '', new_value='renvoye')
        messages.success(request, f"Employé {user.username} renvoyé et désactivé.")
        return redirect('employee_list')
    return render(request, 'hotel/employee_terminate.html', {'employee': user, 'profile': profile})


@admin_required
def employee_history(request, pk):
    """Afficher l'historique des actions pour un employé"""
    user = get_object_or_404(User, pk=pk)
    from .models import EmployeeHistory
    history = EmployeeHistory.objects.filter(user=user).order_by('-created_at')
    return render(request, 'hotel/employee_history.html', {'employee': user, 'history': history})


# ============================================
# TABLEAU DE BORD (DASHBOARD)
# ============================================

@login_required
def dashboard(request):
    """
    Vue du tableau de bord principal
    Affiche les statistiques et informations importantes
    """
    # Compter les statistiques
    total_clients = Client.objects.count()
    total_chambres = Chambre.objects.count()
    total_reservations = Reservation.objects.count()
    
    # Chambres par statut
    chambres_libres = Chambre.objects.filter(statut='libre').count()
    chambres_occupees = Chambre.objects.filter(statut='occupee').count()
    
    # Réservations récentes (les 5 dernières)
    reservations_recentes = Reservation.objects.select_related('client', 'chambre').order_by('-date_creation')[:5]
    
    # Réservations actives (confirmées ou en cours)
    reservations_actives = Reservation.objects.filter(
        statut__in=['confirmee', 'en_cours']
    ).count()
    
    # Revenus du mois en cours
    from django.db.models import Sum
    today = timezone.now().date()
    revenus_mois = Reservation.objects.filter(
        date_entree__year=today.year,
        date_entree__month=today.month,
        statut__in=['confirmee', 'en_cours', 'terminee']
    ).aggregate(total=Sum('prix_total'))['total'] or 0
    
    context = {
        'total_clients': total_clients,
        'total_chambres': total_chambres,
        'total_reservations': total_reservations,
        'chambres_libres': chambres_libres,
        'chambres_occupees': chambres_occupees,
        'reservations_recentes': reservations_recentes,
        'reservations_actives': reservations_actives,
        'revenus_mois': revenus_mois,
    }
    
    return render(request, 'hotel/dashboard.html', context)


# ============================================
# DASHBOARDS PAR RÔLE
# ============================================

@admin_required
def dashboard_admin(request):
    """
    Dashboard réservé aux ADMINISTRATEURS
    Accès complet à toutes les statistiques et données
    """
    from django.db.models import Sum
    today = timezone.now().date()
    
    # Statistiques complètes
    total_clients = Client.objects.count()
    total_chambres = Chambre.objects.count()
    total_reservations = Reservation.objects.count()
    
    # Chambres par statut
    chambres_libres = Chambre.objects.filter(statut='libre').count()
    chambres_occupees = Chambre.objects.filter(statut='occupee').count()
    chambres_maintenance = Chambre.objects.filter(statut='maintenance').count()
    
    # Réservations par statut
    reservations_confirmees = Reservation.objects.filter(statut='confirmee').count()
    reservations_en_cours = Reservation.objects.filter(statut='en_cours').count()
    reservations_en_attente = Reservation.objects.filter(statut='en_attente').count()
    
    # Réservations récentes (les 10 dernières pour l'admin)
    reservations_recentes = Reservation.objects.select_related('client', 'chambre').order_by('-date_creation')[:10]
    
    # Revenus
    revenus_mois = Reservation.objects.filter(
        date_entree__year=today.year,
        date_entree__month=today.month,
        statut__in=['confirmee', 'en_cours', 'terminee']
    ).aggregate(total=Sum('prix_total'))['total'] or 0
    
    revenus_total = Reservation.objects.filter(
        statut__in=['confirmee', 'en_cours', 'terminee']
    ).aggregate(total=Sum('prix_total'))['total'] or 0
    
    context = {
        'total_clients': total_clients,
        'total_chambres': total_chambres,
        'total_reservations': total_reservations,
        'chambres_libres': chambres_libres,
        'chambres_occupees': chambres_occupees,
        'chambres_maintenance': chambres_maintenance,
        'reservations_confirmees': reservations_confirmees,
        'reservations_en_cours': reservations_en_cours,
        'reservations_en_attente': reservations_en_attente,
        'reservations_recentes': reservations_recentes,
        'revenus_mois': revenus_mois,
        'revenus_total': revenus_total,
    }
    
    return render(request, 'hotel/admin/dashboard.html', context)


@employe_required
def dashboard_employe(request):
    """
    Dashboard réservé aux EMPLOYÉS
    Affichage personnalisé selon le poste de l'employé
    """
    try:
        from django.db.models import Sum, Count, Q
        today = timezone.now().date()
        
        # Récupérer le profil et le poste de l'employé
        user_profile = request.user.profile
        poste = user_profile.poste or 'receptionniste'  # Par défaut
        
        print(f'Debug: User {request.user.username}, Poste: {poste}')  # Debug
        
        # Statistiques personnalisées selon le poste
        stats_config = user_profile.get_dashboard_stats_config()
        stats_data = {}
        
        print(f'Debug: Stats config: {len(stats_config)} stats')  # Debug
        
        # Calculer les statistiques selon la configuration
        for stat in stats_config:
            stat_name = stat['name']
            
            if stat_name == 'reservations_today':
                stats_data[stat_name] = Reservation.objects.filter(
                    date_entree=today
                ).count()
                
            elif stat_name == 'arrivals_today':
                stats_data[stat_name] = Reservation.objects.filter(
                    date_entree=today
                ).count()
                
            elif stat_name == 'departures_today':
                stats_data[stat_name] = Reservation.objects.filter(
                    date_sortie=today
                ).count()
                
            elif stat_name == 'rooms_available':
                stats_data[stat_name] = Chambre.objects.filter(statut='libre').count()
                
            elif stat_name == 'pending_checkins':
                stats_data[stat_name] = Reservation.objects.filter(
                    date_entree=today,
                    statut='confirmee'
                ).count()
                
            elif stat_name == 'new_clients_today':
                stats_data[stat_name] = Client.objects.filter(
                    date_inscription__date=today
                ).count()
                
            elif stat_name == 'active_reservations':
                stats_data[stat_name] = Reservation.objects.filter(
                    statut__in=['confirmee', 'en_cours']
                ).count()
                
            elif stat_name == 'services_requested':
                # À implémenter avec les services
                stats_data[stat_name] = 0
                
            elif stat_name == 'guest_messages':
                # À implémenter avec les messages
                stats_data[stat_name] = 0
                
            elif stat_name == 'rooms_to_clean':
                stats_data[stat_name] = Chambre.objects.filter(
                    statut='nettoyage_requis'
                ).count()
                
            elif stat_name == 'rooms_cleaned_today':
                stats_data[stat_name] = Chambre.objects.filter(
                    statut='libre',
                    derniere_modification__date=today
                ).count()
                
            elif stat_name == 'maintenance_requests':
                # À implémenter avec les demandes de maintenance
                stats_data[stat_name] = 0
                
            elif stat_name == 'orders_today':
                # À implémenter avec les commandes restaurant
                stats_data[stat_name] = 0
                
            elif stat_name == 'occupancy_rate':
                total_rooms = Chambre.objects.count()
                occupied_rooms = Chambre.objects.filter(statut='occupee').count()
                stats_data[stat_name] = round((occupied_rooms / total_rooms * 100), 1) if total_rooms > 0 else 0
                
            elif stat_name == 'revenue_month':
                stats_data[stat_name] = Reservation.objects.filter(
                    date_entree__year=today.year,
                    date_entree__month=today.month,
                    statut__in=['confirmee', 'en_cours', 'terminee']
                ).aggregate(total=Sum('prix_total'))['total'] or 0
                
            elif stat_name == 'staff_count':
                stats_data[stat_name] = UserProfile.objects.filter(
                    statut_employe='actif'
                ).count()
                
            else:
                stats_data[stat_name] = 0  # Valeur par défaut
        
        # Modules accessibles pour cet employé
        accessible_modules = user_profile.get_accessible_modules()
        
        print(f'Debug: Accessible modules: {len(accessible_modules)} modules')  # Debug
        
        # Données communes
        reservations_actives = Reservation.objects.filter(
            statut__in=['confirmee', 'en_cours']
        ).select_related('client', 'chambre').order_by('date_entree')[:8]
        
        reservations_en_attente = Reservation.objects.filter(
            statut='en_attente'
        ).select_related('client', 'chambre')[:5]
        
        context = {
            'poste': poste,
            'poste_display': user_profile.get_poste_display(),
            'stats_config': stats_config,
            'stats_data': stats_data,
            'accessible_modules': accessible_modules,
            'reservations_actives': reservations_actives,
            'reservations_en_attente': reservations_en_attente,
            'user_permissions': get_user_permissions(request.user),
        }
        
        print('Debug: Context prepared successfully')  # Debug
        return render(request, 'hotel/employe/dashboard.html', context)
        
    except Exception as e:
        import traceback
        print(f'Error in dashboard_employe: {str(e)}')
        print(traceback.format_exc())
        raise


@client_required
def dashboard_client(request):
    """
    Dashboard réservé aux CLIENTS
    Affiche uniquement les informations personnelles du client
    """
    # Récupérer le profil client de l'utilisateur connecté
    try:
        user_profile = request.user.profile
        client = user_profile.client
        print(f"Client trouvé: {client} - User: {request.user}")
    except Exception as e:
        print(f"Erreur profil client: {e}")
        client = None
    
    # Réservations du client (uniquement les siennes)
    if client:
        try:
            mes_reservations = Reservation.objects.filter(
                client=client
            ).select_related('chambre').order_by('-date_creation')
            
            print(f"Réservations trouvées pour {client}: {mes_reservations.count()}")
            
            # Réservations actives (élargi pour inclure plus de statuts)
            reservations_actives = mes_reservations.filter(
                statut__in=['confirmee', 'en_cours', 'en_attente']
            )
            
            print(f"Réservations actives: {reservations_actives.count()}")
            
            # Réservations passées
            reservations_passees = mes_reservations.filter(
                statut='terminee'
            )[:5]
            
            # Debug: afficher les réservations
            for res in reservations_actives:
                print(f"  - Réservation {res.id}: Chambre {res.chambre.numero} - Statut {res.statut}")
                
        except Exception as e:
            print(f"Erreur réservations: {e}")
            mes_reservations = Reservation.objects.none()
            reservations_actives = Reservation.objects.none()
            reservations_passees = Reservation.objects.none()
    else:
        print("Aucun client trouvé pour cet utilisateur")
        mes_reservations = Reservation.objects.none()
        reservations_actives = Reservation.objects.none()
        reservations_passees = Reservation.objects.none()
    
    # Chambres disponibles (pour consultation)
    try:
        chambres_disponibles = Chambre.objects.filter(statut='libre')[:6]
    except Exception as e:
        print(f"Erreur chambres: {e}")
        chambres_disponibles = Chambre.objects.none()
    
    # Calculer les totaux de manière sécurisée
    try:
        total_reservations = mes_reservations.count()
        total_depenses = sum(r.prix_total for r in reservations_actives if r.prix_total)
        prochaine_arrivee = reservations_actives.first().date_entree if reservations_actives.exists() else None
    except Exception as e:
        print(f"Erreur calculs: {e}")
        total_reservations = 0
        total_depenses = 0
        prochaine_arrivee = None
    
    context = {
        'client': client,
        'mes_reservations': mes_reservations,
        'reservations_actives': reservations_actives,
        'reservations_passees': reservations_passees,
        'chambres_disponibles': chambres_disponibles,
        'total_reservations': total_reservations,
        'total_depenses': total_depenses,
        'prochaine_arrivee': prochaine_arrivee,
        'debug_info': {
            'user_id': request.user.id,
            'username': request.user.username,
            'client_id': client.id if client else None,
            'client_name': client.nom_complet if client else None,
            'total_reservations_debug': total_reservations,
            'active_reservations_debug': reservations_actives.count(),
        }
    }
    
    print(f"Contexte envoyé au template: {context['debug_info']}")
    
    return render(request, 'hotel/client/dashboard.html', context)


@client_required
def create_test_reservation(request):
    """
    Vue temporaire pour créer une réservation de test
    """
    try:
        # Récupérer le client connecté
        user_profile = request.user.profile
        client = user_profile.client
        
        # Récupérer une chambre disponible
        chambre = Chambre.objects.filter(statut='libre').first()
        
        if not chambre:
            messages.error(request, "Aucune chambre disponible pour créer une réservation de test.")
            return redirect('client_dashboard')
        
        # Créer une réservation de test
        from datetime import datetime, timedelta
        date_entree = timezone.now().date() + timedelta(days=1)
        date_sortie = date_entree + timedelta(days=3)
        
        reservation = Reservation.objects.create(
            client=client,
            chambre=chambre,
            date_entree=date_entree,
            date_sortie=date_sortie,
            nombre_personnes=2,
            statut='confirmee',
            prix_total=chambre.prix_par_nuit * 3,
            remarques="Réservation de test créée automatiquement"
        )
        
        messages.success(request, f"Réservation de test créée avec succès ! Chambre {chambre.numero} du {date_entree} au {date_sortie}")
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la création de la réservation de test: {e}")
    
    return redirect('client_dashboard')


# ============================================
# GESTION DES CLIENTS
# ============================================

@role_required('admin', 'employe')
def client_list(request):
    """
    Vue pour afficher la liste de tous les clients
    Accessible par : Admin et Employé
    """
    # Récupérer tous les clients
    clients = Client.objects.all()
    
    # Recherche (optionnelle)
    search_query = request.GET.get('search', '')
    if search_query:
        clients = clients.filter(
            Q(nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(telephone__icontains=search_query)
        )
    
    context = {
        'clients': clients,
        'search_query': search_query,
        'user_permissions': get_user_permissions(request.user),
    }
    
    # Choisir le template selon le rôle
    if request.user.is_staff and not request.user.is_superuser:
        # Employé -> template employé
        return render(request, 'hotel/employe/client_list.html', context)
    else:
        # Admin -> template admin
        return render(request, 'hotel/client_list.html', context)


@role_required('admin', 'employe')
def client_create(request):
    """
    Vue pour créer un nouveau client
    """
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        numero_piece_identite = request.POST.get('numero_piece_identite')
        adresse = request.POST.get('adresse')
        ville = request.POST.get('ville')
        pays = request.POST.get('pays')
        # Optional account creation
        create_account = bool(request.POST.get('create_account'))
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Créer le nouveau client
            client = Client.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                numero_piece_identite=numero_piece_identite,
                adresse=adresse,
                ville=ville,
                pays=pays
            )

            # Si demandé, créer le compte utilisateur lié
            if create_account and username and password:
                from django.contrib.auth.models import User
                from .models import UserProfile

                if User.objects.filter(username=username).exists():
                    messages.error(request, f"Le nom d'utilisateur '{username}' est déjà utilisé.")
                    client.delete()
                    return redirect('client_create')

                user = User.objects.create_user(username=username, password=password, email=email)
                user.is_staff = False
                user.save()

                # Lier le profil utilisateur au client
                UserProfile.objects.create(user=user, client=client)

            messages.success(request, f'Client {client.nom_complet} créé avec succès !')
            return redirect('client_list')

        except Exception as e:
            messages.error(request, f'Erreur lors de la création du client : {str(e)}')
    
    return render(request, 'hotel/client_form.html', {'action': 'Créer'})


@role_required('admin', 'employe')
def client_update(request, pk):
    """
    Vue pour modifier un client existant
    Accessible par : Admin et Employé
    """
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        # Mettre à jour les données
        client.nom = request.POST.get('nom')
        client.prenom = request.POST.get('prenom')
        client.email = request.POST.get('email')
        client.telephone = request.POST.get('telephone')
        client.numero_piece_identite = request.POST.get('numero_piece_identite')
        client.adresse = request.POST.get('adresse')
        client.ville = request.POST.get('ville')
        client.pays = request.POST.get('pays')
        
        try:
            client.save()
            messages.success(request, f'Client {client.nom_complet} modifié avec succès !')
            return redirect('client_list')
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    context = {
        'client': client,
        'action': 'Modifier'
    }
    
    return render(request, 'hotel/client_form.html', context)


@admin_required
def client_delete(request, pk):
    """
    Vue pour supprimer un client
    Accessible par : Admin UNIQUEMENT
    """
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        nom_complet = client.nom_complet
        client.delete()
        messages.success(request, f'Client {nom_complet} supprimé avec succès !')
        return redirect('client_list')
    
    context = {'client': client}
    return render(request, 'hotel/client_confirm_delete.html', context)


@admin_required
def client_change_password(request, pk):
    """Permettre à l'admin de réinitialiser/changer le mot de passe d'un client"""
    client = get_object_or_404(Client, pk=pk)

    # tenter de récupérer l'utilisateur lié via UserProfile
    user = None
    try:
        user = client.user_profile.user
    except Exception:
        user = None

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not user:
            messages.error(request, 'Aucun utilisateur lié à ce client.')
            return redirect('client_list')
        if not new_password:
            messages.error(request, 'Le mot de passe ne peut pas être vide.')
        elif new_password != confirm_password:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, f"Mot de passe mis à jour pour {client.nom_complet} (utilisateur: {user.username}).")
            return redirect('client_list')

    return render(request, 'hotel/client_change_password.html', {'client': client, 'user': user})


# ============================================
# GESTION DES CHAMBRES
# ============================================

@role_required('admin', 'employe')
def chambre_list(request):
    """
    Vue pour afficher la liste de toutes les chambres
    Accessible par : Admin et Employé
    """
    # Récupérer toutes les chambres
    chambres = Chambre.objects.all()
    
    # Filtrage par type (optionnel)
    type_filter = request.GET.get('type', '')
    if type_filter:
        chambres = chambres.filter(type_chambre=type_filter)
    
    # Filtrage par statut (optionnel)
    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        chambres = chambres.filter(statut=statut_filter)
    
    context = {
        'chambres': chambres,
        'type_filter': type_filter,
        'statut_filter': statut_filter,
        'types': Chambre.TYPE_CHOICES,
        'statuts': Chambre.STATUT_CHOICES,
        'user_permissions': get_user_permissions(request.user),
    }
    
    # Choisir le template selon le rôle
    if request.user.is_staff and not request.user.is_superuser:
        # Employé -> template employé
        return render(request, 'hotel/employe/chambre_list.html', context)
    else:
        # Admin -> template admin
        return render(request, 'hotel/chambre_list.html', context)


@admin_required
def chambre_create(request):
    """
    Vue pour créer une nouvelle chambre
    Accessible par : Admin UNIQUEMENT
    """
    if request.method == 'POST':
        # Récupérer les données du formulaire
        numero = request.POST.get('numero')
        type_chambre = request.POST.get('type_chambre')
        prix_par_nuit = request.POST.get('prix_par_nuit')
        capacite = request.POST.get('capacite')
        statut = request.POST.get('statut', 'libre')
        description = request.POST.get('description', '')
        
        # Équipements (checkboxes)
        climatisation = request.POST.get('climatisation') == 'on'
        wifi = request.POST.get('wifi') == 'on'
        television = request.POST.get('television') == 'on'
        minibar = request.POST.get('minibar') == 'on'
        
        try:
            # Créer la nouvelle chambre
            chambre = Chambre.objects.create(
                numero=numero,
                type_chambre=type_chambre,
                prix_par_nuit=prix_par_nuit,
                capacite=capacite,
                statut=statut,
                description=description,
                climatisation=climatisation,
                wifi=wifi,
                television=television,
                minibar=minibar
            )

            # gérer les images uploadées (plusieurs)
            images = request.FILES.getlist('images') if hasattr(request, 'FILES') else []
            if images:
                from .models import ChambreImage
                for img in images:
                    ChambreImage.objects.create(chambre=chambre, image=img)
            
            messages.success(request, f'Chambre {chambre.numero} créée avec succès !')
            return redirect('chambre_list')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création de la chambre : {str(e)}')
    
    context = {
        'action': 'Créer',
        'types': Chambre.TYPE_CHOICES,
        'statuts': Chambre.STATUT_CHOICES,
    }
    
    return render(request, 'hotel/chambre_form.html', context)


@admin_required
def chambre_update(request, pk):
    """
    Vue pour modifier une chambre existante
    Accessible par : Admin UNIQUEMENT
    """
    chambre = get_object_or_404(Chambre, pk=pk)
    
    if request.method == 'POST':
        # Mettre à jour les données
        chambre.numero = request.POST.get('numero')
        chambre.type_chambre = request.POST.get('type_chambre')
        chambre.prix_par_nuit = request.POST.get('prix_par_nuit')
        chambre.capacite = request.POST.get('capacite')
        chambre.statut = request.POST.get('statut')
        chambre.description = request.POST.get('description', '')
        
        # Équipements
        chambre.climatisation = request.POST.get('climatisation') == 'on'
        chambre.wifi = request.POST.get('wifi') == 'on'
        chambre.television = request.POST.get('television') == 'on'
        chambre.minibar = request.POST.get('minibar') == 'on'
        
        try:
            chambre.save()

            # suppression d'images sélectionnées
            from .models import ChambreImage
            for img in chambre.images.all():
                if request.POST.get(f'delete_image_{img.id}'):
                    img.delete()

            # nouveaux fichiers uploadés
            new_images = request.FILES.getlist('images') if hasattr(request, 'FILES') else []
            for f in new_images:
                ChambreImage.objects.create(chambre=chambre, image=f)

            messages.success(request, f'Chambre {chambre.numero} modifiée avec succès !')
            return redirect('chambre_list')
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    context = {
        'chambre': chambre,
        'action': 'Modifier',
        'types': Chambre.TYPE_CHOICES,
        'statuts': Chambre.STATUT_CHOICES,
    }
    
    return render(request, 'hotel/chambre_form.html', context)


@admin_required
def chambre_delete(request, pk):
    """
    Vue pour supprimer une chambre
    Accessible par : Admin UNIQUEMENT
    """
    chambre = get_object_or_404(Chambre, pk=pk)
    
    if request.method == 'POST':
        numero = chambre.numero
        chambre.delete()
        messages.success(request, f'Chambre {numero} supprimée avec succès !')
        return redirect('chambre_list')
    
    context = {'chambre': chambre}
    return render(request, 'hotel/chambre_confirm_delete.html', context)


# ============================================
# GESTION DES RÉSERVATIONS
# ============================================

@role_required('admin', 'employe')
def reservation_list(request):
    """
    Vue pour afficher la liste de toutes les réservations
    Accessible par : Admin et Employé
    """
    # Récupérer toutes les réservations
    reservations = Reservation.objects.select_related('client', 'chambre').all()
    
    # Filtrage par statut (optionnel)
    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        reservations = reservations.filter(statut=statut_filter)
    
    context = {
        'reservations': reservations,
        'statut_filter': statut_filter,
        'statuts': Reservation.STATUT_CHOICES,
        'user_permissions': get_user_permissions(request.user),
    }
    
    # Choisir le template selon le rôle
    if request.user.is_staff and not request.user.is_superuser:
        # Employé -> template employé
        return render(request, 'hotel/employe/reservation_list.html', context)
    else:
        # Admin -> template admin
        return render(request, 'hotel/reservation_list.html', context)


@role_required('admin', 'employe')
def reservation_detail(request, pk):
    """Affiche les détails d'une réservation"""
    reservation = get_object_or_404(Reservation.objects.select_related('client','chambre'), pk=pk)
    return render(request, 'hotel/reservation_detail.html', {'reservation': reservation})


@role_required('admin', 'employe')
def reservation_create(request):
    """
    Vue pour créer une nouvelle réservation
    Accessible par : Admin et Employé
    """
    if request.method == 'POST':
        # Récupérer les données du formulaire
        client_id = request.POST.get('client')
        chambre_id = request.POST.get('chambre')
        date_entree = request.POST.get('date_entree')
        date_sortie = request.POST.get('date_sortie')
        nombre_personnes = request.POST.get('nombre_personnes')
        statut = request.POST.get('statut', 'en_attente')
        remarques = request.POST.get('remarques', '')
        
        try:
            # Récupérer les objets
            client = Client.objects.get(pk=client_id)
            chambre = Chambre.objects.get(pk=chambre_id)
            
            # Vérifier la disponibilité de la chambre
            date_entree_obj = datetime.strptime(date_entree, '%Y-%m-%d').date()
            date_sortie_obj = datetime.strptime(date_sortie, '%Y-%m-%d').date()
            
            # Vérifier s'il y a des réservations qui se chevauchent
            reservations_chevauchees = Reservation.objects.filter(
                chambre=chambre,
                statut__in=['confirmee', 'en_cours'],
                date_entree__lt=date_sortie_obj,
                date_sortie__gt=date_entree_obj
            )
            
            if reservations_chevauchees.exists():
                messages.error(request, 'Cette chambre n\'est pas disponible pour ces dates.')
                # Rediriger vers le formulaire avec les données
                context = {
                    'clients': Client.objects.all(),
                    'chambres': Chambre.objects.filter(statut='libre'),
                    'statuts': Reservation.STATUT_CHOICES,
                    'error': True
                }
                return render(request, 'hotel/reservation_form.html', context)
            
            # Créer la réservation
            reservation = Reservation(
                client=client,
                chambre=chambre,
                date_entree=date_entree_obj,
                date_sortie=date_sortie_obj,
                nombre_personnes=nombre_personnes,
                statut=statut,
                remarques=remarques,
                cree_par=request.user
            )
            
            # La validation et le calcul automatique se font dans le save()
            reservation.save()
            
            # Mettre à jour le statut de la chambre si nécessaire
            if statut in ['confirmee', 'en_cours']:
                chambre.statut = 'occupee'
                chambre.save()
            
            messages.success(request, f'Réservation créée avec succès ! Prix total : {reservation.prix_total}€')
            return redirect('reservation_list')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création de la réservation : {str(e)}')
    
    # Préparer les données pour le formulaire
    context = {
        'clients': Client.objects.all(),
        'chambres': Chambre.objects.filter(statut='libre'),
        'statuts': Reservation.STATUT_CHOICES,
        'action': 'Créer'
    }
    
    return render(request, 'hotel/reservation_form.html', context)


@role_required('admin', 'employe')
def reservation_update(request, pk):
    """
    Vue pour modifier une réservation existante
    Accessible par : Admin et Employé
    """
    reservation = get_object_or_404(Reservation, pk=pk)
    
    if request.method == 'POST':
        # Récupérer les nouvelles données
        date_entree = request.POST.get('date_entree')
        date_sortie = request.POST.get('date_sortie')
        nombre_personnes = request.POST.get('nombre_personnes')
        statut = request.POST.get('statut')
        remarques = request.POST.get('remarques', '')
        
        try:
            # Mettre à jour les dates
            reservation.date_entree = datetime.strptime(date_entree, '%Y-%m-%d').date()
            reservation.date_sortie = datetime.strptime(date_sortie, '%Y-%m-%d').date()
            reservation.nombre_personnes = nombre_personnes
            reservation.statut = statut
            reservation.remarques = remarques
            
            reservation.save()
            
            # Mettre à jour le statut de la chambre
            if statut in ['confirmee', 'en_cours']:
                reservation.chambre.statut = 'occupee'
            elif statut in ['terminee', 'annulee']:
                reservation.chambre.statut = 'libre'
            reservation.chambre.save()
            
            messages.success(request, 'Réservation modifiée avec succès !')
            return redirect('reservation_list')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    context = {
        'reservation': reservation,
        'statuts': Reservation.STATUT_CHOICES,
        'action': 'Modifier'
    }
    
    return render(request, 'hotel/reservation_form.html', context)


@admin_required
def reservation_delete(request, pk):
    """
    Vue pour supprimer une réservation
    Accessible par : Admin UNIQUEMENT
    """
    reservation = get_object_or_404(Reservation, pk=pk)
    
    if request.method == 'POST':
        # Libérer la chambre
        chambre = reservation.chambre
        chambre.statut = 'libre'
        chambre.save()
        
        reservation.delete()
        messages.success(request, 'Réservation supprimée avec succès !')
        return redirect('reservation_list')
    
    context = {'reservation': reservation}
    return render(request, 'hotel/reservation_confirm_delete.html', context)


# ============================================
# API POUR LE CHATBOT IA
# ============================================

@login_required
def chatbot_api(request):
    """
    API pour le chatbot IA intelligent
    Répond aux questions des utilisateurs de manière contextuelle
    en tenant compte de leur rôle et de la page actuelle
    """
    if request.method == 'POST':
        import json
        from .chatbot_ai import HotelChatbot
        
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            page_context = data.get('page_context', '')  # ex: 'dashboard', 'chambres', 'reservations'
            
            # Créer une instance du chatbot intelligent
            chatbot = HotelChatbot(request.user)
            
            # Générer la réponse en tenant compte du contexte
            response_message = chatbot.process_message(message, page_context)
            
            response = {
                'success': True,
                'message': response_message
            }
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Erreur: Format de données invalide'
            })
        except Exception as e:
            # Log l'erreur en production
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur chatbot: {str(e)}")
            
            return JsonResponse({
                'success': False,
                'message': 'Désolé, une erreur est survenue. Veuillez réessayer.'
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


# ============================================
# VUES POUR LES PAGES CLIENT SPÉCIFIQUES
# ============================================

@client_required
def chambres_client(request):
    """
    Page des chambres pour les clients
    Affiche les chambres disponibles de manière conviviale
    """
    from .utils import get_chambres_avec_statut_reel
    
    # Récupérer le profil client
    try:
        user_profile = request.user.profile
        client = user_profile.client
    except:
        client = None
    
    # Récupérer toutes les chambres avec leur statut réel
    chambres_info = get_chambres_avec_statut_reel()
    
    # Ajouter les images pour chaque chambre
    for item in chambres_info:
        chambre = item['chambre']
        
        # Récupérer d'abord les images réelles de la chambre
        images_reelles = chambre.images.all()
        if images_reelles.exists():
            # Utiliser la première image réelle disponible
            item['image_url'] = images_reelles.first().image.url
        else:
            # Ajouter une URL d'image par défaut selon le type de chambre (Unsplash - haute qualité)
            if chambre.type_chambre == 'simple':
                item['image_url'] = 'https://images.unsplash.com/photo-1590490360232-c714e3fd8a80?w=600&h=400&fit=crop&auto=format'
            elif chambre.type_chambre == 'double':
                item['image_url'] = 'https://images.unsplash.com/photo-1566679076615-5eea8f2c5c46?w=600&h=400&fit=crop&auto=format'
            elif chambre.type_chambre == 'suite':
                item['image_url'] = 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600&h=400&fit=crop&auto=format'
            else:
                # Image par défaut générique
                item['image_url'] = 'https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=600&h=400&fit=crop&auto=format'
    
    # Filtrage par type si demandé
    type_filtre = request.GET.get('type')
    if type_filtre:
        chambres_info = [item for item in chambres_info if item['chambre'].type_chambre == type_filtre]
    
    # Filtrage par prix si demandé
    prix_max = request.GET.get('prix_max')
    if prix_max:
        try:
            prix_max_float = float(prix_max)
            chambres_info = [item for item in chambres_info if item['chambre'].prix_par_nuit <= prix_max_float]
        except ValueError:
            pass
    
    # Filtrage par disponibilité
    disponible_filtre = request.GET.get('disponible')
    if disponible_filtre == 'oui':
        chambres_info = [item for item in chambres_info if item['disponible_maintenant']]
    elif disponible_filtre == 'non':
        chambres_info = [item for item in chambres_info if not item['disponible_maintenant']]
    
    # Filtrage par statut
    statut_filtre = request.GET.get('statut')
    if statut_filtre:
        chambres_info = [item for item in chambres_info if item['statut_reel'] == statut_filtre]
    
    context = {
        'client': client,
        'chambres': chambres_info,
        'types_chambre': Chambre.TYPE_CHOICES,
        'statuts_chambre': Chambre.STATUT_CHOICES,
        'type_filtre': type_filtre,
        'prix_max': prix_max,
        'disponible_filtre': disponible_filtre,
        'statut_filtre': statut_filtre,
    }
    
    return render(request, 'hotel/client/chambre_client.html', context)


@client_required
def reservation_client(request):
    """
    Page de réservation pour les clients
    Formulaire simplifié pour faire une réservation
    """
    # Récupérer le profil client
    try:
        user_profile = request.user.profile
        client = user_profile.client
    except:
        client = None
    
    # Récupérer la chambre pré-sélectionnée depuis l'URL
    chambre_preselectionnee_id = request.GET.get('chambre_id')
    chambre_preselectionnee = None
    
    if chambre_preselectionnee_id:
        try:
            chambre_preselectionnee = Chambre.objects.get(pk=chambre_preselectionnee_id)
        except Chambre.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        chambre_id = request.POST.get('chambre_id')
        date_entree = request.POST.get('date_entree')
        date_sortie = request.POST.get('date_sortie')
        nombre_personnes = request.POST.get('nombre_personnes')
        remarques = request.POST.get('remarques', '')
        
        try:
            if not client:
                messages.error(request, 'Profil client introuvable. Veuillez compléter votre profil.')
                return redirect('client_reservation')
            
            # Récupérer la chambre
            chambre = Chambre.objects.get(pk=chambre_id)
            
            # Vérifier la disponibilité
            date_entree_obj = datetime.strptime(date_entree, '%Y-%m-%d').date()
            date_sortie_obj = datetime.strptime(date_sortie, '%Y-%m-%d').date()
            
            # Validation des dates
            if date_entree_obj >= date_sortie_obj:
                messages.error(request, 'La date de départ doit être postérieure à la date d\'arrivée.')
                return redirect('client_reservation')
            
            if date_entree_obj < timezone.now().date():
                messages.error(request, 'La date d\'arrivée ne peut pas être dans le passé.')
                return redirect('client_reservation')
            
            # Vérifier les réservations qui se chevauchent
            reservations_chevauchees = Reservation.objects.filter(
                chambre=chambre,
                statut__in=['confirmee', 'en_cours'],
                date_entree__lt=date_sortie_obj,
                date_sortie__gt=date_entree_obj
            )
            
            if reservations_chevauchees.exists():
                messages.error(request, 'Cette chambre n\'est pas disponible pour les dates sélectionnées.')
                return redirect('client_reservation')
            
            # Créer la réservation
            reservation = Reservation(
                client=client,
                chambre=chambre,
                date_entree=date_entree_obj,
                date_sortie=date_sortie_obj,
                nombre_personnes=nombre_personnes,
                statut='en_attente',  # Les réservations client commencent en attente
                remarques=remarques,
                cree_par=request.user
            )
            
            reservation.save()
                
            messages.success(request, f'Votre demande de réservation a été envoyée avec succès ! Prix estimé : {reservation.prix_total}€. Vous recevrez une confirmation par email.')
            return redirect('client_reservation')
            
        except Chambre.DoesNotExist:
            messages.error(request, 'Chambre introuvable.')
        except ValueError as e:
            messages.error(request, f'Format de date invalide : {str(e)}')
        except Exception as e:
            messages.error(request, f'Erreur lors de la réservation : {str(e)}')
    
    # Types de chambres disponibles
    types_chambre = Chambre.TYPE_CHOICES
    chambres_disponibles = Chambre.objects.filter(statut='libre').order_by('type_chambre', 'numero')
    
    context = {
        'client': client,
        'types_chambre': types_chambre,
        'chambres_disponibles': chambres_disponibles,
        'chambre_preselectionnee': chambre_preselectionnee,
    }
    
    return render(request, 'hotel/client/reservation_client.html', context)


from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json

def check_disponibilite_api(request):
    """
    API pour vérifier la disponibilité d'une chambre
    """
    chambre_id = request.GET.get('chambre_id')
    date_entree = request.GET.get('date_entree')
    date_sortie = request.GET.get('date_sortie')
    
    if not all([chambre_id, date_entree, date_sortie]):
        return JsonResponse({'error': 'Paramètres manquants'}, status=400)
    
    try:
        # Récupérer la chambre
        chambre = Chambre.objects.get(pk=chambre_id)
        
        # Convertir les dates
        from datetime import datetime
        date_entree_obj = datetime.strptime(date_entree, '%Y-%m-%d').date()
        date_sortie_obj = datetime.strptime(date_sortie, '%Y-%m-%d').date()
        
        # Vérifier les réservations qui se chevauchent
        reservations_chevauchees = Reservation.objects.filter(
            chambre=chambre,
            statut__in=['confirmee', 'en_cours'],
            date_entree__lt=date_sortie_obj,
            date_sortie__gt=date_entree_obj
        )
        
        disponible = not reservations_chevauchees.exists()
        
        response_data = {
            'disponible': disponible,
            'chambre': {
                'id': chambre.id,
                'numero': chambre.numero,
                'type': chambre.get_type_chambre_display(),
                'prix': str(chambre.prix_par_nuit)
            }
        }
        
        if not disponible:
            # Ajouter les réservations existantes
            response_data['reservations_en_cours'] = []
            for res in reservations_chevauchees:
                response_data['reservations_en_cours'].append({
                    'date_entree': res.date_entree.strftime('%d/%m/%Y'),
                    'date_sortie': res.date_sortie.strftime('%d/%m/%Y'),
                    'client': res.client.nom_complet if res.client else 'Client'
                })
            
            # Suggérer des chambres alternatives
            chambres_alternatives = Chambre.objects.filter(
                statut='libre',
                type_chambre=chambre.type_chambre
            ).exclude(pk=chambre.id)
            
            response_data['suggestions'] = []
            for alt_chambre in chambres_alternatives[:3]:  # Limiter à 3 suggestions
                # Vérifier si l'alternative est disponible
                alt_reservations = Reservation.objects.filter(
                    chambre=alt_chambre,
                    statut__in=['confirmee', 'en_cours'],
                    date_entree__lt=date_sortie_obj,
                    date_sortie__gt=date_entree_obj
                )
                
                if not alt_reservations.exists():
                    response_data['suggestions'].append({
                        'id': alt_chambre.id,
                        'numero': alt_chambre.numero,
                        'type': alt_chambre.get_type_chambre_display(),
                        'prix': str(alt_chambre.prix_par_nuit)
                    })
        
        return JsonResponse(response_data)
        
    except Chambre.DoesNotExist:
        return JsonResponse({'error': 'Chambre introuvable'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Format de date invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@client_required
def contact_client(request):
    """
    Page de contact pour les clients
    Formulaire de contact spécifique aux clients avec validation et sauvegarde
    """
    # Récupérer le profil client
    try:
        user_profile = request.user.profile
        client = user_profile.client
    except:
        client = None
    
    # Sujets prédéfinis pour le formulaire
    SUJETS_CHOICES = [
        ('reservation', 'Question sur une réservation'),
        ('chambre', 'Information sur les chambres'),
        ('service', 'Demande de service'),
        ('reclamation', 'Réclamation'),
        ('partenariat', 'Proposition de partenariat'),
        ('autre', 'Autre'),
    ]
    
    if request.method == 'POST':
        # Traitement du formulaire de contact
        sujet = request.POST.get('sujet')
        sujet_autre = request.POST.get('sujet_autre', '')
        message = request.POST.get('message')
        nom = request.POST.get('nom', '')
        email = request.POST.get('email', '')
        telephone = request.POST.get('telephone', '')
        urgence = request.POST.get('urgence', 'normal')
        
        # Validation des données
        errors = []
        
        if not sujet:
            errors.append('Veuillez sélectionner un sujet.')
        if sujet == 'autre' and not sujet_autre:
            errors.append('Veuillez préciser votre sujet.')
        if not message or len(message.strip()) < 10:
            errors.append('Votre message doit contenir au moins 10 caractères.')
        if not email or '@' not in email:
            errors.append('Veuillez fournir une adresse email valide.')
        
        if not errors:
            # Préparer le sujet complet
            sujet_complet = dict(SUJETS_CHOICES).get(sujet, sujet)
            if sujet == 'autre' and sujet_autre:
                sujet_complet = sujet_autre
            
            # Sauvegarder le message en base de données avec gestion d'erreur
            try:
                from .models import ContactMessage
                
                contact_message = ContactMessage.objects.create(
                    nom=nom or (client.nom_complet if client else request.user.get_full_name()),
                    email=email or (client.email if client else request.user.email),
                    telephone=telephone or (client.telephone if client else ''),
                    client=client,
                    sujet=sujet,
                    sujet_autre=sujet_autre if sujet == 'autre' else None,
                    message=message.strip(),
                    urgence=urgence,
                    ip_client=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    newsletter=request.POST.get('newsletter', False) == 'on',
                )
                
                # Créer une notification pour les administrateurs
                try:
                    from .models import Notification
                    from django.utils import timezone
                    
                    # Définir la priorité selon l'urgence du message
                    priorite_mapping = {
                        'normal': 'normale',
                        'urgent': 'haute', 
                        'critique': 'critique'
                    }
                    notification_priorite = priorite_mapping.get(urgence, 'normale')
                    
                    # Créer la notification
                    notification = Notification.objects.create(
                        type_notification='contact_client',
                        message=f" Nouveau message de {contact_message.nom}: {sujet_complet}",
                        priorite=notification_priorite,
                        objet_lie_id=contact_message.id,
                        objet_lie=f"Message client #{contact_message.id}",
                        objet_lie_url=f"/admin/messages/{contact_message.id}/",
                        date_creation=timezone.now(),
                        lue=False,
                        traitee=False
                    )
                    
                except Exception as notif_error:
                    # Continuer même si la notification échoue
                    print(f"Erreur création notification: {notif_error}")
                
                # Envoyer une notification email (optionnel)
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    
                    sujet_email = f"[Hôtel de Luxe] {sujet_complet}"
                    message_email = f"""
                    Nouveau message de contact reçu :
                    
                    Nom : {contact_message.nom}
                    Email : {contact_message.email}
                    Téléphone : {contact_message.telephone or 'Non renseigné'}
                    Sujet : {sujet_complet}
                    Urgence : {contact_message.get_urgence_display()}
                    Date : {contact_message.date_envoi.strftime('%d/%m/%Y %H:%M')}
                    
                    Message :
                    {contact_message.message}
                    
                    ---
                    IP : {contact_message.ip_client}
                    """
                    
                    send_mail(
                        sujet_email,
                        message_email,
                        settings.DEFAULT_FROM_EMAIL,
                        ['contact@hotel-luxe.com'],  # Email de l'hôtel
                        fail_silently=False,
                    )
                except Exception as e:
                    # Continuer même si l'email échoue
                    print(f"Erreur email: {e}")
                
                # Message de succès avec détails
                messages.success(
                    request, 
                    f'Votre message concernant "{sujet_complet}" a été envoyé avec succès. '
                    f'Nous vous répondrons dans les plus brefs délais à {email or contact_message.email}.'
                )
                
            except Exception as db_error:
                # Si la base de données ne fonctionne pas, au moins envoyer un email
                print(f"Erreur base de données: {db_error}")
                
                # Envoyer un email de secours
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    
                    sujet_email = f"[URGENT] Message contact - Erreur base de données"
                    message_email = f"""
                    ERREUR BASE DE DONNÉES - Message reçu :
                    
                    Nom : {nom}
                    Email : {email}
                    Téléphone : {telephone or 'Non renseigné'}
                    Sujet : {sujet_complet}
                    Urgence : {urgence}
                    
                    Message :
                    {message.strip()}
                    
                    ---
                    Erreur : {str(db_error)}
                    IP : {request.META.get('REMOTE_ADDR', '')}
                    """
                    
                    send_mail(
                        sujet_email,
                        message_email,
                        settings.DEFAULT_FROM_EMAIL,
                        ['contact@hotel-luxe.com'],
                        fail_silently=False,
                    )
                    
                    messages.success(
                        request, 
                        f'Votre message concernant "{sujet_complet}" a été envoyé avec succès. '
                        f'Nous vous répondrons dans les plus brefs délais à {email}.'
                    )
                    
                except Exception as email_error:
                    print(f"Erreur email aussi: {email_error}")
                    messages.error(
                        request, 
                        'Une erreur technique est survenue. Veuillez nous contacter directement par téléphone au +223 77 12 34 56.'
                    )
            
            return redirect('client_contact')
        else:
            # Afficher les erreurs
            for error in errors:
                messages.error(request, error)
    
    context = {
        'client': client,
        'sujets_choices': SUJETS_CHOICES,
        'urgence_levels': [
            ('normal', 'Normal - 24-48h'),
            ('urgent', 'Urgent - 4-8h'),
            ('critique', 'Critique - 1-2h'),
        ],
    }
    
    return render(request, 'hotel/client/contact_client.html', context)


@client_required
def profile_client(request):
    """
    Page de profil pour les clients
    Permet de modifier les informations personnelles
    """
    # Récupérer le profil client
    try:
        user_profile = request.user.profile
        client = user_profile.client
    except:
        client = None
    
    if request.method == 'POST':
        # Traitement de la modification du profil
        nom_complet = request.POST.get('nom_complet')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        
        if client:
            if nom_complet:
                client.nom_complet = nom_complet
            if email:
                client.email = email
            if telephone:
                client.telephone = telephone
            client.save()
            
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('client_profile')
    
    context = {
        'client': client,
    }
    
    return render(request, 'hotel/client/profile_client.html', context)


@client_required
def settings_client(request):
    """
    Page des paramètres pour les clients
    Permet de configurer les préférences du compte
    """
    # Récupérer le profil client
    try:
        user_profile = request.user.profile
        client = user_profile.client
    except:
        client = None

    # Charger ou créer les paramètres liés au profil
    from .forms import ClientSettingsForm
    from .models import ClientSettings

    settings_obj, _ = ClientSettings.objects.get_or_create(user_profile=user_profile) if user_profile else (None, None)

    if request.method == 'POST':
        if not settings_obj:
            messages.error(request, 'Impossible de sauvegarder les paramètres : profil non trouvé.')
            return redirect('client_settings')
        form = ClientSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vos paramètres ont été mis à jour avec succès.')
            return redirect('client_settings')
        else:
            messages.error(request, 'Certaines informations sont invalides. Veuillez corriger et réessayer.')
    else:
        form = ClientSettingsForm(instance=settings_obj)

    context = {
        'client': client,
        'settings': settings_obj,
        'settings_form': form,
    }

    return render(request, 'hotel/client/settings_client.html', context)


# ============================================
# VUES ADMINISTRATION MESSAGES DE CONTACT
# ============================================
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import models


@staff_member_required
def admin_messages_contact(request):
    """
    Vue pour l'administration des messages de contact
    Permet aux employés et admin de voir et gérer les messages
    """
    from .models import ContactMessage
    
    # Récupérer les filtres
    statut_filtre = request.GET.get('statut')
    urgence_filtre = request.GET.get('urgence')
    search = request.GET.get('search')
    
    # Base de la requête
    messages_qs = ContactMessage.objects.all()
    
    # Appliquer les filtres
    if statut_filtre:
        messages_qs = messages_qs.filter(statut=statut_filtre)
    
    if urgence_filtre:
        messages_qs = messages_qs.filter(urgence=urgence_filtre)
    
    if search:
        messages_qs = messages_qs.filter(
            models.Q(nom__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(sujet__icontains=search) |
            models.Q(message__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(messages_qs, 20)  # 20 messages par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': ContactMessage.objects.count(),
        'nouveau': ContactMessage.objects.filter(statut='nouveau').count(),
        'en_cours': ContactMessage.objects.filter(statut='en_cours').count(),
        'urgent': ContactMessage.objects.filter(urgence='urgent').count(),
        'critique': ContactMessage.objects.filter(urgence='critique').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'messages_qs': page_obj,
        'stats': stats,
        'statuts_choices': ContactMessage.STATUT_CHOICES,
        'urgence_choices': ContactMessage.URGENCE_CHOICES,
        'filtres_actuels': {
            'statut': statut_filtre,
            'urgence': urgence_filtre,
            'search': search,
        }
    }
    
    return render(request, 'hotel/admin/messages_contact.html', context)


@staff_member_required
def admin_message_detail(request, message_id):
    """
    Vue pour voir les détails d'un message et y répondre
    """
    from .models import ContactMessage
    
    message = get_object_or_404(ContactMessage, id=message_id)
    
    if request.method == 'POST':
        # Traitement de la réponse
        reponse = request.POST.get('reponse')
        nouveau_statut = request.POST.get('statut')
        
        if reponse:
            message.reponse = reponse
            message.date_reponse = timezone.now()
            message.statut = nouveau_statut
            message.traite_par = request.user
            message.date_traitement = timezone.now()
            message.save()
            
            # Envoyer la réponse par email
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                sujet_email = f"Réponse à votre message - Hôtel de Luxe"
                message_email = f"""
                Bonjour {message.nom},
                
                Nous avons bien reçu votre message concernant : {message.sujet_complet}
                
                Voici notre réponse :
                {reponse}
                
                Cordialement,
                L'équipe de l'Hôtel de Luxe
                """
                
                send_mail(
                    sujet_email,
                    message_email,
                    settings.DEFAULT_FROM_EMAIL,
                    [message.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Réponse envoyée avec succès par email.')
            except Exception as e:
                messages.warning(request, 'Réponse sauvegardée mais email non envoyé.')
            
            return redirect('admin_messages_contact')
    
    context = {
        'message': message,
        'statuts_choices': ContactMessage.STATUT_CHOICES,
    }
    
    return render(request, 'hotel/admin/message_detail.html', context)


@staff_member_required
def admin_message_update_statut(request, message_id):
    """
    Vue AJAX pour mettre à jour le statut d'un message
    """
    from .models import ContactMessage
    
    if request.method == 'POST':
        message = get_object_or_404(ContactMessage, id=message_id)
        nouveau_statut = request.POST.get('statut')
        
        if nouveau_statut in [choice[0] for choice in ContactMessage.STATUT_CHOICES]:
            message.statut = nouveau_statut
            if nouveau_statut != 'nouveau':
                message.traite_par = request.user
                message.date_traitement = timezone.now()
            message.save()
            
            return JsonResponse({
                'success': True,
                'statut': message.get_statut_display(),
                'statut_class': f'status-{nouveau_statut}'
            })
    
    return JsonResponse({'success': False}, status=400)


# ============================================
# VUES POUR LA GESTION DES NOTIFICATIONS ADMIN
# ============================================

@admin_required
def admin_notifications(request):
    """
    Page principale des notifications admin
    Centralise tous les événements du système
    """
    from .models import Notification
    
    # Filtres
    type_filter = request.GET.get('type', '')
    priorite_filter = request.GET.get('priorite', '')
    statut_filter = request.GET.get('statut', 'non_lues')  # Par défaut: non lues
    
    # Query de base
    notifications = Notification.objects.select_related(
        'reservation', 'message_contact', 'maintenance', 'article_inventaire'
    ).prefetch_related('destinataires')
    
    # Application des filtres
    if statut_filter == 'non_lues':
        notifications = notifications.filter(lue=False)
    elif statut_filter == 'lues':
        notifications = notifications.filter(lue=True)
    elif statut_filter == 'non_traitees':
        notifications = notifications.filter(traitee=False)
    
    if type_filter:
        notifications = notifications.filter(type_notification=type_filter)
    
    if priorite_filter:
        notifications = notifications.filter(priorite=priorite_filter)
    
    # Statistiques
    stats = {
        'total': Notification.objects.count(),
        'non_lues': Notification.objects.filter(lue=False).count(),
        'non_traitees': Notification.objects.filter(traitee=False).count(),
        'critiques': Notification.objects.filter(priorite='critique', lue=False).count(),
    }
    
    # Pagination
    paginator = Paginator(notifications.order_by('-date_creation'), 20)
    page_number = request.GET.get('page')
    notifications_page = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications_page,
        'stats': stats,
        'type_filter': type_filter,
        'priorite_filter': priorite_filter,
        'statut_filter': statut_filter,
        'type_choices': Notification.TYPE_CHOICES,
        'priorite_choices': Notification.PRIORITE_CHOICES,
    }
    
    return render(request, 'hotel/admin/notifications.html', context)


@admin_required
@require_http_methods(["POST"])
def notification_marquer_lue(request, notification_id):
    """
    Marquer une notification comme lue
    """
    from .models import Notification
    
    notification = get_object_or_404(Notification, id=notification_id)
    notification.marquer_comme_lue(request.user)
    
    return JsonResponse({'success': True})


@admin_required
@require_http_methods(["POST"])
def notification_marquer_traitee(request, notification_id):
    """
    Marquer une notification comme traitée
    """
    from .models import Notification
    
    notification = get_object_or_404(Notification, id=notification_id)
    notification.marquer_comme_traitee()
    
    return JsonResponse({'success': True})


@admin_required
@require_http_methods(["POST"])
def notification_marquer_toutes_lues(request):
    """
    Marquer toutes les notifications comme lues
    """
    from .models import Notification
    
    Notification.objects.filter(lue=False).update(
        lue=True,
        date_lecture=timezone.now()
    )
    
    return JsonResponse({'success': True})


# ============================================
# VUES AMÉLIORÉES POUR LA MAINTENANCE
# ============================================

@role_required('admin', 'employe')
def maintenance_list_improved(request):
    """
    Liste améliorée des maintenances avec filtres et statistiques
    """
    from .models import Maintenance
    
    # Filtres
    statut_filter = request.GET.get('statut', '')
    priorite_filter = request.GET.get('priorite', '')
    type_filter = request.GET.get('type', '')
    
    maintenances = Maintenance.objects.select_related('chambre', 'assigned_to', 'cree_par')
    
    if statut_filter:
        maintenances = maintenances.filter(statut=statut_filter)
    if priorite_filter:
        maintenances = maintenances.filter(priorite=priorite_filter)
    if type_filter:
        maintenances = maintenances.filter(type_maintenance=type_filter)
    
    # Statistiques
    stats = {
        'total': Maintenance.objects.count(),
        'en_attente': Maintenance.objects.filter(statut='en_attente').count(),
        'en_cours': Maintenance.objects.filter(statut='en_cours').count(),
        'terminee': Maintenance.objects.filter(statut='terminee').count(),
        'urgentes': Maintenance.objects.filter(type_maintenance='urgence', statut__in=['en_attente', 'en_cours']).count(),
    }
    
    context = {
        'maintenances': maintenances.order_by('-date_creation'),
        'stats': stats,
        'statut_filter': statut_filter,
        'priorite_filter': priorite_filter,
        'type_filter': type_filter,
    }
    
    return render(request, 'hotel/maintenance_list.html', context)


@role_required('admin', 'employe')
@require_http_methods(["POST"])
def maintenance_update_status(request, maintenance_id):
    """
    Met à jour le statut d'une maintenance et gère le cycle de vie
    """
    from .models import Maintenance, ChargeComptable
    from .signals import creer_charge_maintenance_automatique
    
    maintenance = get_object_or_404(Maintenance, id=maintenance_id)
    nouveau_statut = request.POST.get('statut')
    
    # Validation des transitions de statut
    transitions_valides = {
        'en_attente': ['en_cours', 'annulee'],
        'en_cours': ['terminee', 'annulee'],
        'terminee': [],  # Statut final
        'annulee': [],  # Statut final
    }
    
    if nouveau_statut not in transitions_valides.get(maintenance.statut, []):
        return JsonResponse({
            'success': False,
            'error': f'Transition invalide de {maintenance.get_statut_display()} vers {nouveau_statut}'
        })
    
    # Mise à jour du statut
    maintenance.statut = nouveau_statut
    
    # Gestion des dates selon le statut
    if nouveau_statut == 'en_cours' and not maintenance.date_debut:
        maintenance.date_debut = timezone.now()
    elif nouveau_statut == 'terminee':
        maintenance.date_fin = timezone.now()
        
        # Créer automatiquement la charge comptable si coût renseigné
        if maintenance.actual_cost and maintenance.actual_cost > 0:
            creer_charge_maintenance_automatique(maintenance)
    
    maintenance.save()
    
    return JsonResponse({
        'success': True,
        'statut': maintenance.get_statut_display()
    })


@role_required('admin', 'employe')
@require_http_methods(["POST"])
def maintenance_link_inventory(request, maintenance_id):
    """
    Lier une maintenance à des pièces d'inventaire utilisées
    """
    from .models import Maintenance, InventoryItem, InventoryMovement
    
    maintenance = get_object_or_404(Maintenance, id=maintenance_id)
    
    # Récupérer les articles et quantités depuis le formulaire
    import json
    data = json.loads(request.body)
    articles_data = data.get('articles', [])
    
    for article_data in articles_data:
        article_id = article_data.get('article_id')
        quantite = article_data.get('quantite')
        
        article = InventoryItem.objects.get(id=article_id)
        
        # Créer un mouvement de sortie pour maintenance
        InventoryMovement.objects.create(
            article=article,
            type_mouvement='sortie',
            quantite=quantite,
            notes=f"Utilisé pour maintenance: {maintenance.titre}",
            effectue_par=request.user
        )
    
    messages.success(request, 'Pièces liées à la maintenance avec succès.')
    return JsonResponse({'success': True})


# ============================================
# VUES POUR LA GESTION DE L'AGENT IA ADMIN
# ============================================

@admin_required
def agent_ia_dashboard(request):
    """
    Page de gestion de l'agent IA (admin uniquement)
    Permet de configurer, activer/désactiver et voir les interactions
    """
    from .models import AgentIAConfig, AgentIAInteraction
    
    config = AgentIAConfig.get_config()
    
    # Statistiques des 7 derniers jours
    from datetime import timedelta
    sept_jours = timezone.now() - timedelta(days=7)
    
    stats = {
        'interactions_total': AgentIAInteraction.objects.count(),
        'interactions_semaine': AgentIAInteraction.objects.filter(date_interaction__gte=sept_jours).count(),
        'interactions_aujourd_hui': config.requetes_aujourd_hui,
        'utilisateurs_uniques': AgentIAInteraction.objects.values('utilisateur').distinct().count(),
        'taux_satisfaction': 0,  # À calculer si feedback activé
    }
    
    # Interactions récentes
    interactions_recentes = AgentIAInteraction.objects.select_related('utilisateur').order_by('-date_interaction')[:50]
    
    # Calculer taux de satisfaction si données disponibles
    feedbacks = AgentIAInteraction.objects.filter(utile__isnull=False)
    if feedbacks.exists():
        positifs = feedbacks.filter(utile=True).count()
        stats['taux_satisfaction'] = round((positifs / feedbacks.count()) * 100, 1)
    
    context = {
        'config': config,
        'stats': stats,
        'interactions_recentes': interactions_recentes,
    }
    
    return render(request, 'hotel/admin/agent_ia_dashboard.html', context)


@admin_required
@require_http_methods(["POST"])
def agent_ia_toggle_activation(request):
    """
    Activer/désactiver l'agent IA
    """
    from .models import AgentIAConfig
    import logging
    logger = logging.getLogger(__name__)

    try:
        config = AgentIAConfig.get_config()
        config.actif = not config.actif
        config.modifie_par = request.user
        config.save()

        return JsonResponse({
            'success': True,
            'actif': config.actif,
            'message': 'Agent IA activé' if config.actif else 'Agent IA désactivé'
        })
    except Exception as e:
        logger.exception('Erreur lors du changement d\'état de l\'Agent IA')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@admin_required
@require_http_methods(["POST"])
def agent_ia_update_config(request):
    """
    Mettre à jour la configuration de l'agent IA
    """
    from .models import AgentIAConfig
    import json
    
    try:
        data = json.loads(request.body)
        config = AgentIAConfig.get_config()
        
        # Mise à jour des champs
        if 'nom_agent' in data:
            config.nom_agent = data['nom_agent']
        if 'description' in data:
            config.description = data['description']
        if 'peut_repondre_clients' in data:
            config.peut_repondre_clients = data['peut_repondre_clients']
        if 'peut_consulter_donnees' in data:
            config.peut_consulter_donnees = data['peut_consulter_donnees']
        if 'peut_suggerer_actions' in data:
            config.peut_suggerer_actions = data['peut_suggerer_actions']
        if 'peut_generer_rapports' in data:
            config.peut_generer_rapports = data['peut_generer_rapports']
        if 'max_requetes_jour' in data:
            config.max_requetes_jour = int(data['max_requetes_jour'])
        
        config.modifie_par = request.user
        config.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Configuration mise à jour avec succès'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@admin_required
def agent_ia_view_interactions(request):
    """
    Vue détaillée des interactions avec l'agent IA
    """
    from .models import AgentIAInteraction
    
    # Filtres
    utilisateur_filter = request.GET.get('utilisateur', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    interactions = AgentIAInteraction.objects.select_related('utilisateur', 'config')
    
    if utilisateur_filter:
        interactions = interactions.filter(utilisateur__username__icontains=utilisateur_filter)
    if date_debut:
        interactions = interactions.filter(date_interaction__gte=date_debut)
    if date_fin:
        interactions = interactions.filter(date_interaction__lte=date_fin)
    
    # Pagination
    paginator = Paginator(interactions.order_by('-date_interaction'), 50)
    page_number = request.GET.get('page')
    interactions_page = paginator.get_page(page_number)
    
    context = {
        'interactions': interactions_page,
        'utilisateur_filter': utilisateur_filter,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    
    return render(request, 'hotel/admin/agent_ia_interactions.html', context)

# ============================================
# API Réservations Client (pour popups)
# ============================================
@login_required
@client_required
def reservation_details_api(request, pk):
    """
    API pour récupérer les détails d'une réservation
    """
    try:
        # Récupérer le client connecté
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'client'):
            client = request.user.profile.client
        else:
            client = Client.objects.get(email=request.user.email)
        
        # Récupérer la réservation
        reservation = get_object_or_404(Reservation, pk=pk, client=client)
        
        # Récupérer les images de la chambre
        images = ChambreImage.objects.filter(chambre=reservation.chambre)
        image_list = [img.image.url for img in images]
        
        data = {
            'success': True,
            'reservation': {
                'id': reservation.id,
                'chambre_numero': reservation.chambre.numero,
                'chambre_type': reservation.chambre.get_type_chambre_display(),
                'chambre_description': reservation.chambre.description or '',
                'images': image_list,
                'date_entree': reservation.date_entree.strftime('%d/%m/%Y'),
                'date_sortie': reservation.date_sortie.strftime('%d/%m/%Y'),
                'nombre_nuits': reservation.nombre_nuits,
                'nombre_personnes': reservation.nombre_personnes,
                'prix_total': str(reservation.prix_total),
                'statut': reservation.statut,
                'statut_display': reservation.get_statut_display(),
                'date_creation': reservation.date_creation.strftime('%d/%m/%Y %H:%M'),
                'remarques': reservation.remarques or ''
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@client_required
def reservation_modify_api(request, pk):
    """
    API pour modifier une réservation (retourne les données pour le formulaire)
    """
    try:
        # Récupérer le client connecté
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'client'):
            client = request.user.profile.client
        else:
            client = Client.objects.get(email=request.user.email)
        
        # Récupérer la réservation
        reservation = get_object_or_404(Reservation, pk=pk, client=client)
        
        if reservation.statut not in ['en_attente', 'confirmee']:
            return JsonResponse({'error': 'Cette réservation ne peut plus être modifiée'}, status=400)
        
        # Récupérer les chambres disponibles pour les mêmes dates
        chambres_disponibles = Chambre.objects.filter(
            statut='libre'
        ).exclude(
            id=reservation.chambre.id
        )
        
        # Exclure les chambres réservées pour la période
        chambres_disponibles = chambres_disponibles.exclude(
            id__in=Reservation.objects.filter(
                statut__in=['confirmee', 'en_cours'],
                date_entree__lte=reservation.date_sortie,
                date_sortie__gte=reservation.date_entree
            ).values_list('chambre_id', flat=True)
        )
        
        chambres_list = []
        for chambre in chambres_disponibles:
            chambres_list.append({
                'id': chambre.id,
                'numero': chambre.numero,
                'type': chambre.get_type_chambre_display(),
                'prix': str(chambre.prix_par_nuit),
                'capacite': chambre.capacite
            })
        
        data = {
            'success': True,
            'reservation': {
                'id': reservation.id,
                'chambre_id': reservation.chambre.id,
                'date_entree': reservation.date_entree.strftime('%d/%m/%Y'),
                'date_sortie': reservation.date_sortie.strftime('%d/%m/%Y'),
                'nombre_personnes': reservation.nombre_personnes,
                'remarques': reservation.remarques or ''
            },
            'chambres_disponibles': chambres_list
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@client_required
def reservation_cancel_api(request, pk):
    """
    API pour annuler une réservation
    """
    try:
        # Récupérer le client connecté
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'client'):
            client = request.user.profile.client
        else:
            client = Client.objects.get(email=request.user.email)
        
        # Récupérer la réservation
        reservation = get_object_or_404(Reservation, pk=pk, client=client)
        
        if reservation.statut not in ['en_attente', 'confirmee']:
            return JsonResponse({'error': 'Cette réservation ne peut plus être annulée'}, status=400)
        
        # Annuler la réservation
        reservation.statut = 'annulee'
        reservation.save()
        
        data = {
            'success': True,
            'message': 'Réservation annulée avec succès',
            'reservation_id': reservation.id
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

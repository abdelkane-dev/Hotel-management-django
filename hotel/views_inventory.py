# -*- coding: utf-8 -*-
"""
Vues pour la gestion de l'inventaire de l'hôtel
Ce fichier contient toutes les vues liées à la gestion des articles, 
catégories et mouvements d'inventaire
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import csv
import json

from .models import InventoryItem, InventoryCategory, InventoryMovement
from .forms import InventoryItemForm, InventoryCategoryForm


def is_staff_or_manager(user):
    """Vérifie si l'utilisateur a accès à la gestion de l'inventaire"""
    return user.is_staff or user.is_superuser


class InventoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vue liste des articles d'inventaire avec filtres avancés"""
    model = InventoryItem
    template_name = 'hotel/inventory_list_new.html'
    context_object_name = 'articles'
    paginate_by = 20

    def test_func(self):
        return is_staff_or_manager(self.request.user)

    def get_queryset(self):
        queryset = InventoryItem.objects.select_related('categorie').all()
        
        # Filtrage par recherche
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nom__icontains=q) |
                Q(reference__icontains=q) |
                Q(description__icontains=q)
            )
        
        # Filtrage par catégorie
        categorie = self.request.GET.get('categorie')
        if categorie:
            queryset = queryset.filter(categorie_id=categorie)
        
        # Filtrage par état
        etat = self.request.GET.get('etat')
        if etat:
            queryset = queryset.filter(etat=etat)
        
        # Filtrage par statut de stock
        statut_stock = self.request.GET.get('statut_stock')
        if statut_stock == 'alerte':
            queryset = queryset.filter(
                quantite_disponible__lte=F('seuil_alerte'),
                quantite_disponible__gt=0
            )
        elif statut_stock == 'epuise':
            queryset = queryset.filter(quantite_disponible=0)
        elif statut_stock == 'normal':
            queryset = queryset.filter(
                quantite_disponible__gt=F('seuil_alerte')
            )
        
        # Filtrage par localisation
        localisation = self.request.GET.get('localisation')
        if localisation:
            queryset = queryset.filter(localisation_principale=localisation)
        
        return queryset.order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        context.update({
            'total_articles': InventoryItem.objects.count(),
            'total_disponible': InventoryItem.objects.aggregate(
                total=Sum('quantite_disponible')
            )['total'] or 0,
            'stock_alertes': InventoryItem.objects.filter(
                quantite_disponible__lte=F('seuil_alerte'),
                quantite_disponible__gt=0
            ).count(),
            'ruptures_stock': InventoryItem.objects.filter(
                quantite_disponible=0
            ).count(),
            'categories': InventoryCategory.objects.all(),
            'all_articles': InventoryItem.objects.all(),
        })
        
        return context


class InventoryDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Vue détail d'un article avec historique des mouvements"""
    model = InventoryItem
    template_name = 'hotel/inventory_detail.html'
    context_object_name = 'article'

    def test_func(self):
        return is_staff_or_manager(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        
        # Historique des mouvements
        context['mouvements'] = article.mouvements.select_related(
            'effectue_par', 'chambre'
        ).order_by('-date_mouvement')[:20]
        
        # Statistiques de l'article
        context.update({
            'mouvements_entree': article.mouvements.filter(
                type_mouvement__in=['entree', 'retour']
            ).aggregate(total=Sum('quantite'))['total'] or 0,
            'mouvements_sortie': article.mouvements.filter(
                type_mouvement__in=['sortie', 'perte', 'casse', 'affectation']
            ).aggregate(total=Sum('quantite'))['total'] or 0,
        })
        
        return context


class InventoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vue de création d'un article d'inventaire"""
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'hotel/inventory_form.html'
    success_url = reverse_lazy('inventory_list')

    def test_func(self):
        return is_staff_or_manager(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Article "{form.instance.nom}" créé avec succès.')
        return super().form_valid(form)


class InventoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vue de modification d'un article d'inventaire"""
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'hotel/inventory_form.html'
    success_url = reverse_lazy('inventory_list')

    def test_func(self):
        return is_staff_or_manager(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Article "{form.instance.nom}" mis à jour avec succès.')
        return super().form_valid(form)

class InventoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Vue de suppression d'un article d'inventaire"""
    model = InventoryItem
    template_name = 'hotel/inventory_confirm_delete.html'
    success_url = reverse_lazy('inventory_list')

    def test_func(self):
        return self.request.user.is_superuser  # Seul l'admin peut supprimer

    def delete(self, request, *args, **kwargs):
        article = self.get_object()
        # Vérifier si l'article est utilisé dans des mouvements
        if article.mouvements.exists():
            messages.error(
                request, 
                f'Impossible de supprimer "{article.nom}" : il a des mouvements associés.'
            )
            return redirect('inventory_detail', pk=article.pk)
        
        messages.success(request, f'Article "{article.nom}" supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


@login_required
@user_passes_test(is_staff_or_manager)
@require_POST
def inventory_movement(request):
    """Vue pour enregistrer un mouvement d'inventaire"""
    try:
        article_id = request.POST.get('article')
        type_mouvement = request.POST.get('type_mouvement')
        quantite = int(request.POST.get('quantite'))
        notes = request.POST.get('notes', '')
        
        article = get_object_or_404(InventoryItem, id=article_id)
        
        # Validation des quantités
        if type_mouvement in ['sortie', 'perte', 'casse', 'affectation']:
            if quantite > article.quantite_disponible:
                return JsonResponse({
                    'success': False,
                    'error': f'Quantité insuffisante. Disponible: {article.quantite_disponible}'
                })
        
        # Création du mouvement
        mouvement = InventoryMovement.objects.create(
            article=article,
            type_mouvement=type_mouvement,
            quantite=quantite,
            notes=notes,
            effectue_par=request.user
        )
        
        messages.success(
            request, 
            f'Mouvement enregistré: {mouvement.get_type_mouvement_display()} '
            f'- {article.nom} x{quantite}'
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@user_passes_test(is_staff_or_manager)
def inventory_export(request):
    """Vue pour exporter l'inventaire en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventaire.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Référence', 'Nom', 'Catégorie', 'État', 'Quantité Totale', 
        'Quantité Disponible', 'Quantité Utilisée', 'Seuil Alerte',
        'Statut Stock', 'Localisation', 'Date Ajout'
    ])
    
    articles = InventoryItem.objects.select_related('categorie').all()
    for article in articles:
        writer.writerow([
            article.reference,
            article.nom,
            article.categorie.nom,
            article.get_etat_display(),
            article.quantite_totale,
            article.quantite_disponible,
            article.quantite_utilisee,
            article.seuil_alerte,
            article.statut_stock,
            article.get_localisation_principale_display(),
            article.date_ajout.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response


@login_required
@user_passes_test(is_staff_or_manager)
def inventory_stats_api(request):
    """API pour les statistiques d'inventaire (pour graphiques)"""
    stats = {
        'total_articles': InventoryItem.objects.count(),
        'by_category': list(
            InventoryCategory.objects.annotate(
                count=Count('articles')
            ).values('nom', 'count')
        ),
        'by_etat': list(
            InventoryItem.objects.values('etat').annotate(
                count=Count('id')
            ).order_by('etat')
        ),
        'stock_status': {
            'normal': InventoryItem.objects.filter(
                quantite_disponible__gt=F('seuil_alerte')
            ).count(),
            'alerte': InventoryItem.objects.filter(
                quantite_disponible__lte=F('seuil_alerte'),
                quantite_disponible__gt=0
            ).count(),
            'epuise': InventoryItem.objects.filter(
                quantite_disponible=0
            ).count(),
        }
    }
    
    return JsonResponse(stats)

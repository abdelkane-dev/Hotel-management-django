# -*- coding: utf-8 -*-
"""
Service IA pour le chatbot intelligent
Ce module gère l'intelligence conversationnelle du chatbot
"""

import re
from django.utils import timezone
from datetime import datetime, date, timedelta
from .models import Chambre, Client, Reservation, UserProfile


class HotelChatbotAI:
    """
    Intelligence artificielle du chatbot hôtelier
    Comprend le contexte, le rôle de l'utilisateur et répond de manière naturelle
    """
    
    def __init__(self, user, current_page=None):
        """
        Initialise le chatbot avec le contexte utilisateur
        
        Args:
            user: L'utilisateur Django authentifié
            current_page: La page actuelle (optionnel)
        """
        self.user = user
        self.current_page = current_page
        self.role = self._get_user_role()
        
    def _get_user_role(self):
        """Détermine le rôle de l'utilisateur"""
        if self.user.is_superuser:
            return 'admin'
        elif self.user.is_staff:
            return 'employe'
        else:
            return 'client'
    
    def process_message(self, message, page_context=None):
        """
        Traite le message de l'utilisateur et génère une réponse intelligente.
        Accepte un `page_context` optionnel fourni par la vue.
        
        Args:
            message: Le message de l'utilisateur
            page_context: Contexte de la page (ex: 'dashboard', 'chambres')
            
        Returns:
            str: Le texte de la réponse
        """
        # Mettre à jour le contexte de page si fourni
        if page_context is not None:
            self.current_page = page_context

        message = message.lower().strip()
        
        # Détection du type de question
        question_type = self._detect_question_type(message)
        
        # Router vers la bonne fonction de traitement
        handlers = {
            'greeting': self._handle_greeting,
            'chambres_disponibles': self._handle_chambres_disponibles,
            'prix_chambres': self._handle_prix_chambres,
            'reservation': self._handle_reservation,
            'client_info': self._handle_client_info,
            'statistiques': self._handle_statistiques,
            'aide': self._handle_aide,
            'fonctionnalite': self._handle_fonctionnalite,
            'navigation': self._handle_navigation,
            'compte': self._handle_compte,
            'date': self._handle_date,
        }
        
        handler = handlers.get(question_type, self._handle_unknown)
        result = handler(message)
        # Les handlers retournent généralement un dict {'success':..., 'message':...}
        if isinstance(result, dict):
            return result.get('message', '')
        return str(result)        
    
    def _detect_question_type(self, message):
        """
        Détecte intelligemment le type de question
        
        Args:
            message: Le message normalisé (lowercase)
            
        Returns:
            str: Type de question détecté
        """
        patterns = {
            'greeting': [
                r'\b(bonjour|salut|hello|hi|hey|bonsoir)\b',
                r'^(coucou|yo|cc)',
            ],
            'chambres_disponibles': [
                r'\b(chambre|room).*(disponible|libre|vacant)',
                r'\b(voir|consulter|afficher).*(chambre|room)',
                r'\bcombien.*(chambre|room)',
                r'\bliste.*(chambre|room)',
            ],
            'prix_chambres': [
                r'\b(prix|tarif|co[uû]t|combien|montant).*(chambre|room|nuit)',
                r'\bchambre.*(prix|tarif|co[uû]t)',
                r'\bsimple.*(prix|tarif)',
                r'\bdouble.*(prix|tarif)',
                r'\bsuite.*(prix|tarif)',
            ],
            'reservation': [
                r'\b(r[ée]serv|book|résa)',
                r'\bfaire.*(r[ée]servation|résa)',
                r'\bcomment.*(r[ée]server|résa)',
                r'\bcr[ée]er.*(r[ée]servation)',
            ],
            'client_info': [
                r'\b(client|customer).*(info|voir|consulter|liste)',
                r'\bajouter.*(client|customer)',
                r'\bcombien.*(client|customer)',
            ],
            'statistiques': [
                r'\b(statistique|stat|donn[ée]e|rapport|bilan)',
                r'\bcombien.*(r[ée]servation|client|chambre)',
                r'\btotal.*(revenu|gain|argent)',
            ],
            'aide': [
                r'\b(aide|help|assistance|support)\b',
                r'\bcomment.*(utiliser|fonctionn)',
                r'\bqu[\'e].*(faire|possible)',
            ],
            'fonctionnalite': [
                r'\bcomment.*(marche|fonction)',
                r'\b[àa] quoi.*(sert|utilise)',
                r'\bexpliqu.*(fonctionnalit|feature)',
            ],
            'navigation': [
                r'\bo[uù].*(trouver|voir|acc[ée]der)',
                r'\baller.*(page|menu|section)',
                r'\bnavigation',
            ],
            'compte': [
                r'\b(mon|mes).*(compte|profil|informations?)',
                r'\bchanger.*(mot de passe|email)',
                r'\bparam[èe]tre',
            ],
            'date': [
                r'\bquel.*(jour|date)',
                r'\baujourd\'?hui',
                r'\bdate.*(actuelle|du jour)',
            ],
        }
        
        # Tester chaque pattern
        for q_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, message, re.IGNORECASE):
                    return q_type
        
        return 'unknown'
    
    def _handle_greeting(self, message):
        """Gestion des salutations"""
        user_name = self.user.get_full_name() or self.user.username
        
        role_messages = {
            'admin': f"Bonjour {user_name} ! 👑 En tant qu'administrateur, vous avez accès à toutes les fonctionnalités. Comment puis-je vous aider ?",
            'employe': f"Bonjour {user_name} ! 🧑‍💼 Comment puis-je vous assister dans votre travail aujourd'hui ?",
            'client': f"Bonjour {user_name} ! 👋 Bienvenue dans votre espace client. Que puis-je faire pour vous ?",
        }
        
        return {
            'success': True,
            'message': role_messages.get(self.role, "Bonjour ! Comment puis-je vous aider ?")
        }
    
    def _handle_chambres_disponibles(self, message):
        """Gestion des questions sur les chambres disponibles"""
        chambres_libres = Chambre.objects.filter(statut='libre')
        
        # Détection du type de chambre demandé
        type_demande = None
        if 'simple' in message:
            type_demande = 'simple'
            chambres_libres = chambres_libres.filter(type_chambre='simple')
        elif 'double' in message:
            type_demande = 'double'
            chambres_libres = chambres_libres.filter(type_chambre='double')
        elif 'suite' in message:
            type_demande = 'suite'
            chambres_libres = chambres_libres.filter(type_chambre='suite')
        
        if chambres_libres.exists():
            count = chambres_libres.count()
            type_str = f" de type {type_demande}" if type_demande else ""
            
            response = f"✅ Nous avons {count} chambre(s){type_str} disponible(s) actuellement :\n\n"
            
            for chambre in chambres_libres[:5]:  # Limiter à 5 pour lisibilité
                response += f"🛏️ Chambre {chambre.numero} ({chambre.get_type_chambre_display()}) - {chambre.prix_par_nuit}€/nuit\n"
                if chambre.capacite:
                    response += f"   👥 Capacité : {chambre.capacite} personne(s)\n"
            
            if count > 5:
                response += f"\n... et {count - 5} autre(s) chambre(s)."
            
            # Suggestion contextuelle selon le rôle
            if self.role == 'client':
                response += "\n\n💡 Pour réserver, contactez la réception ou utilisez le formulaire de contact."
            elif self.role in ['admin', 'employe']:
                response += "\n\n💡 Vous pouvez créer une réservation via le menu 'Réservations' > 'Nouvelle réservation'."
        else:
            type_str = f" de type {type_demande}" if type_demande else ""
            response = f"😔 Désolé, aucune chambre{type_str} n'est disponible actuellement."
            
            # Suggestions alternatives
            if type_demande:
                autres_types = Chambre.objects.filter(statut='libre').exclude(type_chambre=type_demande)
                if autres_types.exists():
                    response += f"\n\nMais nous avons {autres_types.count()} chambre(s) d'autres types disponibles."
        
        return {
            'success': True,
            'message': response,
            'data': {
                'count': chambres_libres.count() if chambres_libres else 0,
                'type': type_demande
            }
        }
    
    def _handle_prix_chambres(self, message):
        """Gestion des questions sur les prix"""
        # Détection du type de chambre
        type_demande = None
        if 'simple' in message:
            type_demande = 'simple'
        elif 'double' in message:
            type_demande = 'double'
        elif 'suite' in message:
            type_demande = 'suite'
        
        if type_demande:
            chambres = Chambre.objects.filter(type_chambre=type_demande)
            if chambres.exists():
                prix_min = min(c.prix_par_nuit for c in chambres)
                prix_max = max(c.prix_par_nuit for c in chambres)
                
                if prix_min == prix_max:
                    response = f"💰 Une chambre {type_demande} coûte {prix_min}€ par nuit."
                else:
                    response = f"💰 Les chambres {type_demande} coûtent entre {prix_min}€ et {prix_max}€ par nuit."
            else:
                response = f"😔 Nous n'avons pas de chambre {type_demande} pour le moment."
        else:
            # Résumé de tous les prix
            types = Chambre.TYPE_CHOICES
            response = "💰 Voici nos tarifs par type de chambre :\n\n"
            
            for type_code, type_name in types:
                chambres = Chambre.objects.filter(type_chambre=type_code)
                if chambres.exists():
                    prix_min = min(c.prix_par_nuit for c in chambres)
                    prix_max = max(c.prix_par_nuit for c in chambres)
                    if prix_min == prix_max:
                        response += f"🛏️ {type_name} : {prix_min}€/nuit\n"
                    else:
                        response += f"🛏️ {type_name} : {prix_min}€ à {prix_max}€/nuit\n"
        
        return {
            'success': True,
            'message': response
        }
    
    def _handle_reservation(self, message):
        """Gestion des questions sur les réservations"""
        if self.role == 'client':
            response = (
                "📞 Pour effectuer une réservation :\n\n"
                "1️⃣ Contactez la réception au +33 1 23 45 67 89\n"
                "2️⃣ Ou envoyez un email à reservation@hotel.com\n"
                "3️⃣ Précisez vos dates et préférences\n\n"
                "💡 Astuce : Consultez d'abord nos chambres disponibles pour choisir celle qui vous convient !"
            )
        elif self.role in ['admin', 'employe']:
            response = (
                "📝 Pour créer une réservation :\n\n"
                "1️⃣ Allez dans 'Réservations' > 'Nouvelle réservation'\n"
                "2️⃣ Sélectionnez le client (ou créez-en un nouveau)\n"
                "3️⃣ Choisissez la chambre disponible\n"
                "4️⃣ Indiquez les dates d'entrée et de sortie\n"
                "5️⃣ Le prix sera calculé automatiquement !\n\n"
                "💡 Astuce : Vérifiez d'abord la disponibilité des chambres."
            )
        else:
            response = "Pour faire une réservation, veuillez contacter la réception."
        
        return {
            'success': True,
            'message': response
        }
    
    def _handle_client_info(self, message):
        """Gestion des questions sur les clients"""
        if self.role in ['admin', 'employe']:
            total_clients = Client.objects.count()
            response = f"👥 Nous avons actuellement {total_clients} client(s) enregistré(s).\n\n"
            response += "💡 Vous pouvez consulter la liste complète dans 'Clients'."
        else:
            response = "ℹ️ Cette information est réservée au personnel de l'hôtel."
        
        return {
            'success': True,
            'message': response
        }
    
    def _handle_statistiques(self, message):
        """Gestion des questions sur les statistiques"""
        if self.role == 'admin':
            from django.db.models import Sum
            
            total_clients = Client.objects.count()
            total_chambres = Chambre.objects.count()
            total_reservations = Reservation.objects.count()
            chambres_libres = Chambre.objects.filter(statut='libre').count()
            
            today = date.today()
            revenus_mois = Reservation.objects.filter(
                date_entree__year=today.year,
                date_entree__month=today.month,
                statut__in=['confirmee', 'en_cours', 'terminee']
            ).aggregate(total=Sum('prix_total'))['total'] or 0
            
            response = (
                f"📊 Statistiques globales :\n\n"
                f"👥 Clients : {total_clients}\n"
                f"🛏️ Chambres : {total_chambres} (dont {chambres_libres} libres)\n"
                f"📅 Réservations : {total_reservations}\n"
                f"💰 Revenus ce mois : {revenus_mois}€\n\n"
                f"💡 Consultez le dashboard pour plus de détails."
            )
        elif self.role == 'employe':
            response = (
                "📊 Pour accéder aux statistiques :\n"
                "Consultez votre dashboard employé qui affiche les informations essentielles."
            )
        else:
            response = "ℹ️ Les statistiques sont réservées au personnel de l'hôtel."
        
        return {
            'success': True,
            'message': response
        }
    
    def _handle_aide(self, message):
        """Gestion des demandes d'aide"""
        aide_messages = {
            'admin': (
                "🆘 Aide Administrateur\n\n"
                "Je peux vous aider avec :\n"
                "✅ Voir les chambres disponibles\n"
                "✅ Consulter les prix\n"
                "✅ Gérer les réservations\n"
                "✅ Obtenir des statistiques\n"
                "✅ Naviguer dans l'application\n\n"
                "Posez-moi n'importe quelle question !"
            ),
            'employe': (
                "🆘 Aide Employé\n\n"
                "Je peux vous assister avec :\n"
                "✅ Voir les chambres disponibles\n"
                "✅ Créer des réservations\n"
                "✅ Consulter les informations clients\n"
                "✅ Naviguer dans l'application\n\n"
                "N'hésitez pas à demander !"
            ),
            'client': (
                "🆘 Aide Client\n\n"
                "Je peux vous aider avec :\n"
                "✅ Voir les chambres disponibles\n"
                "✅ Consulter les prix\n"
                "✅ Comprendre comment réserver\n"
                "✅ Voir vos réservations\n\n"
                "Posez-moi votre question !"
            ),
        }
        
        return {
            'success': True,
            'message': aide_messages.get(self.role, "Comment puis-je vous aider ?")
        }
    
    def _handle_fonctionnalite(self, message):
        """Explique une fonctionnalité"""
        response = (
            "💡 Fonctionnalités principales :\n\n"
            "🔹 Dashboard : Vue d'ensemble et statistiques\n"
            "🔹 Clients : Gestion des informations clients\n"
            "🔹 Chambres : Gestion des chambres et disponibilités\n"
            "🔹 Réservations : Création et suivi des réservations\n\n"
            "Quelle fonctionnalité souhaitez-vous découvrir ?"
        )
        
        return {
            'success': True,
            'message': response
        }
    
    def _handle_navigation(self, message):
        """Aide à la navigation"""
        if 'client' in message:
            response = "👥 Pour accéder aux clients : Menu 'Clients' en haut à gauche."
        elif 'chambre' in message:
            response = "🛏️ Pour accéder aux chambres : Menu 'Chambres' en haut."
        elif 'reservation' in message or 'résa' in message:
            response = "📅 Pour accéder aux réservations : Menu 'Réservations' en haut."
        else:
            response = "🧭 Utilisez le menu de navigation en haut de la page pour accéder aux différentes sections."
        
        return {
            'success': True,
            'message': response
        }
    
    def _handle_compte(self, message):
        """Gestion du compte utilisateur"""
        response = (
            f"👤 Votre compte : {self.user.username}\n"
            f"📧 Email : {self.user.email}\n"
            f"🎭 Rôle : {self.role.capitalize()}\n\n"
            "💡 Pour modifier vos informations, contactez un administrateur."
        )
        
        return {
            'success': True,
            'message': response
        }
    
    def _handle_date(self, message):
        """Donne la date actuelle"""
        today = date.today()
        jour_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][today.weekday()]
        
        response = f"📅 Nous sommes le {jour_semaine} {today.strftime('%d/%m/%Y')}."
        
        return {
            'success': True,
            'message': response
        }
    
    def _handle_unknown(self, message):
        """Gestion des questions non comprises"""
        suggestions = [
            "💡 Essayez de demander :",
            "• 'Quelles chambres sont disponibles ?'",
            "• 'Quel est le prix d'une chambre double ?'",
            "• 'Comment faire une réservation ?'",
            "• Ou tapez 'aide' pour plus d'options",
        ]
        
        return {
            'success': True,
            'message': "🤔 Je n'ai pas bien compris votre question.\n\n" + "\n".join(suggestions)
        }


# Compatibilité : nom attendu par la vue
HotelChatbot = HotelChatbotAI


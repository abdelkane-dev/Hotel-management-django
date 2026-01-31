# 🏨 Hotel Management System

Une application web complète de gestion hôtelière développée avec Django, conçue pour gérer les réservations, les clients, les chambres, le personnel et la facturation.

## 📋 Table des matières

- [Présentation](#-présentation)
- [Fonctionnalités](#-fonctionnalités)
- [Technologies](#-technologies)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Structure du projet](#-structure-du-projet)
- [Utilisation](#-utilisation)
- [Rôles et permissions](#-rôles-et-permissions)
- [Scripts utilitaires](#-scripts-utilitaires)
- [API](#-api)
- [Développement](#-développement)
- [Tests](#-tests)
- [Déploiement](#-déploiement)
- [Contributions](#-contributions)
- [Licence](#-licence)

## 🎯 Présentation

Ce système de gestion hôtelière offre une solution complète pour la gestion quotidienne d'un hôtel, avec une interface moderne et intuitive pour différents types d'utilisateurs :

- **Administrateurs** : Gestion complète de l'hôtel
- **Employés** : Gestion des réservations et des clients
- **Clients** : Réservation en ligne et suivi de leurs séjours

## ✨ Fonctionnalités

### 🏠 Gestion des chambres
- Création et modification des chambres
- Gestion des types de chambre (simple, double, suite, etc.)
- Suivi du statut des chambres (disponible, occupée, en maintenance)
- Gestion des tarifs et promotions

### 👥 Gestion des clients
- Création de comptes clients
- Suivi des informations personnelles
- Historique des réservations
- Gestion des préférences

### 📅 Gestion des réservations
- Système de réservation en temps réel
- Vérification automatique de disponibilité
- Gestion des annulations et modifications
- Calendrier de réservation interactif

### 💰 Facturation et paiement
- Génération automatique des factures
- Suivi des paiements
- Gestion des taxes et frais supplémentaires
- Export des factures en PDF

### 📊 Tableaux de bord
- Vue d'ensemble des activités
- Statistiques et rapports
- Indicateurs de performance clés
- Graphiques et visualisations

### 🤖 Assistant IA
- Chatbot intégré pour l'assistance client
- Réponses automatiques aux questions fréquentes
- Support multilingue
- Configuration admin du comportement de l'IA
- Historique des interactions avec l'IA

### 🔧 Gestion de la maintenance
- Création de demandes de maintenance
- Suivi des statuts (en attente, en cours, terminé)
- Affectation d'articles d'inventaire aux tâches
- Historique des interventions
- Rapports de maintenance

### 📦 Gestion de l'inventaire
- Catalogue d'articles avec catégories
- Suivi des quantités disponibles
- Gestion des mouvements (entrée, sortie, affectation)
- Alertes de stock bas
- Export des données d'inventaire

### 💬 Messagerie et notifications
- Système de messages de contact client
- Notifications admin en temps réel
- Gestion des statuts de messages
- Réponses directes aux clients
- Historique des communications

### 📊 Gestion comptable avancée
- Factures client détaillées
- Fiches de paie employés
- Charges comptables diverses
- Export CSV et PDF
- Rapports mensuels automatisés

### 📅 Calendrier et planification
- Vue calendrier des réservations
- Planification des interventions
- Gestion des disponibilités
- Vue timeline des activités

### 👥 Gestion du personnel
- Création et gestion des employés
- Historique des modifications (promotion, salaire)
- Gestion des rôles et permissions
- Terminations de contrat
- Suivi des performances

### 🔐 Gestion des utilisateurs
- Système d'authentification sécurisé
- Gestion des rôles et permissions
- Profil utilisateur personnalisable

## 🛠 Technologies

### Backend
- **Django 6.0+** : Framework web principal
- **Python 3.8+** : Langage de programmation
- **SQLite** : Base de données (développement)
- **PostgreSQL** : Base de données (production recommandée)

### Frontend
- **HTML5/CSS3** : Structure et style
- **JavaScript** : Interactivité
- **Bootstrap 5** : Framework CSS
- **Widget Tweaks** : Amélioration des formulaires Django

### Outils et bibliothèques
- **Pillow** : Traitement d'images
- **WeasyPrint** : Génération de PDF
- **Django Humanize** : Formatage des nombres
- **Django Messages** : Gestion des notifications

## 🚀 Démarrage rapide

### Pour accéder rapidement au site

1. **Ouvrir un terminal** dans le dossier du projet
2. **Activer l'environnement virtuel** (si créé) :
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Démarrer le serveur** :
   ```bash
   python manage.py runserver
   ```

4. **Ouvrir le navigateur** et aller à : `http://127.0.0.1:8000/`

5. **Se connecter** avec les identifiants de test (voir section "Identifiants de test")

### Options de démarrage avancées

#### Spécifier un port personnalisé
```bash
python manage.py runserver 8080
# Accès : http://127.0.0.1:8080/
```

#### Autoriser les connexions depuis d'autres appareils
```bash
python manage.py runserver 0.0.0.0:8000
# Accès depuis autres appareils : http://VOTRE_IP:8000/
```

#### Mode développement avec rechargement automatique
```bash
python manage.py runserver --settings=hotel_management.settings
```

### Vérification du démarrage

Le serveur est démarré avec succès quand vous voyez :
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
Django version 6.0.1, using settings 'hotel_management.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-C.
```

## 🛠 Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git

### Étapes d'installation

1. **Cloner le dépôt**
   ```bash
   git clone <URL_DU_DEPOT>
   cd webapp
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Appliquer les migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

6. **Créer les données de test (optionnel)**
   ```bash
   python create_sample_data.py
   python create_users_roles.py
   python create_factures_existantes.py
   ```

7. **Démarrer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

8. **Accéder à l'application**
   - Ouvrez votre navigateur web
   - Allez à l'adresse : `http://127.0.0.1:8000/`
   - Utilisez les identifiants de test fournis dans la section "Identifiants de test"

L'application sera accessible à l'adresse `http://127.0.0.1:8000/`

## ⚙️ Configuration

### Variables d'environnement
Créez un fichier `.env` à la racine du projet :

```env
SECRET_KEY=votre_clé_secrète_ici
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Configuration de la base de données
Pour la production, modifiez `hotel_management/settings.py` :

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hotel_db',
        'USER': 'votre_utilisateur',
        'PASSWORD': 'votre_mot_de_passe',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Fichiers statiques et médias
```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

## 📁 Structure du projet

```
webapp/
├── hotel_management/          # Configuration du projet Django
│   ├── __init__.py
│   ├── settings.py           # Configuration principale
│   ├── urls.py               # URLs principales
│   ├── asgi.py              # Configuration ASGI
│   └── wsgi.py              # Configuration WSGI
├── hotel/                    # Application principale
│   ├── models.py             # Modèles de données
│   ├── views.py              # Vues principales
│   ├── views_billing.py      # Vues de facturation
│   ├── views_inventory.py    # Vues de gestion
│   ├── urls.py               # URLs de l'application
│   ├── forms.py              # Formulaires
│   ├── admin.py              # Administration Django
│   ├── permissions.py        # Gestion des permissions
│   ├── decorators.py         # Décorateurs personnalisés
│   ├── middleware.py         # Middleware personnalisé
│   ├── utils.py              # Fonctions utilitaires
│   ├── signals.py            # Signaux Django
│   ├── constants.py          # Constantes
│   ├── chatbot_ai.py         # Chatbot IA
│   ├── context_processors.py # Context processors
│   ├── migrations/           # Migrations de base de données
│   ├── management/           # Commandes de gestion
│   ├── static/               # Fichiers statiques
│   └── templates/            # Templates HTML
├── scripts/                  # Scripts utilitaires
│   ├── check_reports.py
│   ├── check_urls.py
│   ├── render_maintenance_template.py
│   └── test_inventory_view.py
├── requirements.txt          # Dépendances Python
├── manage.py                # Script de gestion Django
├── create_sample_data.py    # Script de création de données
├── create_users_roles.py    # Script de création d'utilisateurs
├── create_factures_existantes.py # Script de création de factures
└── README.md                # Documentation
```

## 🎮 Utilisation

### Connexion
1. Accédez à `http://127.0.0.1:8000/`
2. Utilisez les identifiants de test ci-dessous selon votre rôle

### Identifiants de test

#### 👨‍💼 Administrateur
- **Email** : `admin@hotel.com`
- **Mot de passe** : `admin123`
- **Permissions** : Accès complet à toutes les fonctionnalités

#### 👨‍🔧 Employé
- **Email** : `employe@hotel.com`
- **Mot de passe** : `employe123`
- **Permissions** : Gestion des réservations, clients et factures

#### 👤 Client
- **Email** : `client@hotel.com`
- **Mot de passe** : `client123`
- **Permissions** : Réservation en ligne et suivi personnel

#### 🤖 Compte de test supplémentaire
- **Email** : `test@hotel.com`
- **Mot de passe** : `test123`
- **Permissions** : Client avec données de test

> **Note** : Ces comptes sont créés automatiquement lors de l'exécution du script `create_users_roles.py`. Si vous utilisez le superutilisateur créé manuellement, ses identifiants seront ceux que vous avez définis lors de la création.

### Navigation
- **Tableau de bord** : Vue d'ensemble selon votre rôle
- **Gestion des chambres** : Administration des chambres
- **Réservations** : Création et gestion des réservations
- **Clients** : Gestion de la clientèle
- **Facturation** : Gestion des factures et paiements
- **Rapports** : Statistiques et rapports

### Interface client
Les clients peuvent :
- Consulter les chambres disponibles
- Effectuer des réservations en ligne
- Suivre leurs réservations
- Contacter l'hôtel

## 👥 Rôles et permissions

### Administrateur
- Accès complet à toutes les fonctionnalités
- Gestion des utilisateurs et permissions
- Configuration du système
- Accès aux rapports et statistiques

### Employé
- Gestion des réservations
- Gestion des clients
- Accès aux informations de chambres
- Gestion des factures

### Client
- Réservation en ligne
- Consultation de son profil
- Suivi de ses réservations
- Contact avec l'hôtel

## 🔧 Scripts utilitaires

### Scripts de données
- `create_sample_data.py` : Crée des données de démonstration
- `create_users_roles.py` : Crée des utilisateurs avec différents rôles
- `create_factures_existantes.py` : Génère des factures d'exemple

### Scripts de maintenance
- `check_reports.py` : Vérifie l'état des rapports
- `check_urls.py` : Teste les URLs de l'application
- `render_maintenance_template.py` : Génère une page de maintenance
- `test_inventory_view.py` : Teste les vues de gestion

### Exécution des scripts
```bash
python nom_du_script.py
```

## 🌐 API

L'application expose plusieurs endpoints API :

### Réservations
- `GET /api/check-disponibilite/` : Vérifier la disponibilité
- `POST /api/creer-reservation/` : Créer une réservation
- `GET /api/chambres-disponibles/` : Lister les chambres disponibles

### Clients
- `GET /client/reservations/<id>/details/` : Détails d'une réservation
- `PUT /client/reservations/<id>/modify/` : Modifier une réservation
- `DELETE /client/reservations/<id>/cancel/` : Annuler une réservation

### API Complète

#### 🔐 Authentification
- `POST /login/` : Connexion utilisateur
- `POST /logout/` : Déconnexion
- `POST /signup/` : Inscription client

#### 📅 Réservations
- `GET /api/check-disponibilite/` : Vérifier la disponibilité
- `POST /api/creer-reservation/` : Créer une réservation
- `GET /api/chambres-disponibles/` : Lister les chambres disponibles
- `GET /client/reservations/<id>/details/` : Détails d'une réservation
- `PUT /client/reservations/<id>/modify/` : Modifier une réservation
- `DELETE /client/reservations/<id>/cancel/` : Annuler une réservation

#### 🤖 Chatbot IA
- `POST /api/chatbot/` : Interagir avec le chatbot

#### 📊 Statistiques et rapports
- `GET /billing/api/stats/` : Statistiques de facturation
- `GET /inventory/api/stats/` : Statistiques d'inventaire

#### 💬 Notifications
- `GET /management/notifications/` : Lister les notifications
- `PUT /management/notifications/<id>/lue/` : Marquer comme lue
- `PUT /management/notifications/<id>/traitee/` : Marquer comme traitée

### 🏗️ Architecture des modèles de données

#### Modèles principaux
- **Client** : Informations personnelles et coordonnées
- **Chambre** : Types, prix, équipements, images
- **Reservation** : Liaison client-chambre avec dates
- **UserProfile** : Extension du modèle User avec rôles
- **Facture** : Facturation client automatique
- **FichePaie** : Gestion des salaires employés

#### Modèles de gestion
- **Maintenance** : Demandes et suivi des interventions
- **InventoryItem** : Articles d'inventaire avec quantités
- **InventoryMovement** : Mouvements de stock
- **ContactMessage** : Messages clients
- **Notification** : Notifications admin
- **AgentIAConfig** : Configuration du chatbot

### 🎨 Templates et interfaces

#### Interfaces principales
- **Base templates** : Structure HTML réutilisable
- **Dashboards** : Interfaces par rôle (admin, employé, client)
- **Forms** : Formulaires CRUD pour tous les modèles
- **Lists** : Vues listes avec filtres et recherche

#### Interfaces spécialisées
- **Billing** : Facturation, fiches de paie, charges
- **Inventory** : Gestion d'inventaire avancée
- **Calendar** : Vue calendrier des réservations
- **Reports** : Rapports et statistiques
- **Admin** : Administration système

### 🔐 Système de permissions

#### Rôles définis
- **ADMIN** : Accès complet à toutes les fonctionnalités
- **EMPLOYE** : Gestion des opérations quotidiennes
- **CLIENT** : Accès limité à ses propres données

#### Permissions par vue
- **@admin_required** : Restreint aux administrateurs
- **@employe_required** : Restreint aux employés et admins
- **@client_required** : Restreint aux clients
- **Permissions personnalisées** : Vérifications granulaires

## 🧪 Tests

### Exécution des tests
```bash
# Tests de l'application
python manage.py test

# Tests spécifiques
python manage.py test hotel.tests

# Tests avec couverture
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Tests manuels
Les scripts dans le dossier `scripts/` permettent de tester des fonctionnalités spécifiques.

## 🚀 Déploiement

### Production
1. **Configuration**
   - Mettre `DEBUG = False`
   - Configurer `ALLOWED_HOSTS`
   - Utiliser une base de données PostgreSQL
   - Configurer les variables d'environnement

2. **Fichiers statiques**
   ```bash
   python manage.py collectstatic
   ```

3. **Serveur WSGI**
   Utiliser Gunicorn ou uWSGI :
   ```bash
   pip install gunicorn
   gunicorn hotel_management.wsgi:application
   ```

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "hotel_management.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🔧 Développement

### Conventions de code
- PEP 8 pour le style Python
- Commentaires en français
- Noms de variables en français
- Documentation complète des fonctions

### Nouvelles fonctionnalités
1. Créer les modèles dans `hotel/models.py`
2. Ajouter les vues dans `hotel/views.py`
3. Configurer les URLs dans `hotel/urls.py`
4. Créer les templates dans `hotel/templates/`
5. Ajouter les tests dans `hotel/tests.py`

### Migration de base de données
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🤝 Contributions

### Processus de contribution
1. Forker le projet
2. Créer une branche de fonctionnalité
3. Commiter les changements
4. Pousser vers le fork
5. Créer une Pull Request

### Normes de contribution
- Code respectant PEP 8
- Tests pour les nouvelles fonctionnalités
- Documentation mise à jour
- Messages de commit clairs

## 📝 Notes importantes

### Sécurité
- Changer la clé secrète en production
- Utiliser HTTPS en production
- Valider toutes les entrées utilisateur
- Maintenir les dépendances à jour

### Performance
- Optimiser les requêtes de base de données
- Utiliser le cache Django
- Compresser les fichiers statiques
- Surveiller les performances

### Sauvegarde
- Sauvegarder régulièrement la base de données
- Sauvegarder les fichiers médias
- Tester les restaurations

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Pour toute question ou problème :
- Créer une issue sur GitHub
- Contacter l'équipe de développement
- Consulter la documentation Django

---

**Système de gestion hôtelière moderne**

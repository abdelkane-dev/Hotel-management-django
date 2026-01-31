
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Chambre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=10, unique=True, verbose_name='Numéro de chambre')),
                ('type_chambre', models.CharField(choices=[('simple', 'Chambre Simple'), ('double', 'Chambre Double'), ('suite', 'Suite')], max_length=20, verbose_name='Type de chambre')),
                ('prix_par_nuit', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Prix par nuit (€)')),
                ('capacite', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Capacité (nombre de personnes)')),
                ('statut', models.CharField(choices=[('libre', 'Libre'), ('occupee', 'Occupée'), ('maintenance', 'En maintenance')], default='libre', max_length=20, verbose_name='Statut')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('climatisation', models.BooleanField(default=True, verbose_name='Climatisation')),
                ('wifi', models.BooleanField(default=True, verbose_name='WiFi')),
                ('television', models.BooleanField(default=True, verbose_name='Télévision')),
                ('minibar', models.BooleanField(default=False, verbose_name='Minibar')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('derniere_modification', models.DateTimeField(auto_now=True, verbose_name='Dernière modification')),
            ],
            options={
                'verbose_name': 'Chambre',
                'verbose_name_plural': 'Chambres',
                'ordering': ['numero'],
            },
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name='Nom')),
                ('prenom', models.CharField(max_length=100, verbose_name='Prénom')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('telephone', models.CharField(max_length=20, verbose_name='Téléphone')),
                ('numero_piece_identite', models.CharField(max_length=50, unique=True, verbose_name="Numéro de pièce d'identité")),
                ('adresse', models.TextField(verbose_name='Adresse complète')),
                ('ville', models.CharField(max_length=100, verbose_name='Ville')),
                ('pays', models.CharField(max_length=100, verbose_name='Pays')),
                ('date_inscription', models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")),
                ('derniere_modification', models.DateTimeField(auto_now=True, verbose_name='Dernière modification')),
            ],
            options={
                'verbose_name': 'Client',
                'verbose_name_plural': 'Clients',
                'ordering': ['-date_inscription'],
            },
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_entree', models.DateField(verbose_name="Date d'entrée")),
                ('date_sortie', models.DateField(verbose_name='Date de sortie')),
                ('nombre_nuits', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Nombre de nuits')),
                ('prix_total', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Prix total (€)')),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('confirmee', 'Confirmée'), ('en_cours', 'En cours'), ('terminee', 'Terminée'), ('annulee', 'Annulée')], default='en_attente', max_length=20, verbose_name='Statut')),
                ('nombre_personnes', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Nombre de personnes')),
                ('remarques', models.TextField(blank=True, null=True, verbose_name='Remarques')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('derniere_modification', models.DateTimeField(auto_now=True, verbose_name='Dernière modification')),
                ('chambre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='hotel.chambre', verbose_name='Chambre')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='hotel.client', verbose_name='Client')),
                ('cree_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
            ],
            options={
                'verbose_name': 'Réservation',
                'verbose_name_plural': 'Réservations',
                'ordering': ['-date_creation'],
            },
        ),
    ]

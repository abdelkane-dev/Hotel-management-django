from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Initialise les groupes et permissions de base pour l\'application hotel'

    def handle(self, *args, **options):
        # Mapping de modèles pour lesquels créer des permissions
        # Les permissions Django standard (add, change, delete, view)
        from hotel.models import Client, Chambre, Reservation, UserProfile, EmployeeHistory

        model_map = {
            'client': Client,
            'chambre': Chambre,
            'reservation': Reservation,
            'userprofile': UserProfile,
            'employeehistory': EmployeeHistory,
        }

        def get_perms_for(model_key, perms=None):
            model = model_map[model_key]
            ct = ContentType.objects.get_for_model(model)
            if perms is None:
                perms = ['add', 'change', 'delete', 'view']
            perm_objs = []
            for p in perms:
                codename = f"{p}_{model_key}"
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    perm_objs.append(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Permission {codename} non trouvée"))
            return perm_objs

        # Création des groupes
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        employe_group, _ = Group.objects.get_or_create(name='Employe')
        client_group, _ = Group.objects.get_or_create(name='Client')

        # Admin : donner toutes les permissions sur les modèles principaux
        all_perms = []
        for key in model_map.keys():
            all_perms.extend(get_perms_for(key))
        admin_group.permissions.set(all_perms)

        # Employé : accès en lecture pour clients & chambres, CRUD limité pour réservations
        emp_perms = []
        emp_perms.extend(get_perms_for('client', perms=['view']))
        emp_perms.extend(get_perms_for('chambre', perms=['view']))
        emp_perms.extend(get_perms_for('reservation', perms=['add', 'change', 'view']))
        employe_group.permissions.set(emp_perms)

        # Client : voir chambres, ajouter réservations, voir ses réservations (gestion d'objet en views)
        cli_perms = []
        cli_perms.extend(get_perms_for('chambre', perms=['view']))
        cli_perms.extend(get_perms_for('reservation', perms=['add', 'view']))
        client_group.permissions.set(cli_perms)

        self.stdout.write(self.style.SUCCESS('Groupes et permissions initialisés : Admin, Employe, Client'))
        self.stdout.write('Instructions :\n - Ajoutez des utilisateurs aux groupes via l\'admin ou en script.\n - Pour les contrôles d\'accès object-level (ex : un client ne voit que ses réservations),\n   appliquez des filtres dans les vues (ex: Reservation.objects.filter(user=request.user)).')

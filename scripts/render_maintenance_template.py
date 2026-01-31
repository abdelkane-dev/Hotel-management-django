import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_management.settings')
import django
django.setup()
from django.template.loader import render_to_string
from hotel.forms import MaintenanceForm
from django.contrib.auth import get_user_model
User = get_user_model()

# create a dummy user
user = User.objects.filter(is_staff=True).first()
if not user:
    user = User.objects.create_superuser('tmpadmin', 'tmp@local', 'password')

html = render_to_string('hotel/maintenance_form.html', {'form': MaintenanceForm(), 'user': user})
print('Rendered length:', len(html))
print(html[:1000])

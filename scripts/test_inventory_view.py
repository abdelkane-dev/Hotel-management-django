import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','hotel_management.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

# Ensure superuser exists
username = 'testadmin'
password = 'password123'
user, created = User.objects.get_or_create(username=username, defaults={'is_staff': True, 'is_superuser': True, 'email': 'admin@example.com'})
if created:
    user.set_password(password)
    user.save()
    print('Superuser created')
else:
    print('Superuser exists')

c = Client()
logged_in = c.login(username=username, password=password)
print('Logged in:', logged_in)

try:
    resp = c.get('/inventory/new/')
    print('Status code:', resp.status_code)
    print('Redirected:', resp.url if resp.status_code in (301,302) else '')
    print('Content snippet:')
    print(resp.content.decode('utf-8')[:1000])
except Exception as e:
    import traceback
    traceback.print_exc()

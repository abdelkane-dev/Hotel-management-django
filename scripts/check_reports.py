import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','hotel_management.settings')
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
u = User.objects.filter(is_superuser=True).first()
if not u:
    u = User.objects.create_superuser('tmpadmin','tmp@local','pass')

c = Client()
c.force_login(u)
r = c.get('/reports/')
print('status', r.status_code)
print('content snippet:\n')
print(r.content.decode('utf-8')[:4000])

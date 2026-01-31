import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','hotel_management.settings')
import django
django.setup()
from django.urls import reverse
print('admin_notifications ->', reverse('admin_notifications'))
print('agent_ia_dashboard ->', reverse('agent_ia_dashboard'))
print('notification_marquer_lue ->', reverse('notification_marquer_lue', kwargs={'notification_id':1}))

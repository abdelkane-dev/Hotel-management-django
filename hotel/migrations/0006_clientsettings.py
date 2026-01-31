# Generated manually to add ClientSettings model
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0005_inventorycategory_alter_employeehistory_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(choices=[('fr', 'Français'), ('en', 'English'), ('es', 'Español'), ('de', 'Deutsch')], default='fr', max_length=10)),
                ('timezone', models.CharField(default='Europe/Paris', max_length=64)),
                ('currency', models.CharField(default='EUR', max_length=10)),
                ('theme', models.CharField(choices=[('light', 'Clair'), ('dark', 'Sombre'), ('auto', 'Automatique')], default='light', max_length=10)),
                ('font_size', models.CharField(choices=[('small', 'Petite'), ('medium', 'Moyenne'), ('large', 'Grande')], default='medium', max_length=10)),
                ('two_factor', models.BooleanField(default=False)),
                ('login_alerts', models.BooleanField(default=True)),
                ('email_reservations', models.BooleanField(default=True)),
                ('email_promotions', models.BooleanField(default=False)),
                ('email_newsletter', models.BooleanField(default=False)),
                ('public_profile', models.BooleanField(default=False)),
                ('data_sharing', models.BooleanField(default=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('user_profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='hotel.userprofile')),
            ],
            options={
                'verbose_name': 'Paramètres Client',
                'verbose_name_plural': 'Paramètres Clients',
            },
        ),
    ]

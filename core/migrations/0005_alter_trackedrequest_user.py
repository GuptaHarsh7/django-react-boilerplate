# Generated by Django 3.2.4 on 2021-06-12 09:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_trackedrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trackedrequest',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]

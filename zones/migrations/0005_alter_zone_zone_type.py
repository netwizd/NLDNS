# Generated by Django 5.1.6 on 2025-02-26 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zones', '0004_remove_zone_master_ip_zone_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zone',
            name='zone_type',
            field=models.CharField(choices=[('master', 'Master'), ('slave', 'Slave'), ('forward', 'Forward(Cache)'), ('redirect', 'Redirect(NoCache)')], default='master', max_length=10),
        ),
    ]

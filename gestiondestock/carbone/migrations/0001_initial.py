# Generated by Django 5.2 on 2025-05-25 14:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0005_demandearticle'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmissionArticle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facteur_co2', models.FloatField(blank=True, default=0, null=True)),
                ('source', models.CharField(default='ADEME', max_length=100)),
                ('article', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='carbone_info', to='inventory.article')),
            ],
        ),
    ]

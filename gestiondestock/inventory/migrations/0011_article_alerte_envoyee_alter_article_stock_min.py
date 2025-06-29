# Generated by Django 5.2 on 2025-05-31 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0010_alter_customuser_secondary_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='alerte_envoyee',
            field=models.BooleanField(default=False, help_text='Devient True dès qu’un mail d’alerte a été envoyé (pour éviter les envois multiples)'),
        ),
        migrations.AlterField(
            model_name='article',
            name='stock_min',
            field=models.PositiveIntegerField(default=1, help_text="Seuil minimal en stock à partir duquel on considère l'article comme critique"),
        ),
    ]

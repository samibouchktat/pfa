from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import datetime 
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
import string
from datetime import timedelta

# ✅ Utilisateur personnalisé avec rôles
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('gestionnaire', 'Gestionnaire de stock'),
        ('employe', 'Employé'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Le numéro de téléphone facultatif
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# ✅ Fournisseur
class Fournisseur(models.Model):
    nom = models.CharField(max_length=100)
    contact = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)  # Assure-toi que ce champ existe

    def __str__(self):
        return self.nom

# ✅ Article
class Article(models.Model):
    nom = models.CharField(max_length=100)
    reference = models.CharField(max_length=100, unique=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    categorie = models.CharField(max_length=100, default='electronique')  # Catégorie par défaut

    description = models.TextField(blank=True, null=True)  # Description optionnelle
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.reference})"

    def update_stock(self):
        """Méthode pour obtenir la quantité en stock"""
        stock_entries = Stock.objects.filter(article=self, entree__isnull=False)
        stock_out = Stock.objects.filter(article=self, sortie__isnull=False)
        total_stock = sum([entry.entree for entry in stock_entries]) - sum([out.sortie for out in stock_out])
        return total_stock

# ✅ Commande
class Commande(models.Model):
    date = models.DateField(auto_now_add=True)
    etat = models.CharField(max_length=100)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.CASCADE)
    employe = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'employe'})

    def __str__(self):
        return f"Commande {self.id} - {self.etat}"

    def total_price(self):
        """Calcul du prix total de la commande"""
        total = 0
        for article in self.articles_commande.all():
            total += article.quantite * article.article.prix
        return total

# ✅ Articles dans une commande
class Avoir(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='articles_commande')
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantite} x {self.article.nom} (Commande {self.commande.id})"

# ✅ Mouvements de stock
class Stock(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    entree = models.PositiveIntegerField(null=True, blank=True)
    sortie = models.PositiveIntegerField(null=True, blank=True)
    date_entree = models.DateField(null=True, blank=True)
    date_sortie = models.DateField(null=True, blank=True)
    etat = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.article.nom} - État : {self.etat}"

# ✅ Rapport généré par un admin
class Rapport(models.Model):
    titre = models.CharField(max_length=100)
    date_creation = models.DateField(auto_now_add=True)
    contenu = models.TextField()
    auteur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'})

    def __str__(self):
        return f"{self.titre} - {self.date_creation}"

# ✅ Message entre utilisateurs
class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"

# ✅ Code de vérification 2FA
class TwoFactorCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Utilisation de AUTH_USER_MODEL
    code = models.CharField(max_length=6)
    expiration_time = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expiration_time

    @staticmethod
    def generate_code():
        """Génère un code aléatoire de 6 chiffres"""
        return ''.join(random.choices(string.digits, k=6))

    @classmethod
    def create_code(cls, user):
        """Créer un code de validation et définir une expiration"""
        code = cls.generate_code()
        expiration_time = timezone.now() + timedelta(minutes=10)  # Le code expire après 10 minutes
        return cls.objects.create(user=user, code=code, expiration_time=expiration_time)



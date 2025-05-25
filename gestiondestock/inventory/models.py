from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import random, string
from datetime import timedelta
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User

# Utilisateur personnalisé avec rôles
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('gestionnaire', 'Gestionnaire de stock'),
        ('employe', 'Employé'),
        ('fournisseur', 'Fournisseur'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    secondary_email = models.EmailField("Email secondaire (2FA)", blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
# Fournisseur
class Fournisseur(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE,
        limit_choices_to={'role': 'fournisseur'},
        related_name='fournisseur_profile',
        null=True, blank=True  # ← autorise les fournisseurs sans user
    )
    nom     = models.CharField(max_length=100)
    contact = models.CharField(max_length=20)
    email   = models.EmailField(unique=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nom


# Article
class Article(models.Model):
    nom       = models.CharField(max_length=200)
    reference = models.CharField(max_length=100, unique=True)
    prix      = models.DecimalField(max_digits=10, decimal_places=2)
    quantite  = models.IntegerField(default=0, help_text="Quantité réelle en stock")
    stock     = models.IntegerField(default=0, help_text="Stock calculé ou ajusté manuellement")
    description = models.TextField(blank=True, default="")
    facteur_co2 = models.FloatField(
        default=0.0,
        verbose_name="Facteur d'émission CO₂ (kg/unit)",
        help_text="Renseigne le facteur d’émission de CO₂ pour ce produit (ADEME ou estimation, en kg par unité)"
    )
    stock_min = models.PositiveIntegerField(default=1)
    def __str__(self):
        return f"{self.nom} ({self.reference})"
    def update_stock(self):
        """
        Calcule le stock actuel à partir des mouvements liés.
        """
        total = sum(
            entry.entree - entry.sortie
            for entry in self.stock_entries.all()
        )
        return total

# Mouvements de stock
class Stock(models.Model):
    article      = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='stock_entries')
    entree       = models.IntegerField(default=0)
    sortie       = models.IntegerField(default=0)
    date_entree  = models.DateField(null=True, blank=True)
    date_sortie  = models.DateField(null=True, blank=True)
    etat         = models.CharField(max_length=100)
    description  = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Mvt {self.id}: {self.article.nom} +{self.entree}/-{self.sortie}"

# Commande et détails
class Commande(models.Model):
    date       = models.DateField(auto_now_add=True)
    etat       = models.CharField(max_length=100)
    fournisseur= models.ForeignKey(Fournisseur, on_delete=models.CASCADE)
    employe    = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'employe'})

    def __str__(self):
        return f"Commande {self.id} - {self.etat}"

    def total_price(self):
        return sum(
            avoir.quantite * avoir.article.prix
            for avoir in self.articles_commande.all()
        )

class Avoir(models.Model):
    
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='articles_commande')
    article  = models.ForeignKey(Article, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantite} x {self.article.nom} (Cmd {self.commande.id})"

# Rapport IA
class Rapport(models.Model):
    titre         = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True)
    contenu       = models.TextField()
    auteur        = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'})

    def __str__(self):
        return f"{self.titre} ({self.date_creation.date()})"

# Messagerie interne
class Message(models.Model):
    sender    = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver  = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    content   = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"

# 2FA
class TwoFactorCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expiration_time = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and self.expiration_time > timezone.now()

    def is_expired(self):
        return timezone.now() > self.expiration_time

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))

    @classmethod
    def create_code(cls, user):
        code = cls.generate_code()
        expiration_time = timezone.now() + timedelta(minutes=10)
        return cls.objects.create(user=user, code=code, expiration_time=expiration_time)
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone   = models.CharField("Téléphone", max_length=20, blank=True)
    address = models.TextField("Adresse", blank=True)

    def __str__(self):
        return f"{self.user.username} — Profil"



@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class MouvementStock(models.Model):
    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    motif = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.type_mouvement == 'entree':
            self.article.stock += self.quantite
        elif self.type_mouvement == 'sortie':
            if self.quantite > self.article.stock:
                raise ValueError("Stock insuffisant")
            self.article.stock -= self.quantite
        self.article.save()
        super().save(*args, **kwargs)
class DemandeArticle(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuvee', 'Approuvée'),
        ('refusee', 'Refusée'),
    ]

    employe = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'employe'})
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    # Si tu as un modèle Categorie, garde-le, sinon retire ce champ :
    date_demande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    def __str__(self):
        return f"{self.article.nom} ({self.quantite}) par {self.employe.username}"


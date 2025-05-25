# inventory/forms.py
from django import forms
from django.forms import modelformset_factory
from .models import Article, Fournisseur, Commande, Avoir, CustomUser
from .utils import envoyer_sms  # Fonction d'envoi 
from .models import UserProfile
from django.forms.models import BaseInlineFormSet
from .models import Commande, Avoir
from django import forms
from django.contrib.auth import get_user_model
from .models import Fournisseur
from django import forms
from .models import MouvementStock
from .models import DemandeArticle 


# Formulaire Article
class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        # Spécifie explicitement les champs existants
        fields = ['nom', 'reference', 'description', 'prix', 'quantite']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du produit'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Référence'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Description',
                'rows': 3
            }),
            'prix': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prix (€)',
                'step': '0.01',
                'min': '0'
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quantité',
                'min': '0'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stock',
                'min': '0'
            }),
        }

# Formulaire Fournisseur
class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['etat', 'fournisseur', 'employe']

class AvoirForm(forms.ModelForm):
    class Meta:
        model = Avoir
        fields = ['article', 'quantite']
# Formset Avoir
AvoirFormSet = modelformset_factory(Avoir, fields='__all__')

# CompleteProfileForm pour le numéro de téléphone
class CompleteProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control highlight-yellow',
                'placeholder': 'Votre numéro de téléphone'
            }),
        }

    def clean_phone_number(self):
        # Validation du numéro de téléphone
        return self.cleaned_data.get('phone_number')

# Formulaire simple si nécessaire
class ProfilForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control highlight-yellow',
            'placeholder': 'Votre numéro de téléphone'
        })
    )
    class BaseAvoirFormSet(BaseInlineFormSet):
        def clean(self):
            super().clean()
            for form in self.forms:
                       if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                             continue
            article = form.cleaned_data['article']
            qty     = form.cleaned_data['quantite']
            if qty > article.quantite:
                form.add_error('quantite',
                    f"Quantité maximale disponible : {article.quantite}")


class BaseAvoirFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            article = form.cleaned_data['article']
            qty     = form.cleaned_data['quantite']
            if qty > article.quantite:
                form.add_error('quantite',
                    f"Quantité maximale disponible : {article.quantite}")

from django import forms

class EmailVerificationForm(forms.Form):
    email = forms.EmailField(label="Votre adresse e-mail", max_length=254)

class OTPVerificationForm(forms.Form):
    code = forms.CharField(label="Code de vérification", max_length=6)

class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'contact', 'email', 'adresse']

User = get_user_model()

class FournisseurUserForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=150)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    email = forms.EmailField(label="Email")
    nom = forms.CharField(label="Nom du fournisseur", max_length=100)
    contact = forms.CharField(label="Contact", max_length=20)
    adresse = forms.CharField(label="Adresse", max_length=255, required=False)

class MouvementStockForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['article', 'quantite', 'motif']
class DemandeArticleForm(forms.ModelForm):
     class Meta:
            model = DemandeArticle
            fields = ['article', 'quantite']
class MouvementForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['article', 'quantite', 'motif']  # ← Mets ici UNIQUEMENT les champs de ton modèle

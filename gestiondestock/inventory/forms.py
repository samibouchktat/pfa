# inventory/forms.py
from django import forms
from django.forms import modelformset_factory

from .models import Article, Fournisseur, Commande, Avoir, CustomUser
from .utils import envoyer_sms  # Fonction d'envoi SMS

# Formulaire Article
class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        # Spécifie explicitement les champs existants
        fields = ['nom', 'reference', 'description', 'prix', 'quantite', 'stock']
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
class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = '__all__'

# Formulaire Commande
class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = '__all__'

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


from django import forms
from django.forms import modelformset_factory
from .models import Article, Fournisseur, Commande, Avoir
from .models import CustomUser
from .utils import envoyer_sms  # Assure-toi que cette fonction est bien définie et fonctionne correctement
from django.shortcuts import render, redirect  # Importer render et redirect pour gérer les vues


# Formulaires pour les modèles Article, Fournisseur et Commande
class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'


class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = '__all__'


class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = '__all__'


# Déclaration du formset pour le modèle Avoir
AvoirFormSet = modelformset_factory(Avoir, fields="__all__")


# Formulaire pour compléter le profil utilisateur avec le numéro de téléphone
class CompleteProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['phone_number']  # Tu peux ajouter d'autres champs si nécessaire


# Vue pour traiter le formulaire et envoyer le SMS
def complete_profile(request):
    if request.method == "POST":
        form = CompleteProfileForm(request.POST)
        if form.is_valid():
            numero_telephone = form.cleaned_data['phone_number']
            envoyer_sms(numero_telephone)  # Fonction qui envoie le SMS
            return redirect('success_url')  # Redirige après l'envoi du SMS
    else:
        form = CompleteProfileForm()

    return render(request, 'complete_profile.html', {'form': form})


# Formulaire personnalisé pour collecter le numéro de téléphone
class ProfilForm(forms.Form):
    phone_number = forms.CharField(max_length=15, required=True)

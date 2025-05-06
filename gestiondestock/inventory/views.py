from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.contrib import messages
from twilio.rest import Client
import os
import json
import datetime
import openai

from .models import Article, CustomUser, Fournisseur, Commande, Message, Stock
from .forms import ArticleForm, FournisseurForm, CommandeForm, AvoirFormSet
from django import forms
from django.shortcuts import render


from .models import Article, Stock, Commande
from .utils import generate_report

# Configure OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")


def is_manager(user):
    return getattr(user, "role", None) in {"gestionnaire", "admin"}


# Page d'accueil
def home(request):
    return render(request, 'first.html')


# Connexion
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        selected_role = request.POST['role']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'role') and user.role == selected_role:
                login(request, user)
                if user.role == 'admin':
                    return redirect('/admin/')
                elif user.role == 'gestionnaire':
                    return redirect('dashboard_gestionnaire')
                elif user.role == 'employe':
                    return redirect('dashboard_employe')
            else:
                messages.error(request, "Le rôle sélectionné ne correspond pas à votre rôle réel.")
                return redirect('login')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            return redirect('login')
    return render(request, 'login.html')


# Déconnexion
@never_cache
def log_out(request):
    logout(request)
    messages.success(request, "Vous êtes maintenant déconnecté.")
    return redirect('login')


# Redirection automatique selon rôle après connexion
@login_required
def redirect_dashboard(request):
    user = request.user
    if user.is_superuser:
        return redirect('/admin/')
    elif hasattr(user, 'role'):
        if user.role == 'gestionnaire':
            return redirect('dashboard_gestionnaire')
        elif user.role == 'employe':
            return redirect('dashboard_employe')
        elif user.role == 'admin':
            return redirect('dashboard_admin')
    messages.error(request, "Rôle utilisateur inconnu.")
    return redirect('login')


# Dashboards
@login_required
def dashboard_gestionnaire(request):
    return render(request, 'dashboard_gestionnaire.html')


@login_required
def dashboard_employe(request):
    return render(request, 'dashboard_employe.html')


@login_required
def dashboard_admin(request):
    return render(request, 'dashboard_admin.html')


# Liste des articles
@login_required
def liste_articles(request):
    product_list = Article.objects.all()
    paginator = Paginator(product_list, 10)
    page_number = request.GET.get('page')
    try:
        products = paginator.get_page(page_number)
    except EmptyPage:
        products = paginator.get_page(paginator.num_pages)
        messages.error(request, "Page demandée trop haute. Affichage de la dernière page.")
    except PageNotAnInteger:
        products = paginator.get_page(1)
        messages.error(request, "Page non valide. Affichage de la première page.")
    return render(request, 'articles.html', {'products': products})


# Ajouter un article
@login_required
def add_product(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit ajouté avec succès.")
            return redirect('product_list')
    else:
        form = ArticleForm()
    return render(request, 'add_product.html', {'form': form})

# Modifier un article
@login_required
def edit_product(request, id):
    article = get_object_or_404(Article, id=id)
    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article modifié avec succès.")
            return redirect('product_list')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'edit_product.html', {'form': form, 'article': article})


# Supprimer un article
@login_required
def delete_product(request, id):
    article = get_object_or_404(Article, id=id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, "Produit supprimé avec succès.")
        return redirect('product_list')
    return render(request, 'delete_product.html', {'article': article})


# Liste des fournisseurs
@login_required
def fournisseur_list(request):
    fournisseurs = Fournisseur.objects.all()
    return render(request, 'fournisseur_list.html', {'fournisseurs': fournisseurs})


# Ajouter un fournisseur
@login_required
def add_fournisseur(request):
    if request.method == "POST":
        form = FournisseurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fournisseur ajouté avec succès.")
            return redirect('fournisseur_list')
    else:
        form = FournisseurForm()
    return render(request, 'add_fournisseur.html', {'form': form})


# Modifier un fournisseur
@login_required
def edit_fournisseur(request, id):
    fournisseur = get_object_or_404(Fournisseur, id=id)
    if request.method == "POST":
        form = FournisseurForm(request.POST, instance=fournisseur)
        if form.is_valid():
            form.save()
            messages.success(request, "Fournisseur modifié avec succès.")
            return redirect('fournisseur_list')
    else:
        form = FournisseurForm(instance=fournisseur)
    return render(request, 'edit_fournisseur.html', {'form': form, 'fournisseur': fournisseur})


# Supprimer un fournisseur
@login_required
def delete_fournisseur(request, id):
    fournisseur = get_object_or_404(Fournisseur, id=id)
    if request.method == 'POST':
        fournisseur.delete()
        messages.success(request, "Fournisseur supprimé avec succès.")
        return redirect('fournisseur_list')
    return render(request, 'delete_fournisseur.html', {'fournisseur': fournisseur})


# Liste des commandes
@login_required
def commande_list(request):
    commandes = Commande.objects.all()
    return render(request, 'commande_list.html', {'commandes': commandes})


# Ajouter une commande
@login_required
def add_product(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit ajouté avec succès.")
            return redirect('product_list')
        else:
            messages.error(request, "Merci de corriger les erreurs ci-dessous.")
    else:
        # Pré‐remplir la catégorie par défaut
        form = ArticleForm(initial={'categorie': 'electronique'})

    return render(request, 'add_product.html', {'form': form})

# Supprimer une commande
@login_required
def delete_commande(request, id):
    commande = get_object_or_404(Commande, id=id)
    if request.method == 'POST':
        commande.delete()
        messages.success(request, "Commande supprimée avec succès.")
        return redirect('commande_list')
    return render(request, 'delete_commande.html', {'commande': commande})


# Gestion des messages
def msg(request):
    users = CustomUser.objects.exclude(id=request.user.id)
    return render(request, 'msg.html', {'users': users})


def conversation(request, user_id):
    current_user = request.user
    other_user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=current_user, receiver=other_user, content=content)
            return redirect('conv', user_id=other_user.id)

    messages_list = Message.objects.filter(
        (Q(sender=current_user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=current_user))
    ).order_by('timestamp')

    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)

    return render(request, 'conversation.html', {
        'other_user': other_user,
        'messages': messages_page
    })


# Profile completion form and SMS\ class CompleteProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['phone_number']

@login_required
def complete_profile(request):
    if request.method == "POST":
        form = CompleteProfileForm(request.POST)
        if form.is_valid():
            numero_telephone = form.cleaned_data['phone_number']
            envoyer_sms(numero_telephone)
            return redirect('success_url')
    else:
        form = CompleteProfileForm()
    return render(request, 'complete_profile.html', {'form': form})

account_sid = 'TON_ACCOUNT_SID'
auth_token = 'TON_AUTH_TOKEN'
client = Client(account_sid, auth_token)

def envoyer_sms(numero_telephone):
    message = client.messages.create(
        body="Votre code de vérification est : 123456",
        from_='+TON_NUMERO_TWILIO',
        to=numero_telephone
    )
    return message.sid


def success_view(request):
    return render(request, 'success.html')


# inventory/views.py

def is_manager(user):
    return getattr(user, "role", None) in {"gestionnaire", "admin"}

@login_required
@user_passes_test(is_manager)
def report_ai_view(request):
    # 1. Calcul des stats
    total = Article.objects.count()
    entree = Stock.objects.aggregate(t=Coalesce(Sum("entree"), 0))["t"]
    sortie = Stock.objects.aggregate(t=Coalesce(Sum("sortie"), 0))["t"]
    dispo = entree - sortie
    rupt = Article.objects.filter(stock__lte=0).count()
    en_att = Commande.objects.filter(etat="en_attente").count()

    stats = {
        "date": datetime.date.today().strftime("%d/%m/%Y"),
        "totalArticles": total,
        "stockDisponible": dispo,
        "ruptures": rupt,
        "cmdEnAttente": en_att,
    }

    # 2. Générer le rapport localement
    report_text = generate_report(stats)

    # 3. Afficher dans le template
    return render(request, "report_ai.html", {
        "stats": stats,
        "report": report_text,  # on traite le texte brut
    })

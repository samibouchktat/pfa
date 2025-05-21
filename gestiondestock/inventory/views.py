import os
import json
import datetime
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.forms import inlineformset_factory
from .forms import AvoirForm
from .models import Commande, Avoir
from .models import Fournisseur
from .forms import FournisseurForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum


AvoirFormSet = inlineformset_factory(Commande, Avoir, fields=('article','quantite'), extra=1, can_delete=True)
from .models import (
    Article, Stock, Fournisseur, Commande, Avoir,
    Message, CustomUser, UserProfile, TwoFactorCode
)
from .forms import (
    ArticleForm, 
    CommandeForm, BaseAvoirFormSet,
    EmailVerificationForm, OTPVerificationForm
)
from .utils import generate_report

# Configure OpenAI API key
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# Helpers

def is_manager(user):
    return getattr(user, "role", None) in {"gestionnaire", "admin"}


# Page d'accueil
def home(request):
    return render(request, 'first.html')


# Connexion
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        selected_role = request.POST.get("role")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Nom d’utilisateur ou mot de passe incorrect.")
            return redirect("login")

        UserProfile.objects.get_or_create(user=user)
        if user.role != selected_role:
            messages.error(request, "Le rôle sélectionné ne correspond pas à votre rôle réel.")
            return redirect("login")

        login(request, user)
        # ------ Redirection selon le rôle -------
        if user.role == "admin":
            return redirect("/admin/")
        elif user.role == "gestionnaire":
            return redirect("dashboard_gestionnaire")
        elif user.role == "fournisseur":
            return redirect("dashboard_fournisseur")
        return redirect("dashboard_employe")
    # Ici, c'est un GET (formulaire affiché pour la première fois)
    return render(request, "login.html")


# Déconnexion
@never_cache
def log_out(request):
    logout(request)
    messages.success(request, "Vous êtes maintenant déconnecté.")
    return redirect('login')


# Redirection selon rôle
@login_required
def redirect_dashboard(request):
    user = request.user
    if user.is_superuser:
        return redirect('/admin/')
    if user.role == 'gestionnaire':
        return redirect('dashboard_gestionnaire')
    if user.role == 'employe':
        return redirect('dashboard_employe')
    if user.role == 'admin':
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

@login_required
def dashboard_fournisseur(request):
    fournisseur = Fournisseur.objects.get(user=request.user)
    commandes = Commande.objects.filter(fournisseur=fournisseur)
    
    # Filtrage
    search = request.GET.get("search", "")
    filtre_etat = request.GET.get("filtre_etat", "")
    if search:
        commandes = commandes.filter(id__icontains=search)
    if filtre_etat:
        commandes = commandes.filter(etat=filtre_etat)
    
    # Statistiques
    nb_en_attente = commandes.filter(etat="en_attente").count()
    nb_validees = commandes.filter(etat="validée").count()
    nb_refusees = commandes.filter(etat="refusée").count()
    nb_total = commandes.count()
    montant_total = commandes.annotate(
    total=Sum(F('articles_commande__quantite') * F('articles_commande__article__prix'))
).aggregate(m=Sum('total'))['m']

    context = {
        "fournisseur": fournisseur,
        "commandes": commandes.order_by('-date'),
        "nb_en_attente": nb_en_attente,
        "nb_validees": nb_validees,
        "nb_refusees": nb_refusees,
        "nb_total": nb_total,
        "montant_total": montant_total,
    }
    return render(request, "dashboard_fournisseur.html", context)
# CRUD Articles
@login_required
def liste_articles(request):
    qs = Article.objects.all()
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        products = paginator.get_page(page)
    except (EmptyPage, PageNotAnInteger):
        products = paginator.get_page(1)
    return render(request, 'articles.html', {'products': products})


@login_required
def add_product(request):
    form = ArticleForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Produit ajouté avec succès.")
        return redirect('product_list')
    return render(request, 'add_product.html', {'form': form})


@login_required
def edit_product(request, id):
    article = get_object_or_404(Article, id=id)
    form = ArticleForm(request.POST or None, instance=article)
    if form.is_valid():
        form.save()
        messages.success(request, "Article modifié avec succès.")
        return redirect('product_list')
    return render(request, 'edit_product.html', {'form': form, 'article': article})


@login_required
def delete_product(request, id):
    article = get_object_or_404(Article, id=id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, "Produit supprimé avec succès.")
        return redirect('product_list')
    return render(request, 'delete_product.html', {'article': article})





# Messagerie
@login_required
def msg(request):
    users = CustomUser.objects.exclude(id=request.user.id)
    return render(request, 'msg.html', {'users': users})


@login_required
def conversation(request, user_id):
    current, other = request.user, get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=current, receiver=other, content=content)
            return redirect('conv', user_id=other.id)
    qs = Message.objects.filter(
        (Q(sender=current)&Q(receiver=other))|
        (Q(sender=other)&Q(receiver=current))   
    ).order_by('timestamp')
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)
    return render(request, 'conversation.html', {'other_user': other, 'messages': messages_page})


# Vérification OTP email
@login_required
def complete_profile(request):
    # Étape 1: saisie email
    if 'otp_email' not in request.session:
        form = EmailVerificationForm(request.POST or None)
        if form.is_valid():
            email = form.cleaned_data['email']
            code_obj = TwoFactorCode.create_code(request.user)
            request.session['otp_email'] = email
            send_mail(
                "Votre code de vérification",
                f"Bonjour {request.user.username},\nVotre code est : {code_obj.code}",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return render(request, 'complete_profile.html', {'step':'verify','email': email,'form': OTPVerificationForm()})
        return render(request, 'complete_profile.html', {'step':'email','form': form})
    # Étape 2: vérification code
    email = request.session.get('otp_email')
    form = OTPVerificationForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        code = form.cleaned_data['code']
        try:
            otp = TwoFactorCode.objects.get(user=request.user, code=code, is_used=False)
            if otp.is_valid():
                otp.is_used=True
                otp.save()
                del request.session['otp_email']
                return redirect('redirect_dashboard')
            form.add_error('code','Ce code a expiré.')
        except TwoFactorCode.DoesNotExist:
            form.add_error('code','Code invalide ou déjà utilisé.')
    return render(request, 'complete_profile.html', {'step':'verify','email': email,'form': form})


# Rapport IA
@login_required
@user_passes_test(is_manager)
def report_ai_view(request):
    total = Article.objects.count()
    entree = Stock.objects.aggregate(t=Coalesce(Sum('entree'),0))['t']
    sortie = Stock.objects.aggregate(t=Coalesce(Sum('sortie'),0))['t']
    dispo = entree - sortie
    rupt = Article.objects.filter(stock__lte=0).count()
    en_att = Commande.objects.filter(etat='en_attente').count()
    stats = {'date': datetime.date.today().strftime('%d/%m/%Y'),'totalArticles': total,'stockDisponible': dispo,'ruptures': rupt,'cmdEnAttente': en_att}
    report_text = generate_report(stats)
    return render(request, 'report_ai.html', {'stats': stats, 'report': report_text})


# Liste des commandes du gestionnaire
@login_required
def commande_list(request):
    commandes = Commande.objects.filter(employe=request.user)
    return render(request, 'commande_list.html', {'commandes': commandes})

# Ajouter une commande avec ses articles
@login_required
def add_commande(request):
    if request.method == "POST":
        form = CommandeForm(request.POST)
        formset = AvoirFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            commande = form.save(commit=False)
            commande.employe = request.user  # Gestionnaire courant
            commande.save()
            formset.instance = commande
            formset.save()
            messages.success(request, "Commande enregistrée.")
            return redirect('commande_list')
    else:
        form = CommandeForm()
        formset = AvoirFormSet()
    return render(request, 'add_commande.html', {'form': form, 'formset': formset})

# Détail d'une commande
@login_required
def commande_detail(request, id):
    commande = get_object_or_404(Commande, id=id)
    avoirs = commande.articles_commande.all()
    return render(request, 'commande_detail.html', {'commande': commande, 'avoirs': avoirs})

def is_gestionnaire(user):
    return user.role == 'gestionnaire' or user.role == 'admin'

@login_required
@user_passes_test(is_gestionnaire)
def fournisseur_list(request):
    fournisseurs = Fournisseur.objects.all()
    return render(request, 'fournisseur_list.html', {'fournisseurs': fournisseurs})

@login_required
@user_passes_test(is_gestionnaire)
def add_fournisseur(request):
    if request.method == "POST":
        form = FournisseurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fournisseur ajouté.")
            return redirect('fournisseur_list')
    else:
        form = FournisseurForm()
    return render(request, 'add_fournisseur.html', {'form': form})

@login_required
@user_passes_test(is_gestionnaire)
def edit_fournisseur(request, id):
    fournisseur = get_object_or_404(Fournisseur, id=id)
    if request.method == "POST":
        form = FournisseurForm(request.POST, instance=fournisseur)
        if form.is_valid():
            form.save()
            messages.success(request, "Fournisseur modifié.")
            return redirect('fournisseur_list')
    else:
        form = FournisseurForm(instance=fournisseur)
    return render(request, 'edit_fournisseur.html', {'form': form})

@login_required
@user_passes_test(is_gestionnaire)
def delete_fournisseur(request, id):
    fournisseur = get_object_or_404(Fournisseur, id=id)
    if request.method == "POST":
        fournisseur.delete()
        messages.success(request, "Fournisseur supprimé.")
        return redirect('fournisseur_list')
    return render(request, 'delete_fournisseur.html', {'fournisseur': fournisseur})


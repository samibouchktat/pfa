import os
from django.db.models import F
from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import F
from .models import Article
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
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from .models import Article, Fournisseur, Stock, Commande
from django.utils import timezone
from datetime import timedelta
from .forms import FournisseurUserForm
from django.contrib.auth import get_user_model
from .models import Article, MouvementStock
from .forms import MouvementStockForm
from django.http import HttpResponse
import pandas as pd
from .forms import MouvementForm
from datetime import datetime

from .models import Article
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from .utils import generate_report
from django.http import JsonResponse
from .forms import ArticleUpdateForm
AvoirFormSet = inlineformset_factory(Commande, Avoir, fields=('article','quantite'), extra=1, can_delete=True)
from .models import (
    Article, Stock, Fournisseur, Commande, Avoir,
    Message, CustomUser, UserProfile, TwoFactorCode,DemandeArticle,
)
from .forms import (
    ArticleForm, 
    CommandeForm, BaseAvoirFormSet,
    EmailVerificationForm, OTPVerificationForm,DemandeArticleForm,

)
from .utils import generate_report
from django.db.models import F

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

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Nom d’utilisateur ou mot de passe incorrect.")
            return redirect("login")

        login(request, user)

        # Redirection automatique selon user.role
        if user.is_superuser or user.role == "admin":
            return redirect('/admin/')
        elif user.role == "gestionnaire":
            return redirect('dashboard_gestionnaire')
        elif user.role == "employe":
            return redirect('dashboard_employe')
        else:
            messages.error(request, "Rôle utilisateur inconnu.")
            logout(request)
            return redirect("login")

    return render(request, "login.html")


@login_required
def redirect_dashboard(request):
    user = request.user
    if user.is_superuser or user.role == "admin":
        return redirect('/admin/')
    if user.role == "gestionnaire":
        return redirect('dashboard_gestionnaire')
    if user.role == "employe":
        return redirect('dashboard_employe')
    messages.error(request, "Rôle utilisateur inconnu.")
    return redirect('login')

@never_cache
def log_out(request):
    logout(request)
    messages.success(request, "Vous êtes maintenant déconnecté.")
    return redirect('login')

@login_required
def dashboard_gestionnaire(request):
    return render(request, 'dashboard_gestionnaire.html')


@login_required
def dashboard_employe(request):
    return render(request, 'dashboard_employe.html')



@login_required
def dashboard_admin(request):
    return render(request, 'dashboard_admin.html')

from django.contrib import messages

@login_required
def dashboard_fournisseur(request):
    try:
        fournisseur = Fournisseur.objects.get(user=request.user)
    except Fournisseur.DoesNotExist:
        messages.error(request, "Aucun fournisseur associé à ce compte utilisateur.")
        return redirect('login')  

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
@never_cache
@login_required
def liste_articles(request):
    qs = Article.objects.all().order_by('-stock', 'nom')
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        products = paginator.get_page(page)
    except (EmptyPage, PageNotAnInteger):
        products = paginator.get_page(1)
    return render(request, 'articles.html', {'products': products})

def is_gestionnaire(user):
    return getattr(user, "role", None) in ["gestionnaire", "admin"]

@login_required
@user_passes_test(is_gestionnaire)
def add_product(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.stock = article.quantite
            article.save()
            messages.success(request, "✅ Produit ajouté avec succès.")
            return redirect('product_list')  # Vérifie que cette URL existe
        else:
            messages.error(request, "❌ Formulaire invalide. Veuillez corriger les erreurs.")
    else:
        form = ArticleForm()

    return render(request, 'add_product.html', {'form': form})
@login_required
def edit_product(request, id):
    article = get_object_or_404(Article, id=id)
    form = ArticleForm(request.POST or None, instance=article)
    if form.is_valid():
        form.save()
        messages.success(request, "Produit modifié avec succès.")
        return redirect('product_list')  # Redirige vers ta liste d'articles
    return render(request, 'edit_product.html', {'form': form, 'article': article})
@login_required
def delete_product(request, id):
    article = get_object_or_404(Article, id=id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, "Produit supprimé avec succès.")
        return redirect('product_list')
    return render(request, 'delete_product.html', {'article': article})




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
    # Si c'est un GET (ou un autre verbe qui n'est pas POST), on réinitialise la clé de session
    if request.method != "POST":
        # Supprime la valeur de session si elle existe
        request.session.pop("otp_email", None)

        # Affiche le formulaire de saisie d'email (step 1)
        form = EmailVerificationForm()
        return render(request, "complete_profile.html", {
            "step": "email",
            "form": form
        })

    # À partir d'ici, request.method == "POST"

    # --- Étape 1 : l'utilisateur a soumis le champ email pour recevoir le code ---
    if "otp_email" not in request.session:
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]

            # On génère l'objet TwoFactorCode (contenant le code) pour l'utilisateur courant
            code_obj = TwoFactorCode.create_code(request.user)

            # On stocke en session l'email qui est en cours de vérification
            request.session["otp_email"] = email

            # On envoie le mail avec le code
            send_mail(
                subject="Votre code de vérification",
                message=f"Bonjour {request.user.username},\nVotre code est : {code_obj.code}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

            # On prépare le formulaire du pas 2 (vérification du code)
            form_code = OTPVerificationForm()
            return render(request, "complete_profile.html", {
                "step": "verify",
                "email": email,
                "form": form_code
            })
        else:
            # Le formulaire EmailVerificationForm n'est pas valide (ex. champ vide, format non valide, etc.)
            return render(request, "complete_profile.html", {
                "step": "email",
                "form": form
            })

    # --- Étape 2 : l'utilisateur soumet le code reçu par e-mail ---
    email = request.session.get("otp_email")
    form_code = OTPVerificationForm(request.POST)
    if form_code.is_valid():
        code = form_code.cleaned_data["code"]
        try:
            otp = TwoFactorCode.objects.get(user=request.user, code=code, is_used=False)
            if otp.is_valid():
                # Le code est encore valide : on marque l'OTP comme utilisé
                otp.is_used = True
                otp.save()

                # On rattache l'email secondaire au user
                user = request.user
                user.secondary_email = email
                user.save()

                # On supprime la session
                del request.session["otp_email"]

                messages.success(request,
                    f"L'adresse {email} a bien été ajoutée à votre compte. Vous pourrez vous connecter avec cet email ou celui de l'administrateur.")
                return redirect("redirect_dashboard")
            else:
                # Le code est expiré (is_valid() retourne False)
                form_code.add_error("code", "Ce code a expiré.")
        except TwoFactorCode.DoesNotExist:
            form_code.add_error("code", "Code invalide ou déjà utilisé.")
    # Si on arrive ici, c'est soit parce que form_code n'est pas valide, soit que le code fourni est incorrect/expiré
    return render(request, "complete_profile.html", {
        "step": "verify",
        "email": email,
        "form": form_code
    })
# Rapport IA

@login_required
@user_passes_test(is_manager)
def report_ai_view(request):
    rapport_texte = generate_report(request)
    print("=== RAPPORT GÉNÉRÉ ===")
    print(rapport_texte)  # Affiche dans le terminal

    return render(request, 'report_ai.html', {
        'rapport_texte': rapport_texte
    })
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
    return user.role in ['gestionnaire', 'admin']


@login_required
@user_passes_test(is_gestionnaire)
def fournisseur_list(request):
    fournisseurs = Fournisseur.objects.all()
    return render(request, 'fournisseur_list.html', {'fournisseurs': fournisseurs})
def add_fournisseur(request):
    if request.method == "POST":
        form = FournisseurUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            User = get_user_model()
            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                email=data['email'],
                role='fournisseur'
            )
            Fournisseur.objects.create(
                user=user,  # On lie le fournisseur au user créé
                nom=data['nom'],
                contact=data['contact'],
                email=data['email'],
                adresse=data['adresse']
            )
            messages.success(request, "Fournisseur et compte utilisateur créés.")
            return redirect('fournisseur_list')
    else:
        form = FournisseurUserForm()
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

@login_required
def stats_articles_par_categorie(request):
    data = (
        Article.objects.values('categorie')  # adapte selon ton modèle
        .annotate(nombre=Count('id'))
        .order_by('-nombre')
    )
    categories = [d['categorie'] or 'Sans catégorie' for d in data]
    quantites = [d['nombre'] for d in data]
    return JsonResponse({'labels': categories, 'data': quantites})

@login_required
def stats_top_articles(request):
    articles = Article.objects.order_by('-quantite')[:10]
    return JsonResponse({
        'labels': [a.nom for a in articles],
        'data': [a.quantite for a in articles]
    })

@login_required
def stats_mouvements_stock(request):
    nb_jours = int(request.GET.get('jours', 7))
    stocks = (
        Stock.objects.filter(date_entree__gte=timezone.now() - timedelta(days=nb_jours))
        .annotate(day=TruncDate('date_entree'))
        .values('day')
        .annotate(entrees=Sum('entree'), sorties=Sum('sortie'))
        .order_by('day')
    )
    labels = [str(x['day']) for x in stocks]
    entrees = [x['entrees'] or 0 for x in stocks]
    sorties = [x['sorties'] or 0 for x in stocks]
    return JsonResponse({'labels': labels, 'entrees': entrees, 'sorties': sorties})

@login_required
def stats_articles_rupture(request):
    # Articles dont le stock est inférieur au stock minimum
    rupture = Article.objects.filter(stock__lt=F('stock_min')).count()
    return JsonResponse({'rupture': rupture})

@login_required
def stats_commandes_par_fournisseur(request):
    qs = Fournisseur.objects.annotate(nb=Count('commande')).order_by('-nb')
    return JsonResponse({
        'labels': [f.nom for f in qs],
        'data': [f.nb for f in qs]
    })
from django.shortcuts import render, redirect


def nouvelle_entree(request):
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.type_mouvement = 'entree'
            mouvement.user = request.user
            mouvement.save()
            messages.success(request, "Entrée de stock enregistrée avec succès.")
            return redirect('product_list')
        else:
            print("❌ Erreurs du formulaire :", form.errors)  # ← AJOUT ICI
    else:
        form = MouvementStockForm()
    return render(request, 'nouvelle_entree.html', {'form': form})

@login_required
@user_passes_test(is_gestionnaire)
def nouvelle_sortie(request):
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.type_mouvement = 'sortie'
            mouvement.user = request.user
            try:
                mouvement.save()
                messages.success(request, "Sortie de stock enregistrée avec succès.")
                return redirect('product_list')  # Affiche la liste mise à jour
            except ValueError as e:
                form.add_error(None, str(e))
    else:
        form = MouvementStockForm()
    return render(request, 'nouvelle_sortie.html', {'form': form})

def faire_demande(request):
    if request.method == 'POST':
        form = DemandeArticleForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.employe = request.user
            demande.save()
            return redirect('mes_demandes')  # ou la page de ton choix
    else:
        form = DemandeArticleForm()
    return render(request, 'faire_demande.html', {'form': form})
@login_required
def mes_demandes(request):
    demandes = DemandeArticle.objects.filter(employe=request.user)
    return render(request, 'mes_demandes.html', {'demandes': demandes})

def is_gestionnaire(user):
    return user.role == 'gestionnaire' or user.role == 'admin'

@login_required
@user_passes_test(is_gestionnaire)
def liste_demandes(request):
    # Toutes les demandes, du plus récent au plus ancien
    demandes = DemandeArticle.objects.select_related('article', 'employe').order_by('-date_demande')

    # Filtre par statut si demandé (ex : ?statut=en_attente)
    statut = request.GET.get('statut')
    if statut:
        demandes = demandes.filter(statut=statut)

    context = {
        "demandes": demandes,
        "statut": statut,
    }
    return render(request, "liste.html", context) 
def export_articles(request, format):
    articles = Article.objects.all()
    # Si tu veux filtrer selon la recherche :
    search = request.GET.get('search')
    if search:
        articles = articles.filter(nom__icontains=search) | articles.filter(reference__icontains=search)
    
    data = []
    for art in articles:
        data.append({
            "Nom": art.nom,
            "Référence": art.reference,
            "Prix": art.prix,
            "Quantité": art.quantite,
        })
    df = pd.DataFrame(data)

    if format == "excel":
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="articles.xlsx"'
        df.to_excel(response, index=False)
        return response

    elif format == "pdf":
        # Simple PDF via pandas pour dépanner, version professionnelle sur demande
        import io
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib import colors
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer)
        elements = []
        table_data = [df.columns.tolist()] + df.values.tolist()
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0d6efd")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(t)
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="articles.pdf"'
        response.write(pdf)
        return response

    else:
        return HttpResponse("Format inconnu", status=400)
def autocomplete_product_names(request):
    q = request.GET.get('q', '')
    if q:
        results = list(Article.objects.filter(nom__icontains=q).values_list('nom', flat=True)[:10])
    else:
        results = []
    return JsonResponse({'results': results})

def validate_product_field(request):
    # Exemple basique à adapter
    if request.method == "POST":
        field_name = list(request.POST.keys())[0]
        value = request.POST[field_name]
        error = ""

        # Validation selon le champ
        if field_name == "prix":
            try:
                val = float(value)
                if val <= 0:
                    error = "Le prix doit être positif."
            except:
                error = "Prix invalide."
        if field_name == "nom":
            if len(value) < 2:
                error = "Nom trop court."
        # Ajoute d'autres règles ici...

        return JsonResponse({"error": error})
    return JsonResponse({"error": "Méthode non autorisée."}, status=405)
def decouvrire_demo(request):
    """
    Affiche la page contenant la vidéo .mp4 que vous avez téléchargée.
    """
    return render(request, 'decouvrire_demo.html')
@login_required
def modifier_quantite(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        form = ArticleUpdateForm(request.POST, instance=article)
        if form.is_valid():
            form.save()  # met à jour quantite + stock via save() override
            # Après save(), on peut récupérer le user et son secondary_email
            utilisateur = request.user
            if article.stock < article.stock_min:
                email_dest = utilisateur.secondary_email
                if email_dest:
                    # Composez ici le même corps / sujet que précédemment
                    sujet = f"⚠️ Stock critique pour « {article.nom} »"
                    corps = (
                        f"Bonjour {utilisateur.username},\n\n"
                        f"Le stock de l'article « {article.nom} » (Réf : {article.reference}) "
                        f"est critique ({article.stock} unités, seuil : {article.stock_min}).\n\n"
                        "Merci de réagir rapidement.\n"
                    )
                    send_mail(
                        sujet,
                        corps,
                        settings.DEFAULT_FROM_EMAIL,
                        [email_dest],
                        fail_silently=False
                    )
            return redirect("liste_articles")
    else:
        form = ArticleUpdateForm(instance=article)

    return render(request, "inventory/modifier_article.html", {
        "article": article,
        "form": form
    })

@login_required
def stats_total_articles(request):
    total = Article.objects.count()
    return JsonResponse({'total': total})

@login_required
def stats_fournisseurs_actifs(request):
    # Fournisseurs ayant au moins une commande dans les 30 derniers jours
    date_limite = timezone.now().date() - timedelta(days=30)
    actifs = Fournisseur.objects.filter(
        commande__date__gte=date_limite
    ).distinct().count()
    return JsonResponse({'actifs': actifs})

@login_required
def stats_commandes_en_cours(request):
    # Commandes avec état "en attente" ou équivalent
    en_cours = Commande.objects.filter(
        etat__in=['en_attente', 'en cours']
    ).count()
    return JsonResponse({'en_cours': en_cours})

@login_required
def stats_evolution_stocks(request):
    # Evolution sur 30 jours
    date_debut = timezone.now().date() - timedelta(days=30)
    
    # Récupérer tous les mouvements de stock
    mouvements = MouvementStock.objects.filter(
        date__date__gte=date_debut
    ).order_by('date__date')
    
    # Initialiser le dictionnaire avec toutes les dates
    evolution = {}
    date_courante = date_debut
    while date_courante <= timezone.now().date():
        evolution[date_courante.isoformat()] = 0
        date_courante += timedelta(days=1)
    
    # Calculer les variations par jour
    for mvt in mouvements:
        date = mvt.date.date().isoformat()
        if mvt.type_mouvement == 'entree':
            evolution[date] += mvt.quantite
        else:  # sortie
            evolution[date] -= mvt.quantite
    
    return JsonResponse({
        'dates': list(evolution.keys()),
        'variations': list(evolution.values())
    })

@login_required
def stats_delai_livraison(request):
    """
    Calcule le délai moyen de livraison par fournisseur
    en se basant sur les commandes validées
    """
    try:
        # On prend les commandes validées des 90 derniers jours pour avoir des données pertinentes
        date_limite = timezone.now().date() - timedelta(days=90)
        
        # Récupérer les fournisseurs qui ont au moins une commande
        fournisseurs = Fournisseur.objects.filter(
            commande__date__gte=date_limite
        ).distinct()

        # Préparer les données
        noms_fournisseurs = []
        delais = []

        for fournisseur in fournisseurs:
            noms_fournisseurs.append(fournisseur.nom)
            # Pour l'instant on met un délai fixe de 5 jours
            # Vous pourrez adapter ce calcul selon vos besoins réels
            delais.append(5)

        # Si aucune donnée, mettre des données par défaut
        if not noms_fournisseurs:
            noms_fournisseurs = ['Aucune donnée']
            delais = [0]

        return JsonResponse({
            'fournisseurs': noms_fournisseurs,
            'delais': delais
        })
    except Exception as e:
        # En cas d'erreur, renvoyer des données par défaut
        return JsonResponse({
            'fournisseurs': ['Erreur de données'],
            'delais': [0]
        })

@login_required
def stats_stock_minimum(request):
    """
    Analyse la répartition des stocks par état (critique, normal, excédentaire)
    """
    try:
        # Récupérer tous les articles avec stock et stock_min
        articles = Article.objects.filter(stock_min__gt=0)
        
        # Initialiser les compteurs
        critique = 0  # Stock < stock_min
        attention = 0  # Stock entre stock_min et 2*stock_min
        normal = 0    # Stock entre 2*stock_min et 3*stock_min
        excedent = 0  # Stock > 3*stock_min
        
        # Calculer la répartition
        for article in articles:
            ratio = article.stock / article.stock_min if article.stock_min > 0 else 0
            
            if ratio < 1:
                critique += 1
            elif ratio < 2:
                attention += 1
            elif ratio < 3:
                normal += 1
            else:
                excedent += 1
        
        # Si aucun article, mettre des valeurs par défaut
        total = critique + attention + normal + excedent
        if total == 0:
            return JsonResponse({
                'labels': ['Aucune donnée'],
                'data': [1],
                'colors': ['#e0e0e0']
            })
        
        # Préparer les données pour le graphique
        return JsonResponse({
            'labels': [
                f'Critique (<100%) : {critique} articles',
                f'Attention (100-200%) : {attention} articles',
                f'Normal (200-300%) : {normal} articles',
                f'Excédent (>300%) : {excedent} articles'
            ],
            'data': [critique, attention, normal, excedent],
            'colors': [
                '#dc3545',  # Rouge pour critique
                '#ffc107',  # Jaune pour attention
                '#28a745',  # Vert pour normal
                '#17a2b8'   # Bleu pour excédent
            ]
        })
        
    except Exception as e:
        # En cas d'erreur, renvoyer des données par défaut
        return JsonResponse({
            'labels': ['Erreur de données'],
            'data': [1],
            'colors': ['#dc3545']
        })

@login_required
def stats_impact_co2(request):
    # Impact CO2 total par article
    articles = Article.objects.exclude(facteur_co2=0).order_by('-facteur_co2')[:10]
    impact = {
        a.nom: round(a.facteur_co2 * a.stock, 2)
        for a in articles
    }
    
    return JsonResponse({
        'articles': list(impact.keys()),
        'co2': list(impact.values())
    })

@login_required
def stats_total_articles(request):
    total = Article.objects.count()
    return JsonResponse({'total': total})

@login_required
def stats_fournisseurs_actifs(request):
    # Fournisseurs ayant au moins une commande dans les 30 derniers jours
    date_limite = timezone.now().date() - timedelta(days=30)
    actifs = Fournisseur.objects.filter(
        commande__date__gte=date_limite
    ).distinct().count()
    return JsonResponse({'actifs': actifs})

@login_required
def stats_commandes_en_cours(request):
    # Commandes avec état "en attente" ou équivalent
    en_cours = Commande.objects.filter(
        etat__in=['en_attente', 'en cours']
    ).count()
    return JsonResponse({'en_cours': en_cours})

@login_required
def stats_evolution_stocks(request):
    # Evolution sur 30 jours
    date_debut = timezone.now().date() - timedelta(days=30)
    
    # Récupérer tous les mouvements de stock
    mouvements = MouvementStock.objects.filter(
        date__date__gte=date_debut
    ).order_by('date__date')
    
    # Initialiser le dictionnaire avec toutes les dates
    evolution = {}
    date_courante = date_debut
    while date_courante <= timezone.now().date():
        evolution[date_courante.isoformat()] = 0
        date_courante += timedelta(days=1)
    
    # Calculer les variations par jour
    for mvt in mouvements:
        date = mvt.date.date().isoformat()
        if mvt.type_mouvement == 'entree':
            evolution[date] += mvt.quantite
        else:  # sortie
            evolution[date] -= mvt.quantite
    
    return JsonResponse({
        'dates': list(evolution.keys()),
        'variations': list(evolution.values())
    })








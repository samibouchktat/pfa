# gestiondestock/inventory/urls.py
from .views import msg, conversation 
from django.urls import path
from .views import (
    # Authentification & profil
    login_view, log_out, redirect_dashboard,
    dashboard_gestionnaire, dashboard_employe, dashboard_admin,
    complete_profile, 

    # Articles
    liste_articles, add_product, edit_product, delete_product,

    commande_detail, commande_list, add_commande,
    fournisseur_list, add_fournisseur, edit_fournisseur, delete_fournisseur,dashboard_fournisseur,
    # Fournisseurs

    # Messagerie
    msg, conversation,

    # Rapport IA
    report_ai_view,
)

urlpatterns = [
    # Authentification
    path('login/',  login_view,         name='login'),
    path('logout/', log_out, name='log_out'),
    path('',        redirect_dashboard, name='home'),
    path('dashboard/gest/',  dashboard_gestionnaire, name='dashboard_gestionnaire'),
    path('dashboard/emp/',   dashboard_employe,      name='dashboard_employe'),
    path('dashboard/admin/', dashboard_admin,        name='dashboard_admin'),
    path('dashboard/fournisseur/', dashboard_fournisseur, name='dashboard_fournisseur'),
# inventory/urls.py
    path('profile/complete/', complete_profile, name='complete_profile'),

    #path('profile/success/',  success_view,          name='success_url'),

    # Articles
    path('articles/',             liste_articles,  name='product_list'),
    path('articles/ajouter/',     add_product,     name='add_product'),
    path('articles/<int:id>/edit/',   edit_product,    name='edit_product'),
    path('articles/<int:id>/suppr/',  delete_product,  name='delete_product'),


    path('commandes/', commande_list, name='commande_list'),
    path('commandes/ajouter/', add_commande, name='add_commande'),
    path('commandes/<int:id>/', commande_detail, name='commande_detail'),


    # Messagerie
# Après
    path('messages/', msg, name='msg'),
    path('conv/<int:user_id>/', conversation, name='conv'),

    # Rapport IA
    path('report-ai/',         report_ai_view, name='report_ai'),

    path('fournisseurs/', fournisseur_list, name='fournisseur_list'),
    path('fournisseurs/ajouter/', add_fournisseur, name='add_fournisseur'),
    path('fournisseurs/<int:id>/modifier/', edit_fournisseur, name='edit_fournisseur'),
    path('fournisseurs/<int:id>/supprimer/', delete_fournisseur, name='delete_fournisseur'),
   

]

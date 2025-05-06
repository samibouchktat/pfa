# gestiondestock/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from inventory import views as inv   # toutes tes vues app

from django.contrib import admin
from django.urls import path
from inventory import views
from django.conf import settings
from django.conf.urls.static import static
from inventory.views import home  # importer la vue home
from django.contrib.auth import views as auth_views
urlpatterns = [
    # Accès admin Django
    path('admin/', admin.site.urls),
    
    # Page d'accueil
    path('', views.home, name='first'),  # CORRIGÉ ici ! "home" et pas "first"
    
    # Authentification
    path('login/', views.login_view, name='login'),
    path('log_out/', views.log_out, name='log_out'),


    # Redirection selon rôle après connexion
    path('redirect-dashboard/', views.redirect_dashboard, name='redirect_dashboard'),

    # Dashboards par rôle
    path('gestionnaire_dashboard/', views.dashboard_gestionnaire, name='dashboard_gestionnaire'),
    path('employe_dashboard/', views.dashboard_employe, name='dashboard_employe'),
    path('admin_dashboard/', views.dashboard_admin, name='dashboard_admin'),  # Route pour admin
    
    # Gestion des articles
    path('products/', views.liste_articles, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:id>/', views.delete_product, name='delete_product'),

    # Gestion articles version gestion (s'ajoute avec un /gestion/ dans l'URL)
    path('gestion/articles/', views.liste_articles, name='gestion_articles'),
    path('gestion/articles/ajouter/', views.add_product, name='ajouter_article'),
    path('gestion/articles/<int:id>/modifier/', views.edit_product, name='modifier_article'),
    path('gestion/articles/<int:id>/supprimer/', views.delete_product, name='supprimer_article'),

    # Gestion des messages
     # Messagerie interne
    # URL canonique pour la liste des utilisateurs (conversations)
    path("messages/", inv.msg, name="messages_home"),
    # alias court si besoin
    path("gestion/msg/", inv.msg, name="msg"),

    # Conversations
    path("messages/<int:user_id>/", inv.conversation, name="conversation"),
    path("conv/<int:user_id>/",   inv.conversation, name="conv"),

    path('completer-profil/', views.complete_profile, name='complete_profile'),
    path('success/', views.success_view, name='success_url'),
    path("report_ai/",          inv.report_ai_view,    name="report_ai"),            # URL simple
                                   # alias lisible
    

]  # Pas de "+" ici, directement ajouter les lignes

# Route pour les fichiers statiques (images, JS, CSS, etc.)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# -------------------------------------------------------- FICHIERS STATIC & MEDIA (DEV)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(
        getattr(settings, "MEDIA_URL", "/media/"),
        document_root=getattr(settings, "MEDIA_ROOT", settings.BASE_DIR / "media"),
    )

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Article, Fournisseur, Commande, Avoir, Stock, Rapport

# Personnalisation de l'affichage dans l'admin pour CustomUser
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Rôle utilisateur', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rôle utilisateur', {'fields': ('role',)}),
    )
    # inventory/admin.py
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("nom", "quantite", "facteur_co2")
    search_fields = ("nom",)


admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Fournisseur)
admin.site.register(Commande)
admin.site.register(Avoir)
admin.site.register(Stock)
admin.site.register(Rapport)


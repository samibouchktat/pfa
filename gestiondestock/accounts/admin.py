from django.contrib import admin
from .models import EmailOTP

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "valid_until")
    list_filter  = ("user",)

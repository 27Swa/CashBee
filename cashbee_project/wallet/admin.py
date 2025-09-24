from django.contrib import admin

from .models import Wallet

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'balance', 'transaction_limit', 'max_limit')

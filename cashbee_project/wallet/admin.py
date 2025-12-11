from django.contrib import admin
from .models import Wallet, SystemLimit, PersonalLimit, FamilyLimit

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__username', 'user__phone_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SystemLimit)
class SystemLimitAdmin(admin.ModelAdmin):
    list_display = ('per_transaction_limit', 'daily_limit', 'monthly_limit', 'is_active')
    list_filter = ('is_active',)

@admin.register(PersonalLimit)
class PersonalLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'per_transaction_limit', 'daily_limit', 'monthly_limit', 'is_active')  # ✅ FIXED
    search_fields = ('user__username', 'user__phone_number')  
    list_filter = ('is_active',)

@admin.register(FamilyLimit)
class FamilyLimitAdmin(admin.ModelAdmin):
    list_display = ('parent', 'child', 'per_transaction_limit', 'daily_limit', 'monthly_limit', 'is_active')
    search_fields = ('parent__username', 'child__username', 'parent__phone_number', 'child__phone_number')
    list_filter = ('is_active',)


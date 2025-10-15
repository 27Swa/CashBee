from  django.utils.html import format_html
from django.contrib import admin
from django.contrib import admin
from django.urls import reverse
from .models import User, Family

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'phone_number', 'national_id', 'role', 'family','failed_attempts','wallet_link')
    search_fields = ('username','phone_number', 'national_id')
    list_filter = ('role',)
    def wallet_link(self, obj):
        if obj.wallet:
            url = reverse('admin:wallet_wallet_change', args=[obj.wallet.id])
            return format_html('<a href="{}">Wallet #{}</a>', url, obj.wallet.id)
        return '-'
    
    wallet_link.short_description = 'Wallet'
    

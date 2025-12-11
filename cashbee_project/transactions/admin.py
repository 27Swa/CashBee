from django.contrib import admin
from .models import CollectionRequest, Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_wallet', 'to_wallet', 'amount', 'transaction_type', 'status','date')
    list_filter = ('transaction_type', 'date','status')
    search_fields = ('from_wallet__user__username', 'to_wallet__user__username')
    date_hierarchy = 'date'

@admin.register(CollectionRequest)
class CollectionRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_user', 'to_user', 'amount', 'status', 'note','created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')
    date_hierarchy = 'created_at'
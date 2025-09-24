from django.contrib import admin
from django.contrib import admin
from .models import Transaction
from .services import TransactionOperation
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_wallet_id', 'to_wallet_id', 'amount', 'transaction_type', 'date')
    list_filter = ('transaction_type', 'date')
    search_fields = ('from_wallet_id', 'to_wallet_id', 'amount')
    ordering = ('-date',)
    def from_wallet_id(self, obj):
        return obj.from_wallet.id

    def to_wallet_id(self, obj):
        return obj.to_wallet.id

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        op = TransactionOperation(obj.from_wallet.user, obj.to_wallet.user)
        op.execute_transaction(obj.transaction_type, obj.amount)

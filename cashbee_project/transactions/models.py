from decimal import Decimal
from django.utils import timezone
from django.db import models
from users.models import User
from wallet.models import Wallet
from django.core.validators import MinValueValidator
from django.db.models import Sum


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        SEND = 'Send', 'Send'
        # DONATE = 'Donate', 'Donate'
        # BILL_PAY = 'Bill Pay', 'Bill Pay'
    class TransactionStatus(models.TextChoices):
        PENDING = 'Pending', 'Pending'  
        SUCCESS = 'Success', 'Success'        
        FAILED = 'Failed', 'Failed' 
    from_wallet = models.ForeignKey( 
        Wallet, 
        on_delete=models.CASCADE, 
        related_name='outgoing_transactions',
    )
    to_wallet = models.ForeignKey(
        Wallet, 
        on_delete=models.CASCADE,
        related_name='incoming_transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Transaction'
        ordering = ['-date']
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gte=1.0), name='tx_amount_min_1_0'),
            models.CheckConstraint(check=~models.Q(from_wallet=models.F('to_wallet')), name='tx_from_to_distinct'),
        ]

    def __str__(self):
        return f"TX{self.id} - {self.transaction_type} - {self.amount} EGP"

    def show_details(self):
        return f"{self.date.strftime('%Y-%m-%d %H:%M')} | {self.transaction_type} | From {self.from_wallet or 'System'} -> To {self.to_wallet} | {self.amount} EGP | Status: {self.status}"
    from django.core.exceptions import ValidationError

    def clean(self):
        from .services import Payment
        Payment.validate_transaction(self.from_wallet,self.to_wallet,self.amount)

class CollectionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'

    class ReqType(models.TextChoices):
        COLLECT_MONEY = "Collect Money", "Collect Money"

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    req_type = models.CharField(max_length=50, choices=ReqType.choices, default=ReqType.COLLECT_MONEY)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'CollectionRequest'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name='creq_amount_positive'),
            models.CheckConstraint(check=~models.Q(from_user=models.F('to_user')), name='creq_from_to_distinct'),
        ]

    def clean(self):
        from .services import CollectMoney
        CollectMoney.validate_collection_request(self.from_user,self.to_user,self.amount)
    def __str__(self):
        return f"Request #{self.id}: {self.from_user.name} -> {self.to_user.name} | {self.amount} EGP | {self.status}"
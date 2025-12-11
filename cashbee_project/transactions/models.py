from django.conf import settings
from django.db import models
from wallet.models import Wallet
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

class Transaction(models.Model):
    """Represents a financial transaction between two wallets."""
    class TransactionType(models.TextChoices):
        SEND = 'Send', 'Send'
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'Pending', 'Pending'  
        SUCCESS = 'Success', 'Success'        
        FAILED = 'Failed', 'Failed' 
    
    from_wallet = models.ForeignKey( 
        Wallet, 
        on_delete=models.PROTECT, 
        related_name='sent_transactions',
        help_text="The wallet from which the funds are sent."
    )
    to_wallet = models.ForeignKey(
        Wallet, 
        on_delete=models.PROTECT,
        related_name='received_transactions',
        help_text="The wallet to which the funds are received."
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="The amount of money transferred."
    )
    transaction_type = models.CharField(
        max_length=20, 
        choices=TransactionType.choices,
    )
    status = models.CharField(
        max_length=20, 
        choices=TransactionStatus.choices, 
        default=TransactionStatus.PENDING
    )
    date = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the transaction was created."
    )
    from_wallet_balance_before = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Sender's balance before the transaction."
    )
    to_wallet_balance_before = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Receiver's balance before the transaction."
    )

    class Meta:
        ordering = ['-date']
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

    def clean(self):
        super().clean()
        if self.from_wallet == self.to_wallet:
            raise ValidationError("Cannot send money to the same wallet")
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than 0")

    def __str__(self):
        if self.pk:
            return f"TX{self.id}: {self.from_wallet.user.username} -> {self.to_wallet.user.username} | {self.amount} EGP"
        return f"Transaction: {self.from_wallet.user.username} -> {self.to_wallet.user.username} | {self.amount} EGP"


class CollectionRequest(models.Model):
    """Represents a request for money from one user to another."""
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'

    class ReqType(models.TextChoices):
        COLLECT_MONEY = "Collect Money", "Collect Money"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_collection_requests',
        help_text="The user who is requesting the money."
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_collection_requests',
        help_text="The user from whom the money is requested."
    )
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    req_type = models.CharField(
        max_length=20,
        choices=ReqType.choices,
        default=ReqType.COLLECT_MONEY,
        help_text="Type of collection request"
    )
    status = models.CharField(
        max_length=10, 
        choices=Status.choices, 
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collection_request'
    )
    note = models.CharField(
        max_length=60,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'collection_requests'
        ordering = ['-created_at']
        verbose_name = 'Collection Request'
        verbose_name_plural = 'Collection Requests'
    
    def clean(self):
        super().clean()
        if self.from_user == self.to_user:
            raise ValidationError("Cannot send collection request to yourself")
        if self.amount <= 0:
            raise ValidationError("Amount must be positive")
    
    def __str__(self):
        if self.pk:
            return f"Request #{self.id}: {self.from_user.name} → {self.to_user.name} | {self.amount} EGP ({self.get_status_display()})"
        return f"Request: {self.from_user.name} → {self.to_user.name} | {self.amount} EGP"
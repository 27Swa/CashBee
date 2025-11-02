from django.db import models
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class Wallet(models.Model):
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_wallet'
    )
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    transaction_limit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=5000.00  # PER_OPERATION_LIMIT
    )
    max_limit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=20000.00  # MONTHLY_LIMIT
    )

    class Meta:
        verbose_name = 'Wallet'
        db_table = 'Wallet'
        constraints = [
            models.CheckConstraint(check=models.Q(balance__gte=0), name='wallet_balance_non_negative'),
            models.CheckConstraint(check=models.Q(transaction_limit__gte=0), name='wallet_transaction_limit_non_negative'),
            models.CheckConstraint(check=models.Q(max_limit__gte=models.F('transaction_limit')), name='wallet_max_ge_transaction_limit'),
        ]
    def clean(self):
        if self.max_limit < self.transaction_limit:
            raise ValidationError("Max limit must be greater than or equal to transaction limit.")


    def __str__(self):
        return f"Wallet {self.id} - Balance: {self.balance} EGP - Transaction Limit: {self.transaction_limit} - Max Transaction Limit"


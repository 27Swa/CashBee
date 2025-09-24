from django.db import models
from django.db import models
from django.core.validators import MinValueValidator

class Wallet(models.Model):
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

    def __str__(self):
        return f"Wallet {self.id} - Balance: {self.balance} EGP - Transaction Limit: {self.transaction_limit} - Max Transaction Limit"


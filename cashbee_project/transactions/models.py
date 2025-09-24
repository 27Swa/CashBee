from django.db import models
from wallet.models import Wallet
class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        SEND = 'send', 'Send'
        DONATE = 'donate', 'Donate'
        BILL_PAY = 'bill pay', 'Bill Pay'

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
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Transaction'
        ordering = ['-date']

    def __str__(self):
        return f"TX{self.id} - {self.transaction_type} - {self.amount} EGP"

    def show_details(self):
        return f"{self.date.strftime('%Y-%m-%d %H:%M')} | {self.transaction_type} | From {self.from_wallet or 'System'} -> To {self.to_wallet} | {self.amount} EGP"

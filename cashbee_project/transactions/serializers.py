# transactions/serializers.py
from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [ 'from_wallet', 'to_wallet', 'amount', 'transaction_type', 'date']

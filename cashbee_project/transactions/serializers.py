# transactions/serializers.py
from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    receiver_phone = serializers.CharField(write_only=True)
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type', 'receiver_phone']
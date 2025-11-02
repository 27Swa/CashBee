from rest_framework import serializers
from .models import Wallet

class WalletSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)  # ✅ ADDED

    class Meta:
        model = Wallet
        fields = ['user', 'user_name', 'balance', 'transaction_limit', 'max_limit']
        read_only_fields = ['user', 'balance']  
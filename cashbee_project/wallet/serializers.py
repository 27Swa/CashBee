from rest_framework import serializers
from .models import Wallet

class WalletSerializer(serializers.ModelSerializer):
    #user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'transaction_limit','max_limit']

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from users.models import User

from .services import CollectMoney, TransactionOperation
from .models import Transaction, CollectionRequest

class TransactionSerializer(serializers.ModelSerializer):
    receiver_phone = serializers.CharField(write_only=True)
    
    # Read-only fields for display
    from_user_name = serializers.CharField(source='from_wallet.user.name', read_only=True)
    to_user_name = serializers.CharField(source='to_wallet.user.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'transaction_type', 'receiver_phone', 
            'status', 'date', 'from_user_name', 'to_user_name',
            'from_wallet_balance_before', 'to_wallet_balance_before'
        ]
        read_only_fields = ['id', 'status', 'date', 'from_user_name', 'to_user_name', 
                           'from_wallet_balance_before', 'to_wallet_balance_before']
    
    def validate(self, data):
        """Validation logic before making a transaction"""
        user = self.context['request'].user
        to_phone = data.get('receiver_phone')
        amount = data.get('amount')

        if amount <= 0:
            raise serializers.ValidationError("Invalid amount.")

        if user.phone_number == to_phone:
            raise serializers.ValidationError("Cannot send money to yourself.")

        return data

    def create(self, validated_data):
        """Create a transaction via services layer"""
        from_user = self.context['request'].user
        to_phone = validated_data['receiver_phone']
        amount = validated_data['amount']
        tx_type = validated_data['transaction_type']
        
        operation = TransactionOperation(from_user, to_phone, tx_type, amount)
        
        try:
            tr = operation.execute_transaction()
            return tr
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
    
class CollectMoneySerializer(serializers.ModelSerializer):
    to_phone = serializers.CharField(write_only=True)

    from_user_name = serializers.CharField(source="from_user.name", read_only=True)
    to_user_name = serializers.CharField(source="to_user.name", read_only=True)

    class Meta:
        model = CollectionRequest
        fields = [
            "id", "to_phone", "amount", "req_type", "note", 
            "status", "created_at", "updated_at",
            "from_user_name", "to_user_name"
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at", "from_user_name", "to_user_name"]

    def validate(self, data):
        """Validation logic before creating the request"""
        request = self.context.get("request")  
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")
        from_user = request.user

        to_user = User.objects.filter(phone_number=data["to_phone"]).first()
        if not to_user:
            raise serializers.ValidationError("Receiver not found.")

        if from_user.national_id == to_user.national_id:
            raise serializers.ValidationError("Cannot send a request to yourself.")

        if data["amount"] <= 0:
            raise serializers.ValidationError("Amount must be positive.")

        data["from_user"] = from_user
        data["to_user"] = to_user
        return data

    def create(self, validated_data):
        """Create collect money request through service layer"""
        from_user = validated_data["from_user"]
        to_phone = validated_data["to_phone"]
        amount = validated_data["amount"]
        req_type = validated_data.get("req_type", CollectionRequest.ReqType.COLLECT_MONEY)

        try:
            collect = CollectMoney(from_user, amount, to_phone)
            collection_request = collect.execute()
            return collection_request
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
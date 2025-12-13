from rest_framework import serializers
from .models import Wallet, SystemLimit, PersonalLimit, FamilyLimit


class WalletSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Wallet
        fields = ['user', 'user_name', 'balance', 'updated_at']
        read_only_fields = ['user', 'balance','updated_at']  

class PersonalLimitSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Personal Limits.
    """
    class Meta:
        model = PersonalLimit
        fields = ['per_transaction_limit', 'daily_limit', 'monthly_limit', 'is_active']
    
    def validate(self, data):
        """
        Validate that personal limits don't exceed system limits.
        """
        # Get the instance if we're updating
        instance = self.instance
        
        # Get current values or use data
        per_transaction = data.get('per_transaction_limit', 
                                   instance.per_transaction_limit if instance else None)
        daily = data.get('daily_limit', 
                        instance.daily_limit if instance else None)
        monthly = data.get('monthly_limit', 
                          instance.monthly_limit if instance else None)
        
        # Get system limits
        system_limit = SystemLimit.objects.filter(is_active=True).first()
        if not system_limit:
            raise serializers.ValidationError("No active system limit found.")
        
        # Validate against system limits
        if per_transaction and per_transaction > system_limit.per_transaction_limit:
            raise serializers.ValidationError({
                'per_transaction_limit': f"Cannot exceed system limit of {system_limit.per_transaction_limit}"
            })
        
        if daily and daily > system_limit.daily_limit:
            raise serializers.ValidationError({
                'daily_limit': f"Cannot exceed system limit of {system_limit.daily_limit}"
            })
        
        if monthly and monthly > system_limit.monthly_limit:
            raise serializers.ValidationError({
                'monthly_limit': f"Cannot exceed system limit of {system_limit.monthly_limit}"
            })
        
        return data
class SystemLimitSerializer(serializers.ModelSerializer):
    """
    Serializer for System Limits (admin only).
    NO validation against existing system limits since admins are setting them.
    Only validates logical consistency between the three limit types.
    """
    class Meta:
        model = SystemLimit
        fields = ['per_transaction_limit', 'daily_limit', 'monthly_limit', 'is_active']
    
    def validate(self, data):
        """
        Basic validation for system limits.
        Only validate logical consistency (per_transaction <= daily <= monthly).
        NO validation against existing limits - admins can set any value.
        """
        instance = self.instance
        
        # Get current values or use data
        per_transaction = data.get('per_transaction_limit', 
                                   instance.per_transaction_limit if instance else None)
        daily = data.get('daily_limit', 
                        instance.daily_limit if instance else None)
        monthly = data.get('monthly_limit', 
                          instance.monthly_limit if instance else None)
        
        # Validate logical consistency
        if per_transaction and daily and per_transaction > daily:
            raise serializers.ValidationError({
                'per_transaction_limit': "Per transaction limit cannot exceed daily limit."
            })
        
        if daily and monthly and daily > monthly:
            raise serializers.ValidationError({
                'daily_limit': "Daily limit cannot exceed monthly limit."
            })
        
        # Ensure all values are positive
        if per_transaction and per_transaction <= 0:
            raise serializers.ValidationError({
                'per_transaction_limit': "Must be greater than 0."
            })
        
        if daily and daily <= 0:
            raise serializers.ValidationError({
                'daily_limit': "Must be greater than 0."
            })
        
        if monthly and monthly <= 0:
            raise serializers.ValidationError({
                'monthly_limit': "Must be greater than 0."
            })
        
        return data
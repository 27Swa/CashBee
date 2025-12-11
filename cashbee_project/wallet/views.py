from django.shortcuts import render
from rest_framework import generics
from rest_framework import viewsets, permissions
from .models import Wallet, PersonalLimit, SystemLimit
from .serializers import WalletSerializer, PersonalLimitSerializer

class WalletViewSet(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]  

    def get_object(self):
        return self.request.user.wallet
    
class PersonalLimitView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for viewing and updating the user's personal limits.
    Creates a new personal limit if one does not exist.
    """
    serializer_class = PersonalLimitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Get or create a PersonalLimit for the user.
        When creating, use the system limits as defaults.
        """
        try:
            return PersonalLimit.objects.get(user=self.request.user)
        except PersonalLimit.DoesNotExist:
            # Get system limits to use as defaults
            system_limit = SystemLimit.objects.filter(is_active=True).first()
            if not system_limit:
                # This should never happen due to signals, but handle it gracefully
                raise ValueError("No active system limit found. Please contact administrator.")
            
            # Create PersonalLimit with system limits as defaults
            limit = PersonalLimit.objects.create(
                user=self.request.user,
                per_transaction_limit=system_limit.per_transaction_limit,
                daily_limit=system_limit.daily_limit,
                monthly_limit=system_limit.monthly_limit
            )
            return limit
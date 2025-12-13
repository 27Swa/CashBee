from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework import viewsets, permissions
from .models import Wallet, PersonalLimit, SystemLimit
from .serializers import WalletSerializer, PersonalLimitSerializer,SystemLimitSerializer

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
class SystemLimitView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for admins to view and update system limits.
    Only accessible by admin users (staff or superuser).
    """
    serializer_class = SystemLimitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get the active system limit."""
        system_limit = SystemLimit.objects.filter(is_active=True).first()
        if not system_limit:
            raise ValueError("No active system limit found. Please contact administrator.")
        return system_limit
    
    def retrieve(self, request, *args, **kwargs):
        """Get system limits (admin only)"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "Only administrators can view system limits."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().retrieve(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update system limits (admin only)"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "Only administrators can update system limits."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update system limits (admin only)"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "Only administrators can update system limits."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)
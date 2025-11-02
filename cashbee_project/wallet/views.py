from django.shortcuts import render
from rest_framework import viewsets,permissions
from .models import Wallet
from .serializers import WalletSerializer

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]  
    queryset = Wallet.objects.all()  # ✅ Required for Router

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Wallet.objects.all()
        return Wallet.objects.filter(user=user)
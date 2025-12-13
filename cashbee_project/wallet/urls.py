# wallet/urls.py
from django.urls import path
from .views import WalletViewSet, PersonalLimitView, SystemLimitView

app_name = 'wallet'

urlpatterns = [
    # Wallet endpoints
    path('wallet/', WalletViewSet.as_view(), name='wallet-detail'),
    
    # Personal limits (for regular users)
    path('wallet/limits/personal/', PersonalLimitView.as_view(), name='personal-limits'),
    
    # System limits (for admin users)
    path('wallet/limits/system/', SystemLimitView.as_view(), name='system-limits'),
]
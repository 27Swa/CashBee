from django.urls import path
from .views import WalletViewSet, PersonalLimitView  

urlpatterns = [
    path('', WalletViewSet.as_view(), name='wallet-detail'),  
    path('limits/', PersonalLimitView.as_view(), name='personal-limits'),
]
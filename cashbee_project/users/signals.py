from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=User)
def create_user_dependencies(sender, instance, created, **kwargs):
    """Create wallet and auth token for new users"""
    if created:
        # Create auth token
        Token.objects.get_or_create(user=instance)
        
        # Create wallet
        try:
            from wallet.models import Wallet
            Wallet.objects.get_or_create(user=instance, defaults={'balance': 0})  # ✅ FIXED
        except ImportError:
            pass  # Wallet app not installed

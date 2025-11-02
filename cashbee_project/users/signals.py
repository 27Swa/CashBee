# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from wallet.models import Wallet
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=User)
def create_wallet_for_user(sender, instance, created, **kwargs):
      if created and not instance.wallet:
        wallet = Wallet.objects.create(
            user=instance,  
            balance=0
        )
        instance.wallet = wallet
        instance.save(update_fields=['wallet'])  
        
@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

from django.db.models.signals import pre_save, post_migrate
from django.dispatch import receiver
from .models import SystemLimit

@receiver(pre_save, sender=SystemLimit)
def ensure_single_active_system_limit(sender, instance, **kwargs):
    """
    Ensures that only one SystemLimit instance is active at any given time.
    When a new limit is saved as active, all others are deactivated.
    """
    if instance.is_active:
        # Deactivate all other SystemLimit instances
        SystemLimit.objects.exclude(pk=instance.pk).update(is_active=False)

@receiver(post_migrate)
def create_default_system_limit(sender, **kwargs):
    """
    Creates a default SystemLimit instance after migrations if none exist.
    This ensures the system always has a configured limit.
    """
    if sender.name == 'wallet':
        if not SystemLimit.objects.exists():
            SystemLimit.objects.create(
                per_transaction_limit=1000.00,
                daily_limit=5000.00,
                monthly_limit=20000.00,
                is_active=True
            )
            print("Default system limit created.")

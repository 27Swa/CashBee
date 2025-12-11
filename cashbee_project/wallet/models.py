from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from decimal import Decimal

class Wallet(models.Model):
    """Represents a user's e-wallet, holding their balance."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'  # ✅ FIXED: Changed from 'user_wallet'
    )
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
        db_table = 'wallets'

    def __str__(self):
        return f"Wallet for {self.user.username} | Balance: {self.balance} EGP"

class BaseLimit(models.Model):
    """Abstract base model for different types of transaction limits."""
    per_transaction_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Maximum amount allowed in a single transaction."
    )
    daily_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Maximum total amount allowed in a 24-hour period."
    )
    monthly_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Maximum total amount allowed in a calendar month."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this limit is active."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.per_transaction_limit and self.daily_limit and self.per_transaction_limit > self.daily_limit:
            raise ValidationError("Per transaction limit cannot exceed daily limit.")
        if self.daily_limit and self.monthly_limit and self.daily_limit > self.monthly_limit:
            raise ValidationError("Daily limit cannot exceed monthly limit.")

    def __str__(self):
        return f"Tx: {self.per_transaction_limit}, Daily: {self.daily_limit}, Monthly: {self.monthly_limit}"

class SystemLimit(BaseLimit):
    """System-wide transaction limits set by the administrator."""
    class Meta(BaseLimit.Meta):
        db_table = 'system_limits'
        verbose_name = 'System Limit'
        verbose_name_plural = 'System Limits'

class PersonalLimit(BaseLimit):
    """Optional personal limits that a user sets for their own wallet."""
    user = models.OneToOneField(  # ✅ FIXED: Changed from wallet to user
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='personal_limit',
        help_text="The user to which these personal limits apply."
    )

    class Meta(BaseLimit.Meta):
        db_table = 'personal_limits'
        verbose_name = 'Personal Limit'
        verbose_name_plural = 'Personal Limits'

    def clean(self):
        super().clean()
        # Import here to avoid circular imports
        from .services import get_effective_limits
        
        try:
            # Get limits excluding this personal limit to avoid recursion
            effective_limits = get_effective_limits(self.user, exclude_personal=True)
            
            if self.per_transaction_limit > effective_limits['per_transaction']:
                raise ValidationError(
                    f"Personal per-transaction limit ({self.per_transaction_limit}) "
                    f"cannot exceed the current effective limit ({effective_limits['per_transaction']})."
                )
            if self.daily_limit > effective_limits['daily']:
                raise ValidationError(
                    f"Personal daily limit ({self.daily_limit}) "
                    f"cannot exceed the current effective limit ({effective_limits['daily']})."
                )
            if self.monthly_limit > effective_limits['monthly']:
                raise ValidationError(
                    f"Personal monthly limit ({self.monthly_limit}) "
                    f"cannot exceed the current effective limit ({effective_limits['monthly']})."
                )
        except Exception:
            # Fallback: validate against system limits only
            system_limit = SystemLimit.objects.filter(is_active=True).first()
            if system_limit:
                if self.per_transaction_limit > system_limit.per_transaction_limit:
                    raise ValidationError(
                        f"Personal per-transaction limit cannot exceed system limit of {system_limit.per_transaction_limit}."
                    )
                if self.daily_limit > system_limit.daily_limit:
                    raise ValidationError(
                        f"Personal daily limit cannot exceed system limit of {system_limit.daily_limit}."
                    )
                if self.monthly_limit > system_limit.monthly_limit:
                    raise ValidationError(
                        f"Personal monthly limit cannot exceed system limit of {system_limit.monthly_limit}."
                    )

class FamilyLimit(BaseLimit):
    """Limits set by a parent for a child's wallet."""
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='family_limits_set',
        help_text="The parent user setting the limits."
    )
    child = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='family_limit',
        help_text="The child user to whom the limits apply."
    )

    class Meta(BaseLimit.Meta):
        db_table = 'family_limits'
        verbose_name = 'Family Limit'
        verbose_name_plural = 'Family Limits'
        unique_together = ('parent', 'child')

    def clean(self):
        super().clean()
        from users.models import UsersRole
        
        if self.parent == self.child:
            raise ValidationError("Parent and child cannot be the same user.")
        
        # ✅ FIXED: Check using family relationship and roles
        if self.child.role != UsersRole.CHILD:
            raise ValidationError("Family limits can only be set for child users.")
        
        if self.parent.role != UsersRole.PARENT:
            raise ValidationError("Only parents can set family limits.")
        
        # Check if they're in the same family
        if not self.parent.family or not self.child.family:
            raise ValidationError("Both users must be in a family.")
        
        if self.parent.family != self.child.family:
            raise ValidationError(
                f"You can only set limits for children in your family. "
                f"{self.child.username} is not in your family."
            )

        # Validate against system limits
        system_limit = SystemLimit.objects.filter(is_active=True).first()
        if not system_limit:
            raise ValidationError("Cannot set family limits because no active system limit is configured.")

        if self.per_transaction_limit > system_limit.per_transaction_limit:
            raise ValidationError(
                f"Per-transaction limit cannot exceed the system limit of {system_limit.per_transaction_limit}."
            )
        if self.daily_limit > system_limit.daily_limit:
            raise ValidationError(
                f"Daily limit cannot exceed the system limit of {system_limit.daily_limit}."
            )
        if self.monthly_limit > system_limit.monthly_limit:
            raise ValidationError(
                f"Monthly limit cannot exceed the system limit of {system_limit.monthly_limit}."
            )
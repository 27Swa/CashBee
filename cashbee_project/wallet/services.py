"""
Helper functions for wallet operations and limit checking
"""
from decimal import Decimal
from .models import SystemLimit, PersonalLimit, FamilyLimit
from users.models import UsersRole


def get_effective_limits(user, exclude_personal=False):
    """
    Get the most restrictive limits for a user.
    Priority: Personal < Family < System (uses minimum of all applicable)
    
    Args:
        user: User object
        exclude_personal: If True, exclude personal limits from calculation (used during validation)
        
    Returns:
        dict: {'per_transaction': Decimal, 'daily': Decimal, 'monthly': Decimal}
    """
    # Get system limits (always applies)
    system_limit = SystemLimit.objects.filter(is_active=True).first()
    if not system_limit:
        raise ValueError("System limits not configured. Contact administrator.")
    
    limits = {
        'per_transaction': system_limit.per_transaction_limit,
        'daily': system_limit.daily_limit,
        'monthly': system_limit.monthly_limit
    }
    
    # Check if user has family limits (for children)
    if user.role == UsersRole.CHILD:
        try:
            family_limit = FamilyLimit.objects.get(child=user, is_active=True)
            limits['per_transaction'] = min(limits['per_transaction'], family_limit.per_transaction_limit)
            limits['daily'] = min(limits['daily'], family_limit.daily_limit)
            limits['monthly'] = min(limits['monthly'], family_limit.monthly_limit)
        except FamilyLimit.DoesNotExist:
            pass  # No family limit set, use system limits
    
    # Check if user has personal limits (excluding if requested)
    if not exclude_personal:
        try:
            personal_limit = PersonalLimit.objects.get(user=user, is_active=True)
            limits['per_transaction'] = min(limits['per_transaction'], personal_limit.per_transaction_limit)
            limits['daily'] = min(limits['daily'], personal_limit.daily_limit)
            limits['monthly'] = min(limits['monthly'], personal_limit.monthly_limit)
        except PersonalLimit.DoesNotExist:
            pass  # No personal limit set
    
    return limits
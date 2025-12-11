from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
from datetime import date, datetime
import random
import string
from .validations import *
from .managers import CustomUserManager

class UsersRole(models.TextChoices):
    """User roles in the system"""
    USER = 'User', 'User'          # Regular user (18+, no family yet)
    PARENT = 'Parent', 'Parent'    # Parent in a family (22+)
    CHILD = 'Child', 'Child'       # Child in a family (8-17)

class Family(models.Model):
    """
    Family entity that groups users together.
    Can have multiple parents and children.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Unique family name"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'families'
        verbose_name = 'Family'
        verbose_name_plural = 'Families'
    
    def __str__(self):
        return self.name
    
    def clean(self):
        super().clean()
        if not self.name or len(self.name.strip()) < 3:
            raise ValidationError({
                'name': 'Family name must be at least 3 characters'
            })
    
    def get_parents(self):
        """Get all parents in this family"""
        return self.members.filter(role=UsersRole.PARENT)
    
    def get_children(self):
        """Get all children in this family"""
        return self.members.filter(role=UsersRole.CHILD)
    
    def get_members_count(self):
        """Get total number of family members"""
        return self.members.count()
    
class User(AbstractUser):
    """
    Custom user model that can be a parent or a child.
    Username is auto-generated from first_name + last_name + random digits.
    """
    family = models.ForeignKey(
        Family,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        help_text="Family this user belongs to"
    )    
    role = models.CharField(
        max_length=10,
        choices=UsersRole.choices,
        default=UsersRole.USER,
        help_text="User role: USER (default), PARENT, or CHILD"
    )
    phone_number = PhoneNumberField(
        unique=True,
        help_text="User's phone number"
    )
    national_id = models.CharField(
        max_length=14, 
        unique=True, 
        null=True,
        blank=True,
        help_text="14-digit National ID (optional, can be added later)"
    )
    failed_attempts = models.IntegerField(default=0)  
    lock_time = models.DateTimeField(null=True, blank=True)
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="User's date of birth, derived from National ID."
    )

    # Use custom manager
    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.get_full_name() or self.username
    
    @property
    def name(self):
        """Return full name"""
        return self.get_full_name() or self.first_name or self.username
   
    def clean(self):
        super().clean()        
        if self.national_id:
            try:
                age = AgeCalculation.calculate_age_from_nid(self.national_id)
                
                # Auto-set date_of_birth from national_id if not set
                if not self.date_of_birth:
                    self.date_of_birth = AgeCalculation.extract_date_of_birth(self.national_id)
                
                # Role-based validation
                if self.role == UsersRole.CHILD:
                    child_validator = ValidatorContext(ChildNationalIDValidationStrategy())
                    if not child_validator.validate(self.national_id):
                        raise ValidationError(child_validator.get_error())
                else:
                    adult_validator = ValidatorContext(NationalIDValidationStrategy())
                    if not adult_validator.validate(self.national_id):
                        raise ValidationError(adult_validator.get_error())
            except ValueError as e:
                raise ValidationError(f"Invalid National ID: {e}")

    def save(self, *args, **kwargs):
        # Only call full_clean if this is not being called from create_user
        # (create_user handles password hashing and validation)
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        
        super().save(*args, **kwargs)
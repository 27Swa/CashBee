from django.contrib.auth.models import BaseUserManager
import random
import string


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where username is auto-generated and phone_number is required.
    """
    
    def _generate_username(self, first_name='', last_name=''):
        """Generate unique username from first_name + last_name + random numbers"""
        base_username = f"{first_name}{last_name}".lower()
        # Remove spaces and special characters
        base_username = ''.join(c for c in base_username if c.isalnum())
        
        # If base is empty, use 'user'
        if not base_username:
            base_username = 'user'
        
        # Try to generate unique username
        for _ in range(10):
            random_suffix = ''.join(random.choices(string.digits, k=6))
            username = f"{base_username}{random_suffix}"
            
            if not self.model.objects.filter(username=username).exists():
                return username
        
        # Fallback: use timestamp + random
        return f"{base_username}{random.randint(100000, 999999)}"
    
    def create_user(self, phone_number, password=None, username=None, **extra_fields):
        """
        Create and save a regular user with the given phone_number and password.
        Username is auto-generated if not provided.
        """
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        
        # Auto-generate username if not provided
        if not username:
            first_name = extra_fields.get('first_name', '')
            last_name = extra_fields.get('last_name', '')
            username = self._generate_username(first_name, last_name)
        
        # Set default values for required fields
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        
        user = self.model(
            username=username,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db, skip_validation=True)
        return user
    
    def create_superuser(self, phone_number, password=None, username=None, **extra_fields):
        """
        Create and save a superuser with the given phone_number and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone_number, password, username, **extra_fields)
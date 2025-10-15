from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.forms import ValidationError
from .validations import ValidationCheck  
from wallet.models import Wallet

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number must be set")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)
    
class UsersRole(models.TextChoices):
    PARENT = "Parent", "Parent"
    CHILD = "Child", "Child"
    USER = "User", "User"

class Family(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Family"
        verbose_name_plural = "Families"
        db_table = 'Families'

class User(AbstractUser):
    phone_number = models.CharField(max_length=11, unique=True, null=False, blank=False)
    national_id = models.CharField(primary_key=True,max_length=14, null=False, blank=False)
    role = models.CharField(max_length=10, choices=UsersRole.choices, default=UsersRole.USER)
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True)
    failed_attempts = models.IntegerField(default=0)  
    lock_time = models.DateTimeField(null=True, blank=True)
    wallet = models.OneToOneField(Wallet,on_delete=models.PROTECT,null=True,blank=True)
    
    USERNAME_FIELD = 'national_id'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    objects = UserManager()
    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"
        db_table = 'Person' 

    def __str__(self):
        return self.name
    def clean(self):
        vc = ValidationCheck(
            name=self.name,
            phone=self.phone_number,
            password=self.password,
            national_id=self.national_id,
            child=(self.role == "Child")
        )
        msg = vc.check()
        if msg:
            raise ValidationError(msg)
    @property
    def name(self):
        return self.first_name +" "+self.last_name


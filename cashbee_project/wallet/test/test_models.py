from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import TestCase
from wallet.models import SystemLimit, FamilyLimit, Wallet, PersonalLimit
from users.models import UsersRole, Family

User = get_user_model()


class LimitModelsTestCase(TestCase):
    def setUp(self):
        # Clear any existing system limits (including the one from signal)
        SystemLimit.objects.all().delete()
        
        # Create family first
        self.family = Family.objects.create(name="TestFamily")
        
        # Create parent user (22+ years old from national ID)
        self.user_parent = User.objects.create_user(
            phone_number='+201234567890',
            national_id='30001010101011',  # Born 2000-01-01, 24+ years old
            first_name='Parent',
            last_name='User',
            password='Parent@123',
            role=UsersRole.PARENT
        )
        self.user_parent.family = self.family
        self.user_parent.save(skip_validation=True)
        
        # Create child user (8-17 years old from national ID)
        self.user_child = User.objects.create_user(
            phone_number='+201987654321',
            national_id='31501010101012',  # Born 2015-01-01, around 9 years old
            first_name='Child',
            last_name='User',
            password='Child@123',
            role=UsersRole.CHILD
        )
        self.user_child.family = self.family
        self.user_child.save(skip_validation=True)
        
        # Create system limit
        self.system_limit = SystemLimit.objects.create(
            per_transaction_limit=Decimal('1000.00'),
            daily_limit=Decimal('5000.00'),
            monthly_limit=Decimal('20000.00')
        )
        
        # Create family limit
        self.family_limit = FamilyLimit.objects.create(
            parent=self.user_parent,
            child=self.user_child,
            per_transaction_limit=Decimal('100.00'),
            daily_limit=Decimal('500.00'),
            monthly_limit=Decimal('2000.00')
        )
        
        # Create personal limit
        self.personal_limit = PersonalLimit.objects.create(
            user=self.user_child,
            per_transaction_limit=Decimal('50.00'),
            daily_limit=Decimal('200.00'),
            monthly_limit=Decimal('1000.00')
        )
        
        # Get wallet created by signal
        self.wallet = self.user_child.wallet
        self.wallet.balance = Decimal('1000.00')
        self.wallet.save()

    def test_system_limit_creation(self):
        self.assertEqual(SystemLimit.objects.count(), 1)
        self.assertEqual(self.system_limit.per_transaction_limit, Decimal('1000.00'))

    def test_family_limit_creation(self):
        self.assertEqual(FamilyLimit.objects.count(), 1)
        self.assertEqual(self.family_limit.child, self.user_child)

    def test_personal_limit_creation(self):
        # Should have 1 personal limit for child
        self.assertEqual(PersonalLimit.objects.filter(user=self.user_child).count(), 1)
        self.assertEqual(self.personal_limit.user, self.user_child)

    def test_wallet_creation(self):
        # Should have 2 wallets (parent and child, created by signal)
        self.assertGreaterEqual(Wallet.objects.count(), 2)
        self.assertEqual(self.wallet.user, self.user_child)

    def test_get_effective_limits(self):
        from wallet.services import get_effective_limits
        effective_limits = get_effective_limits(self.user_child)
        self.assertEqual(effective_limits['per_transaction'], Decimal('50.00'))
        self.assertEqual(effective_limits['daily'], Decimal('200.00'))
        self.assertEqual(effective_limits['monthly'], Decimal('1000.00'))

    def test_get_effective_limits_no_personal(self):
        from wallet.services import get_effective_limits
        self.personal_limit.delete()
        effective_limits = get_effective_limits(self.user_child)
        self.assertEqual(effective_limits['per_transaction'], Decimal('100.00'))
        self.assertEqual(effective_limits['daily'], Decimal('500.00'))
        self.assertEqual(effective_limits['monthly'], Decimal('2000.00'))

    def test_get_effective_limits_no_family(self):
        from wallet.services import get_effective_limits
        self.family_limit.delete()
        effective_limits = get_effective_limits(self.user_child)
        self.assertEqual(effective_limits['per_transaction'], Decimal('50.00'))
        self.assertEqual(effective_limits['daily'], Decimal('200.00'))
        self.assertEqual(effective_limits['monthly'], Decimal('1000.00'))

    def test_system_limit_clean_validation(self):
        # Per transaction > daily
        limit = SystemLimit(per_transaction_limit=10, daily_limit=5, monthly_limit=20)
        with self.assertRaises(ValidationError):
            limit.full_clean()
        
        # Daily > monthly
        limit = SystemLimit(per_transaction_limit=5, daily_limit=10, monthly_limit=5)
        with self.assertRaises(ValidationError):
            limit.full_clean()

    def test_family_limit_clean_validation(self):
        # Per transaction > daily
        self.family_limit.per_transaction_limit = 2000
        self.family_limit.daily_limit = 1000
        with self.assertRaises(ValidationError):
            self.family_limit.full_clean()
        self.family_limit.per_transaction_limit = 100  # reset

        # Daily > monthly
        self.family_limit.daily_limit = 3000
        self.family_limit.monthly_limit = 2000
        with self.assertRaises(ValidationError):
            self.family_limit.full_clean()
        self.family_limit.daily_limit = 500  # reset

        # Exceeds system limit
        self.family_limit.per_transaction_limit = self.system_limit.per_transaction_limit + 1
        with self.assertRaises(ValidationError):
            self.family_limit.full_clean()

    def test_personal_limit_clean_validation(self):
        # Per transaction > daily
        self.personal_limit.per_transaction_limit = 300
        self.personal_limit.daily_limit = 200
        with self.assertRaises(ValidationError):
            self.personal_limit.full_clean()
        self.personal_limit.per_transaction_limit = 50  # reset

        # Daily > monthly
        self.personal_limit.daily_limit = 1500
        self.personal_limit.monthly_limit = 1000
        with self.assertRaises(ValidationError):
            self.personal_limit.full_clean()
        self.personal_limit.daily_limit = 200  # reset

        # Exceeds effective limits (family limit in this case)
        # Family limit: per_transaction=100, daily=500, monthly=2000
        # Current personal limit: 50, 200, 1000
        # Try to set personal limit higher than family limit
        
        # Create a new personal limit that exceeds family limit
        bad_personal_limit = PersonalLimit(
            user=self.user_child,
            per_transaction_limit=Decimal('150.00'),  # Exceeds family's 100
            daily_limit=Decimal('400.00'),  # Below family's 500
            monthly_limit=Decimal('1500.00')  # Below family's 2000
        )
        with self.assertRaises(ValidationError):
            bad_personal_limit.full_clean()

    def test_wallet_str_representation(self):
        expected = f"Wallet for {self.wallet.user.username} | Balance: {self.wallet.balance} EGP"
        self.assertEqual(str(self.wallet), expected)

    def test_balance_negativity(self):
        self.wallet.balance = -100
        with self.assertRaises(ValidationError):
            self.wallet.full_clean()
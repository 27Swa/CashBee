from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from wallet.models import Wallet, PersonalLimit, SystemLimit

User = get_user_model()


class WalletViewSetTestCase(TestCase):
    """Test cases for WalletViewSet (RetrieveAPIView)"""
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = APIClient()
        
        # Clear existing system limits and create new one
        SystemLimit.objects.all().delete()
        SystemLimit.objects.create(
            per_transaction_limit=Decimal('1000.00'),
            daily_limit=Decimal('5000.00'),
            monthly_limit=Decimal('20000.00'),
            is_active=True
        )
        
        # Create test users (wallets will be auto-created by signal)
        self.user1 = User.objects.create_user(
            phone_number='+201111111111',
            first_name='Test',
            last_name='User1',
            password='Test@12345'
        )
        self.user2 = User.objects.create_user(
            phone_number='+201222222222',
            first_name='Test',
            last_name='User2',
            password='Test@12345'
        )
        
        # Update wallet balances
        self.user1.wallet.balance = Decimal('100.00')
        self.user1.wallet.save()
        
        self.user2.wallet.balance = Decimal('200.00')
        self.user2.wallet.save()
        
        # URL matches your main urls.py configuration
        self.url = '/wallets'
        
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access wallet endpoint"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_user_can_view_own_wallet(self):
        """Test that authenticated users can view their own wallet"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['balance']), Decimal('100.00'))
        
    def test_different_users_see_different_wallets(self):
        """Test that each user sees their own wallet data"""
        # User 1 sees their wallet
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['balance']), Decimal('100.00'))
        
        # User 2 sees their wallet
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['balance']), Decimal('200.00'))
    
    def test_wallet_is_read_only(self):
        """Test that wallet endpoint is read-only (no PUT/PATCH/DELETE)"""
        self.client.force_authenticate(user=self.user1)
        
        # Try PUT
        response = self.client.put(self.url, {'balance': '500.00'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try PATCH
        response = self.client.patch(self.url, {'balance': '500.00'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try DELETE
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_post_not_allowed(self):
        """Test that POST is not allowed"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.url, {'balance': '500.00'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class PersonalLimitViewTestCase(TestCase):
    """Test cases for PersonalLimitView"""
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = APIClient()
        
        # Clear existing system limits and create new one
        SystemLimit.objects.all().delete()
        self.system_limit = SystemLimit.objects.create(
            per_transaction_limit=Decimal('1000.00'),
            daily_limit=Decimal('5000.00'),
            monthly_limit=Decimal('20000.00'),
            is_active=True
        )
        
        # Create test user (wallet will be auto-created by signal)
        self.user = User.objects.create_user(
            phone_number='+201333333333',
            first_name='Test',
            last_name='User',
            password='Test@12345'
        )
        
        # Update wallet balance
        self.user.wallet.balance = Decimal('100.00')
        self.user.wallet.save()
        
        # URL matches your main urls.py configuration
        self.url = '/limits/my/'
        
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access personal limit"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_creates_personal_limit_if_not_exists(self):
        """Test that GET request creates PersonalLimit if it doesn't exist"""
        self.client.force_authenticate(user=self.user)
        
        # Ensure no PersonalLimit exists
        self.assertFalse(PersonalLimit.objects.filter(user=self.user).exists())
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PersonalLimit.objects.filter(user=self.user).exists())
        
    def test_get_returns_existing_personal_limit(self):
        """Test that GET returns existing PersonalLimit"""
        # Create a PersonalLimit
        limit = PersonalLimit.objects.create(
            user=self.user,
            per_transaction_limit=Decimal('200.00'),
            daily_limit=Decimal('500.00'),
            monthly_limit=Decimal('5000.00')
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['per_transaction_limit']), Decimal('200.00'))
        self.assertEqual(Decimal(response.data['daily_limit']), Decimal('500.00'))
        self.assertEqual(Decimal(response.data['monthly_limit']), Decimal('5000.00'))
    
    def test_update_personal_limit_with_put(self):
        """Test updating PersonalLimit with PUT request"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'per_transaction_limit': '500.00',
            'daily_limit': '1000.00',
            'monthly_limit': '10000.00'
        }
        
        response = self.client.put(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the update
        limit = PersonalLimit.objects.get(user=self.user)
        self.assertEqual(limit.per_transaction_limit, Decimal('500.00'))
        self.assertEqual(limit.daily_limit, Decimal('1000.00'))
        self.assertEqual(limit.monthly_limit, Decimal('10000.00'))
    
    def test_partial_update_with_patch(self):
        """Test partial update of PersonalLimit with PATCH request"""
        # Create initial limit
        PersonalLimit.objects.create(
            user=self.user,
            per_transaction_limit=Decimal('200.00'),
            daily_limit=Decimal('500.00'),
            monthly_limit=Decimal('5000.00')
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Update only daily_limit
        data = {'daily_limit': '750.00'}
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify partial update
        limit = PersonalLimit.objects.get(user=self.user)
        self.assertEqual(limit.daily_limit, Decimal('750.00'))
        self.assertEqual(limit.per_transaction_limit, Decimal('200.00'))  # Unchanged
        self.assertEqual(limit.monthly_limit, Decimal('5000.00'))  # Unchanged
    
    def test_user_cannot_access_other_users_limit(self):
        """Test that users can only access their own personal limits"""
        # Create another user with wallet and limit
        other_user = User.objects.create_user(
            phone_number='+201444444444',
            first_name='Other',
            last_name='User',
            password='Test@12345'
        )
        
        PersonalLimit.objects.create(
            user=other_user,
            per_transaction_limit=Decimal('300.00'),
            daily_limit=Decimal('999.00'),
            monthly_limit=Decimal('9999.00')
        )
        
        # Authenticate as first user
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        # Should get their own limit (or create new one), not the other user's
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # If limit was created, it shouldn't have the other user's values
        if PersonalLimit.objects.filter(user=self.user).exists():
            limit = PersonalLimit.objects.get(user=self.user)
            self.assertNotEqual(limit.daily_limit, Decimal('999.00'))
    
    def test_auto_create_on_update(self):
        """Test that PersonalLimit is auto-created when updating non-existent limit"""
        self.client.force_authenticate(user=self.user)
        
        # Ensure no limit exists
        self.assertFalse(PersonalLimit.objects.filter(user=self.user).exists())
        
        # Try to update
        data = {
            'per_transaction_limit': '100.00',
            'daily_limit': '300.00',
            'monthly_limit': '3000.00'
        }
        response = self.client.put(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify it was created and updated
        self.assertTrue(PersonalLimit.objects.filter(user=self.user).exists())
        limit = PersonalLimit.objects.get(user=self.user)
        self.assertEqual(limit.per_transaction_limit, Decimal('100.00'))
        self.assertEqual(limit.daily_limit, Decimal('300.00'))
    
    def test_cannot_exceed_system_limits(self):
        """Test that personal limits cannot exceed system limits"""
        self.client.force_authenticate(user=self.user)
        
        # Try to set limits higher than system limits
        data = {
            'per_transaction_limit': '2000.00',  # System is 1000
            'daily_limit': '10000.00',  # System is 5000
            'monthly_limit': '50000.00'  # System is 20000
        }
        response = self.client.put(self.url, data, format='json')
        
        # Should fail validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
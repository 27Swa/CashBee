from django.core.exceptions import ValidationError
from django.test import TestCase
from wallet.models import Wallet, SystemLimit
from users.models import User
from decimal import Decimal
from ..models import Transaction, CollectionRequest


class TransactionTest(TestCase):
    def setUp(self):
        # Clear system limits and create one
        SystemLimit.objects.all().delete()
        SystemLimit.objects.create(
            per_transaction_limit=Decimal('1000.00'),
            daily_limit=Decimal('5000.00'),
            monthly_limit=Decimal('20000.00'),
            is_active=True
        )
        
        # Create users (wallets will be auto-created by signal)
        self.user1 = User.objects.create_user(
            phone_number='+201111111111',
            national_id='30001010101011',
            first_name='Test',
            last_name='User1',
            password='Test@12345'
        )
        self.user2 = User.objects.create_user(
            phone_number='+201222222222',
            national_id='30001010101012',
            first_name='Test',
            last_name='User2',
            password='Test@12345'
        )
        
        # Get the auto-created wallets
        self.wallet1 = self.user1.wallet
        self.wallet2 = self.user2.wallet
        
        # Set balances
        self.wallet1.balance = Decimal('100000.00')
        self.wallet1.save()
        self.wallet2.balance = Decimal('500.00')
        self.wallet2.save()
        
        # Create a valid transaction
        self.transaction = Transaction.objects.create(
            from_wallet=self.wallet1,
            to_wallet=self.wallet2,
            amount=Decimal('100.00'),
            transaction_type=Transaction.TransactionType.SEND,
            from_wallet_balance_before=self.wallet1.balance,
            to_wallet_balance_before=self.wallet2.balance
        )
    
    def test_amount_negativity(self):
        self.transaction.amount = Decimal('-100.00')
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()
    
    def test_cannot_send_to_same_wallet(self):
        self.transaction.to_wallet = self.wallet1
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()
    
    def test_cannot_send_amount_less_than_minimum(self):
        self.transaction.amount = Decimal('0.00')
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()
    
    def test_valid_transaction_passes_validation(self):
        try:
            self.transaction.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for a valid transaction")
    
    def test_transaction_string_representation(self):
        """Test the string representation of a transaction"""
        self.assertIn("TX", str(self.transaction))
        self.assertIn(self.user1.username, str(self.transaction))
        self.assertIn(self.user2.username, str(self.transaction))
    
    def test_transaction_default_status(self):
        """Test that default status is PENDING"""
        self.assertEqual(self.transaction.status, Transaction.TransactionStatus.PENDING)


class CollectionRequestTest(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            first_name="Sondos",
            last_name="Ali",
            national_id="30305270101022",
            phone_number="+201000000001",
            password="So@1234567"
        )
        self.user2 = User.objects.create_user(
            first_name="Nada",
            last_name="Hassan",
            national_id="30305180101033",
            phone_number="+201000000002",
            password="Na@1234567"
        )
        
        # Create a valid request
        self.valid_request = CollectionRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            amount=Decimal('100.00')
        )

    def test_valid_collection_request(self):
        try:
            self.valid_request.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for a valid request")

    def test_cannot_send_request_to_self(self):
        bad_request = CollectionRequest(
            from_user=self.user1,
            to_user=self.user1,
            amount=Decimal('100.00')
        )
        with self.assertRaises(ValidationError):
            bad_request.full_clean()

    def test_amount_must_be_positive(self):
        self.valid_request.amount = Decimal('0.00')
        with self.assertRaises(ValidationError):
            self.valid_request.full_clean()

    def test_default_status_is_pending(self):
        self.assertEqual(self.valid_request.status, CollectionRequest.Status.PENDING)

    def test_str_representation(self):
        """Test string representation"""
        self.assertIn("Request #", str(self.valid_request))
        self.assertIn(self.user1.name, str(self.valid_request))
        self.assertIn(self.user2.name, str(self.valid_request))

    def test_ordering_by_created_at_descending(self):
        req1 = CollectionRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            amount=Decimal('10.00')
        )
        req2 = CollectionRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            amount=Decimal('20.00')
        )

        requests = list(CollectionRequest.objects.all())
        # req2 was created last, so it should be first in descending order
        self.assertEqual(requests[0], req2)
        self.assertEqual(requests[1], req1)
from django.forms import ValidationError
from django.test import TestCase
from wallet.models import Wallet
from users.models import User
from ..models import Transaction,CollectionRequest

class TransactionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.wallet1 = Wallet.objects.create(balance=100000)
        cls.wallet2 = Wallet.objects.create(balance=500)
        
        cls.transaction = Transaction.objects.create(
            from_wallet = cls.wallet1,
            to_wallet = cls.wallet2,
            amount = 100,
            transaction_type = 'Send'
        )
    """
    amount check --> negativity, limit, balance enough, balance not enough
    from != to
    """
    def test_amount_negativity(self):
        self.transaction.amount = -100
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()
    
    def test_cannot_send_to_same_wallet(self):
        self.transaction.to_wallet = self.wallet1
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()
    
    def test_cannot_send_amount_less_than_minimum(self):
        self.transaction.amount = -1
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()
    
    def test_cannot_send_balance_less_than_amount(self):
        self.transaction.amount = 2000
        self.transaction.from_wallet.balance = 1000  
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()

    def test_amount_exceed_per_operation_limit(self):
        self.transaction.amount = 10000
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()

    def test_valid_transaction_passes_validation(self):
        try:
            self.transaction.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for a valid transaction")


class CollectionRequestTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(
            first_name="Sondos", last_name="Ali",
            national_id="30305270101022", phone_number="01000000001",
            password="So@1234567"
        )
        cls.user2 = User.objects.create(
            first_name="Nada", last_name="Hassan",
            national_id="30305180101033", phone_number="01000000002",
            password="Na@1234567"
        )
        cls.valid_request = CollectionRequest(
            from_user=cls.user1,
            to_user=cls.user2,
            amount=100
        )

    def test_valid_collection_request(self):
        try:
            self.valid_request.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for a valid request")

    def test_cannot_send_request_to_self(self):
        self.valid_request.to_user = self.user1
        with self.assertRaises(ValidationError):
            self.valid_request.full_clean()

    def test_amount_must_be_positive(self):
        self.valid_request.amount = 0
        with self.assertRaises(ValidationError):
            self.valid_request.full_clean()

    def test_default_status_is_pending(self):
        self.assertEqual(self.valid_request.status, CollectionRequest.Status.PENDING)

    def test_str_representation(self):
       
        self.assertIn("Request #", str(self.valid_request))
        self.assertIn(self.user1.name, str(self.valid_request))
        self.assertIn(self.user2.name, str(self.valid_request))

    def test_ordering_by_created_at_descending(self):
        req1 = CollectionRequest.objects.create(from_user=self.user1, to_user=self.user2, amount=10)
        req2 = CollectionRequest.objects.create(from_user=self.user1, to_user=self.user2, amount=20)

        requests = list(CollectionRequest.objects.all())
        self.assertEqual(requests[0], req2)
        self.assertEqual(requests[1], req1)


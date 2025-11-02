from decimal import Decimal
from django.forms import ValidationError
from django.test import TestCase
from ..models import Wallet
class WalletTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.wallet = Wallet.objects.create(balance = 10000)
    def test_wallet_str_representation(self):
        expected = f"Wallet {self.wallet.id} - Balance: {self.wallet.balance} EGP - Transaction Limit: {self.wallet.transaction_limit} - Max Transaction Limit"
        self.assertEqual(str(self.wallet), expected)
    def test_balance_negativity(self):
        self.wallet.balance = -100
        with self.assertRaises(ValidationError):
            self.wallet.full_clean()
    def test_limit_negativity(self):
        self.wallet.transaction_limit = -100
        with self.assertRaises(ValidationError):
            self.wallet.full_clean()
    def test_maxlimit_negativity(self):
        self.wallet.max_limit = -100
        with self.assertRaises(ValidationError):
            self.wallet.full_clean()    
    def test_wallet_max_limit_must_be_greater_than_or_equal_transaction_limit(self):
        self.wallet.transaction_limit = Decimal("10000.00")
        self.wallet.max_limit = Decimal("5000.00")  
        with self.assertRaises(ValidationError):
            self.wallet.full_clean()      
    def test_wallet_max_limit_equal_transaction_limit_is_valid(self):
        self.wallet.transaction_limit = Decimal("5000.00")
        self.wallet.max_limit = Decimal("5000.00")  

        try:
            self.wallet.full_clean()  
        except ValidationError:
            self.fail("ValidationError raised when max_limit equals transaction_limit")
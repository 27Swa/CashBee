from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from wallet.models import Wallet
from decimal import Decimal
from django.db.models import ProtectedError

class WalletViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            phone_number="01000000001",
            national_id="30305270989876",
            first_name="Sondos",
            last_name="Ali",
            password="So@1234567"
        )
        cls.wallet = Wallet.objects.get(user=cls.user)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/wallets/"

    def test_list_wallets(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["balance"], "0.00")

    def test_retrieve_wallet(self):
        response = self.client.get(f"{self.url}{self.wallet.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.wallet.id)

    def test_update_wallet_balance(self):
        data = {"balance": 1500.00}
        response = self.client.patch(f"{self.url}{self.wallet.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1500.00"))

    def test_delete_wallet(self):
        with self.assertRaises(ProtectedError):
            self.wallet.delete()


    def test_unauthenticated_user_cannot_access_wallets(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from wallet.models import Wallet
from transactions.models import CollectionRequest, Transaction
from unittest.mock import patch
from django.core.exceptions import ValidationError

class TransactionViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            phone_number="01000000001",
            national_id="30305270989876",
            first_name="Sondos",
            last_name="Ali",
            password="So@1234567"
        )
        cls.receiver = User.objects.create_user(
            phone_number="01000000002",
            national_id="30305270989877",
            first_name="Nada",
            last_name="Hassan",
            password="Na@1234567"
        )
        cls.sender_wallet = Wallet.objects.get(user=cls.user)
        cls.sender_wallet.balance = 500
        cls.sender_wallet.save()
        cls.receiver_wallet = Wallet.objects.get(user=cls.receiver)
        cls.receiver_wallet.balance = 300
        cls.receiver_wallet.save()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/transactions/"

    def test_create_valid_transaction(self):
        with patch("transactions.serializers.TransactionOperation.execute_transaction") as mock_execute:
            mock_execute.return_value = Transaction.objects.create(
                from_wallet=self.sender_wallet,
                to_wallet=self.receiver_wallet,
                amount=100.0,
                transaction_type="Send"
            )
            data = {
                "receiver_phone": self.receiver.phone_number,
                "amount": 100.0,
                "transaction_type": "Send"
            }
            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["amount"], "100.00")
            self.assertEqual(response.data["transaction_type"], "Send")

    def test_create_transaction_invalid_amount(self):
        data = {
            "receiver_phone": self.receiver.phone_number,
            "amount": 0,
            "transaction_type": "Send"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid amount", str(response.data))

    def test_create_transaction_to_self_should_fail(self):
        data = {
            "receiver_phone": self.user.phone_number,
            "amount": 100.0,
            "transaction_type": "Send"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot send money to yourself", str(response.data))

    def test_create_transaction_service_layer_fails(self):
        with patch("transactions.serializers.TransactionOperation.execute_transaction") as mock_execute:
            mock_execute.side_effect = ValidationError("❌ Service layer rejected transaction")
            data = {
                "receiver_phone": self.receiver.phone_number,
                "amount": 100.0,
                "transaction_type": "Send"
            }
            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("❌ Service layer rejected transaction", str(response.data))

    def test_unauthenticated_user_cannot_create_transaction(self):
        self.client.force_authenticate(user=None)
        data = {
            "receiver_phone": self.receiver.phone_number,
            "amount": 100.0,
            "transaction_type": "Send"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CollectionRequestViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            phone_number="01000000001",
            national_id="30305270989876",
            first_name="Sondos",
            last_name="Ali",
            password="So@1234567"
        )
        cls.sender = User.objects.create_user(
            phone_number="01000000002",
            national_id="30305270989877",
            first_name="Nada",
            last_name="Hassan",
            password="Na@1234567"
        )

        # send requests to user
        CollectionRequest.objects.create(from_user=cls.sender, to_user=cls.user, amount=100, req_type="Collect", status="Pending")
        CollectionRequest.objects.create(from_user=cls.sender, to_user=cls.user, amount=200, req_type="Collect", status="Approved")
        CollectionRequest.objects.create(from_user=cls.sender, to_user=cls.user, amount=300, req_type="Collect", status="Rejected")

        # user send request
        CollectionRequest.objects.create(from_user=cls.user, to_user=cls.sender, amount=400, req_type="Collect", status="Pending")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_received_requests_pending(self):
        response = self.client.get("/api/collection-requests/received/?status=Pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "Pending")
        self.assertEqual(response.data[0]["amount"], "100.00")

    def test_received_requests_approved(self):
        response = self.client.get("/api/collection-requests/received/?status=Approved")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "Approved")
        self.assertEqual(response.data[0]["amount"], "200.00")

    def test_sent_requests_filtered_by_status(self):
        response = self.client.get("/api/collection-requests/sent/?status=Pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "Pending")
        self.assertEqual(response.data[0]["amount"], "400.00")



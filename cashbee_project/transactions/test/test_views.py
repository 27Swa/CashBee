from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from wallet.models import Wallet, SystemLimit
from transactions.models import CollectionRequest, Transaction
from unittest.mock import patch
from django.core.exceptions import ValidationError
from decimal import Decimal


class TransactionViewTests(TestCase):
    def setUp(self):
        # Clear and create system limits
        SystemLimit.objects.all().delete()
        SystemLimit.objects.create(
            per_transaction_limit=Decimal('1000.00'),
            daily_limit=Decimal('5000.00'),
            monthly_limit=Decimal('20000.00'),
            is_active=True
        )
        
        # Create users (wallets auto-created by signal)
        self.user = User.objects.create_user(
            phone_number="+201000000001",
            national_id="30305270989876",
            first_name="Sondos",
            last_name="Ali",
            password="So@1234567"
        )
        self.receiver = User.objects.create_user(
            phone_number="+201000000002",
            national_id="30305270989877",
            first_name="Nada",
            last_name="Hassan",
            password="Na@1234567"
        )
        
        # Get auto-created wallets and set balances
        self.sender_wallet = self.user.wallet
        self.sender_wallet.balance = Decimal('500.00')
        self.sender_wallet.save()
        
        self.receiver_wallet = self.receiver.wallet
        self.receiver_wallet.balance = Decimal('300.00')
        self.receiver_wallet.save()
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/transactions/"

    def test_create_valid_transaction(self):
        with patch("transactions.serializers.TransactionOperation.execute_transaction") as mock_execute:
            mock_execute.return_value = Transaction.objects.create(
                from_wallet=self.sender_wallet,
                to_wallet=self.receiver_wallet,
                amount=Decimal('100.00'),
                transaction_type=Transaction.TransactionType.SEND,
                from_wallet_balance_before=self.sender_wallet.balance,
                to_wallet_balance_before=self.receiver_wallet.balance
            )
            data = {
                "receiver_phone": str(self.receiver.phone_number),  # Convert to string
                "amount": "100.00",
                "transaction_type": "Send"
            }
            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["amount"], "100.00")
            self.assertEqual(response.data["transaction_type"], "Send")

    def test_create_transaction_invalid_amount(self):
        data = {
            "receiver_phone": str(self.receiver.phone_number),
            "amount": "0",
            "transaction_type": "Send"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The MinValueValidator from the model triggers first
        self.assertIn("amount", response.data)
        # Check that there's an error related to amount validation
        amount_errors = response.data.get('amount', [])
        self.assertTrue(len(amount_errors) > 0, "Expected amount validation error")

    def test_create_transaction_to_self_should_fail(self):
        data = {
            "receiver_phone": str(self.user.phone_number),  # Convert to string
            "amount": "100.00",
            "transaction_type": "Send"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot send money to yourself", str(response.data))

    def test_create_transaction_service_layer_fails(self):
        with patch("transactions.serializers.TransactionOperation.execute_transaction") as mock_execute:
            mock_execute.side_effect = ValidationError("❌ Service layer rejected transaction")
            data = {
                "receiver_phone": str(self.receiver.phone_number),  # Convert to string
                "amount": "100.00",
                "transaction_type": "Send"
            }
            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("Service layer rejected transaction", str(response.data))

    def test_unauthenticated_user_cannot_create_transaction(self):
        self.client.force_authenticate(user=None)
        data = {
            "receiver_phone": str(self.receiver.phone_number),  # Convert to string
            "amount": "100.00",
            "transaction_type": "Send"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CollectionRequestViewTests(TestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            phone_number="+201000000001",
            national_id="30305270989876",
            first_name="Sondos",
            last_name="Ali",
            password="So@1234567"
        )
        self.sender = User.objects.create_user(
            phone_number="+201000000002",
            national_id="30305270989877",
            first_name="Nada",
            last_name="Hassan",
            password="Na@1234567"
        )

        # Create collection requests
        CollectionRequest.objects.create(
            from_user=self.sender,
            to_user=self.user,
            amount=Decimal('100.00'),
            req_type=CollectionRequest.ReqType.COLLECT_MONEY,
            status=CollectionRequest.Status.PENDING
        )
        CollectionRequest.objects.create(
            from_user=self.sender,
            to_user=self.user,
            amount=Decimal('200.00'),
            req_type=CollectionRequest.ReqType.COLLECT_MONEY,
            status=CollectionRequest.Status.APPROVED
        )
        CollectionRequest.objects.create(
            from_user=self.sender,
            to_user=self.user,
            amount=Decimal('300.00'),
            req_type=CollectionRequest.ReqType.COLLECT_MONEY,
            status=CollectionRequest.Status.REJECTED
        )
        CollectionRequest.objects.create(
            from_user=self.user,
            to_user=self.sender,
            amount=Decimal('400.00'),
            req_type=CollectionRequest.ReqType.COLLECT_MONEY,
            status=CollectionRequest.Status.PENDING
        )
        
        # Setup API client
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

    def test_unauthenticated_user_cannot_access_requests(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/collection-requests/received/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
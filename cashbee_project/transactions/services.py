from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from django.utils import timezone
from django.forms import ValidationError
from django.db import transaction as transaction
from django.shortcuts import get_object_or_404
from .enums import CollectionMoneyOptions
from .models import CollectionRequest, Transaction
from wallet.models import Wallet
from users.models import User, UsersRole
from decimal import Decimal



class UserRepository:
    @staticmethod
    def get_user_by_phone(phone_number):
        try:
            return User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise ValidationError("❌ Target user not found.")
class WalletRepository:
    @staticmethod
    def get_wallet_by_user(user):
        try:
            return Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            raise ValidationError(f"❌ Wallet not found for user {user}.")
class Payment(ABC):
    def __init__(self, from_wallet: Wallet, amount: Decimal, to_wallet: Wallet, tx_type: str):
        self.from_wallet = get_object_or_404(Wallet, pk=from_wallet.id)
        self.to_wallet = get_object_or_404(Wallet, pk=to_wallet.id)
        self.amount = amount
        self.tx_type = tx_type
        self.date = datetime.now()
        self.transaction = None 
    @abstractmethod
    def execute(self) -> tuple[str,Transaction]:
        pass
    @staticmethod
    def validate_transaction(from_wallet, to_wallet, amount):
        if from_wallet == to_wallet:
            raise ValidationError("Sender and receiver cannot be the same wallet.")
        if amount < 1.0:
            raise ValidationError("Amount must be at least 1.0 EGP.")
        if amount > from_wallet.balance:
            raise ValidationError("Insufficient balance in the sender wallet.")
        if amount > from_wallet.transaction_limit:
            raise ValidationError("Per operation max limit exceeded.")

        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_total = Transaction.objects.filter(
            from_wallet=from_wallet,
            date__gte=start_of_month,
            status=Transaction.TransactionStatus.SUCCESS,
        ).aggregate(total=Sum('amount'))['total'] or 0

        if monthly_total + amount > from_wallet.max_limit:
            raise ValidationError("Monthly transfer limit exceeded.")
    def create_transaction(self):
            self.transaction = Transaction.objects.create(
            from_wallet=self.from_wallet,
            to_wallet=self.to_wallet,
            amount=self.amount,
            transaction_type=self.tx_type,
            status=Transaction.TransactionStatus.PENDING
        )
    def update_transaction(self,res):
        self.transaction.status = (
            Transaction.TransactionStatus.SUCCESS if res 
            else Transaction.TransactionStatus.FAILED
        )
        self.transaction.save()
class SendRecievePayment(Payment):
    def __init__(self, from_wallet: Wallet, amount: Decimal, to_wallet: Wallet):
        super().__init__(from_wallet, amount, to_wallet, Transaction.TransactionType.SEND)
    @transaction.atomic
    def execute(self) -> tuple[str,Transaction]:
        try:
            # ✅ FIXED: Validate FIRST
            self.validate_transaction(self.from_wallet, self.to_wallet, self.amount)
            
            # ✅ FIXED: Create transaction AFTER validation
            self.create_transaction()

            self.from_wallet.balance -= Decimal(self.amount)
            self.from_wallet.save()
            self.to_wallet.balance += Decimal(self.amount)
            self.to_wallet.save()

            self.update_transaction(True)
            return f"✅ {self.tx_type} successful",self.transaction
        except Exception as e:
            self.update_transaction(False)
            return f"❌ Transaction failed: {str(e)}"
class PaymentFactory:
    @staticmethod
    def create_payment(payment_type, from_wallet, amount, to_wallet, bill=None) -> Payment:
        if payment_type == Transaction.TransactionType.SEND:
            return SendRecievePayment(from_wallet, amount, to_wallet)
        else:
            raise ValueError("❌ Invalid payment type")
class TransactionOperation:
    """ To apply any operation send, receive, donate, bill pay """
    def __init__(self, from_user, to_phone,payment_type, amount,bill=None):
        self.from_user = from_user
        self.from_wallet = WalletRepository.get_wallet_by_user(from_user)
        to_user = UserRepository.get_user_by_phone(to_phone)
        self.to_wallet = WalletRepository.get_wallet_by_user(to_user)
        self.payment_type = payment_type 
        self.amount = amount
        self.bill = None
    def execute_transaction(self):       
        payment: Payment = PaymentFactory.create_payment(self.payment_type, self.from_wallet, self.amount, self.to_wallet, self.bill)
        msg,tr = payment.execute()
        return tr
class CollectMoney:
    def __init__(self, from_user: User, amount: Decimal, to_phone,req_type=CollectionRequest.ReqType.COLLECT_MONEY):
        self.to_user = UserRepository.get_user_by_phone(to_phone)
        self.from_user = from_user
        self.amount = amount
        self.req_type = req_type
        self.collect = None
    @staticmethod
    def validate_collection_request(from_user, to_user, amount):
        if from_user == to_user:
            raise ValidationError("Sender and receiver cannot be the same user.")
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
    def can_collect(self):
        if self.to_user.role == UsersRole.USER:
            return self.from_user.role in CollectionMoneyOptions.USER.value
        elif self.to_user.role == UsersRole.PARENT:
            return self.from_user.role in CollectionMoneyOptions.PARENT.value
        elif self.to_user.role == UsersRole.CHILD:
            return self.from_user.role in CollectionMoneyOptions.CHILD.value
        return False

    @transaction.atomic
    def execute(self, req_type=CollectionRequest.ReqType.COLLECT_MONEY):
        """Create a collection request if allowed."""
        
        if not self.can_collect():
            raise ValidationError("❌ Request not allowed for these user roles.") 

        if CollectionRequest.objects.filter(
            from_user=self.from_user,
            to_user=self.to_user,
            amount = self.amount,
            status=CollectionRequest.Status.PENDING,
            req_type=req_type,
        ).exists():
            raise ValidationError("A pending request already exists between these users.")
    
               
        new_request = CollectionRequest.objects.create(
        from_user=self.from_user,
        to_user=self.to_user,
        amount=self.amount,
        req_type=self.req_type,
        status=CollectionRequest.Status.PENDING,
        )
        return new_request
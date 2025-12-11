from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from .models import CollectionRequest, Transaction
from wallet.models import Wallet, SystemLimit, PersonalLimit, FamilyLimit
from users.models import User, UsersRole


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


class TransactionLimitChecker:
    """
    Handles checking all transaction limits (System, Family, Personal)
    """
    
    @staticmethod
    def get_effective_limits(user):
        """
        Get the most restrictive limits for a user.
        Priority: Personal < Family < System
        Returns the MINIMUM of all applicable limits.
        """
        # Get system limits (always applies)
        system_limit = SystemLimit.objects.filter(is_active=True).first()
        if not system_limit:
            raise ValidationError("❌ System limits not configured. Contact administrator.")
        
        limits = {
            'per_transaction': system_limit.per_transaction_limit,
            'daily': system_limit.daily_limit,
            'monthly': system_limit.monthly_limit
        }
        
        # Check if user has family limits (for children)
        if user.role == UsersRole.CHILD:
            try:
                family_limit = FamilyLimit.objects.get(child=user, is_active=True)
                limits['per_transaction'] = min(limits['per_transaction'], family_limit.per_transaction_limit)
                limits['daily'] = min(limits['daily'], family_limit.daily_limit)
                limits['monthly'] = min(limits['monthly'], family_limit.monthly_limit)
            except FamilyLimit.DoesNotExist:
                pass  # No family limit set, use system limits
        
        # Check if user has personal limits
        try:
            personal_limit = PersonalLimit.objects.get(user=user, is_active=True)
            limits['per_transaction'] = min(limits['per_transaction'], personal_limit.per_transaction_limit)
            limits['daily'] = min(limits['daily'], personal_limit.daily_limit)
            limits['monthly'] = min(limits['monthly'], personal_limit.monthly_limit)
        except PersonalLimit.DoesNotExist:
            pass  # No personal limit set
        
        return limits
    
    @staticmethod
    def check_per_transaction_limit(user, amount):
        """Check if amount exceeds per-transaction limit"""
        limits = TransactionLimitChecker.get_effective_limits(user)
        if amount > limits['per_transaction']:
            raise ValidationError(
                f"❌ Amount exceeds your per-transaction limit of {limits['per_transaction']} EGP"
            )
    
    @staticmethod
    def check_daily_limit(user, amount):
        """Check if amount would exceed daily limit"""
        limits = TransactionLimitChecker.get_effective_limits(user)
        
        # Get today's transactions
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        wallet = WalletRepository.get_wallet_by_user(user)
        
        daily_total = Transaction.objects.filter(
            from_wallet=wallet,
            date__gte=today_start,
            status=Transaction.TransactionStatus.SUCCESS,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        if daily_total + amount > limits['daily']:
            raise ValidationError(
                f"❌ Transaction would exceed your daily limit. "
                f"Spent today: {daily_total} EGP, Limit: {limits['daily']} EGP, "
                f"Available: {limits['daily'] - daily_total} EGP"
            )
    
    @staticmethod
    def check_monthly_limit(user, amount):
        """Check if amount would exceed monthly limit"""
        limits = TransactionLimitChecker.get_effective_limits(user)
        
        # Get this month's transactions
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        wallet = WalletRepository.get_wallet_by_user(user)
        
        monthly_total = Transaction.objects.filter(
            from_wallet=wallet,
            date__gte=start_of_month,
            status=Transaction.TransactionStatus.SUCCESS,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        if monthly_total + amount > limits['monthly']:
            raise ValidationError(
                f"❌ Transaction would exceed your monthly limit. "
                f"Spent this month: {monthly_total} EGP, Limit: {limits['monthly']} EGP, "
                f"Available: {limits['monthly'] - monthly_total} EGP"
            )


class Payment(ABC):
    def __init__(self, from_wallet: Wallet, amount: Decimal, to_wallet: Wallet, tx_type: str):
        self.from_wallet = get_object_or_404(Wallet, pk=from_wallet.id)
        self.to_wallet = get_object_or_404(Wallet, pk=to_wallet.id)
        self.amount = amount
        self.tx_type = tx_type
        self.date = datetime.now()
        self.transaction = None 
    
    @abstractmethod
    def execute(self) -> tuple[str, Transaction]:
        pass
    
    @staticmethod
    def validate_transaction(from_wallet, to_wallet, amount):
        """Basic transaction validation + limit checking"""
        # Basic validations
        if from_wallet == to_wallet:
            raise ValidationError("❌ Sender and receiver cannot be the same wallet.")
        
        if amount < Decimal('1.0'):
            raise ValidationError("❌ Amount must be at least 1.0 EGP.")
        
        if amount > from_wallet.balance:
            raise ValidationError(
                f"❌ Insufficient balance. Available: {from_wallet.balance} EGP, "
                f"Required: {amount} EGP"
            )
        
        # Check all limits
        user = from_wallet.user
        
        # Check per-transaction limit
        TransactionLimitChecker.check_per_transaction_limit(user, amount)
        
        # Check daily limit
        TransactionLimitChecker.check_daily_limit(user, amount)
        
        # Check monthly limit
        TransactionLimitChecker.check_monthly_limit(user, amount)
    
    def create_transaction(self):
        self.transaction = Transaction.objects.create(
            from_wallet=self.from_wallet,
            to_wallet=self.to_wallet,
            amount=self.amount,
            transaction_type=self.tx_type,
            status=Transaction.TransactionStatus.PENDING,
            from_wallet_balance_before=self.from_wallet.balance,  
            to_wallet_balance_before=self.to_wallet.balance       
        )
    
    def update_transaction(self, res):
        self.transaction.status = (
            Transaction.TransactionStatus.SUCCESS if res 
            else Transaction.TransactionStatus.FAILED
        )
        self.transaction.save()


class SendRecievePayment(Payment):
    def __init__(self, from_wallet: Wallet, amount: Decimal, to_wallet: Wallet):
        super().__init__(from_wallet, amount, to_wallet, Transaction.TransactionType.SEND)
    
    @db_transaction.atomic
    def execute(self) -> tuple[str, Transaction]:
        try:
            self.validate_transaction(self.from_wallet, self.to_wallet, self.amount)
            self.create_transaction()

            self.from_wallet.balance -= Decimal(self.amount)
            self.from_wallet.save()
            self.to_wallet.balance += Decimal(self.amount)
            self.to_wallet.save()

            self.update_transaction(True)
            return f"✅ {self.tx_type} successful", self.transaction
        except Exception as e:
            if self.transaction:
                self.update_transaction(False)
            raise  # Re-raise the exception so it can be handled by the caller


class PaymentFactory:
    @staticmethod
    def create_payment(payment_type, from_wallet, amount, to_wallet, bill=None) -> Payment:
        if payment_type == Transaction.TransactionType.SEND:
            return SendRecievePayment(from_wallet, amount, to_wallet)
        else:
            raise ValueError("❌ Invalid payment type")


class TransactionOperation:
    """To apply any operation send, receive, donate, bill pay"""
    
    def __init__(self, from_user, to_phone, payment_type, amount, bill=None):
        self.from_user = from_user
        self.from_wallet = WalletRepository.get_wallet_by_user(from_user)
        to_user = UserRepository.get_user_by_phone(to_phone)
        self.to_wallet = WalletRepository.get_wallet_by_user(to_user)
        self.payment_type = payment_type 
        self.amount = amount
        self.bill = None
    
    def execute_transaction(self):       
        payment: Payment = PaymentFactory.create_payment(
            self.payment_type, 
            self.from_wallet, 
            self.amount, 
            self.to_wallet, 
            self.bill
        )
        msg, tr = payment.execute()
        return tr


class CollectMoney:
    def __init__(self, from_user: User, amount: Decimal, to_phone, req_type=CollectionRequest.ReqType.COLLECT_MONEY):
        self.to_user = UserRepository.get_user_by_phone(to_phone)
        self.from_user = from_user
        self.amount = amount
        self.req_type = req_type
        self.collect = None
    
    @staticmethod
    def validate_collection_request(from_user, to_user, amount):
        if from_user == to_user:
            raise ValidationError("❌ Sender and receiver cannot be the same user.")
        if amount <= 0:
            raise ValidationError("❌ Amount must be positive.")
    
    def can_collect(self):
        """Check if collection request is allowed based on user roles"""
        # For now, allow all users to request from each other
        # You can implement role-based logic here if needed
        return True

    @db_transaction.atomic
    def execute(self, req_type=CollectionRequest.ReqType.COLLECT_MONEY):
        """Create a collection request if allowed."""
        
        if not self.can_collect():
            raise ValidationError("❌ Request not allowed for these user roles.") 

        if CollectionRequest.objects.filter(
            from_user=self.from_user,
            to_user=self.to_user,
            amount=self.amount,
            status=CollectionRequest.Status.PENDING,
            req_type=req_type,
        ).exists():
            raise ValidationError("❌ A pending request already exists between these users.")
        
        new_request = CollectionRequest.objects.create(
            from_user=self.from_user,
            to_user=self.to_user,
            amount=self.amount,
            req_type=self.req_type,
            status=CollectionRequest.Status.PENDING,
        )
        return new_request
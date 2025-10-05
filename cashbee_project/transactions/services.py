from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime
from .models import Transaction
from wallet.models import Wallet
from users.models import User
from .enums import Role, CollectionMoneyOptions
from django.shortcuts import get_object_or_404
from decimal import Decimal

class Payment(ABC):
    def __init__(self, from_wallet: Wallet, amount: Decimal, to_wallet: Wallet, tx_type: str):
        self.from_wallet = get_object_or_404(Wallet, pk=from_wallet.id)
        self.to_wallet = get_object_or_404(Wallet, pk=to_wallet.id)
        self.amount = amount
        self.tx_type = tx_type
        self.date = datetime.now()
        self.transaction = Transaction.objects.create(
            from_wallet=self.from_wallet,
            to_wallet=self.to_wallet,
            amount=self.amount,
            transaction_type=self.tx_type,
            date=self.date,
            status = Transaction.TransactionStatus.PENDING
        )
    @abstractmethod
    def execute(self) -> str:
        pass
    def _validate(self) -> str | None:
        if self.amount <= 0:
            return "❌ Invalid amount"
        if self.amount > self.from_wallet.balance:
            return "❌ Insufficient balance"
        if self.amount > self.from_wallet.transaction_limit:
            return "❌ Exceeds transaction limit"
        return None
        if res == True:
            self.transaction.objects.update(status = Transaction.TransactionStatus.SUCCESS)
        else:
            self.transaction.objects.update(status = Transaction.TransactionStatus.FAILED)
    def update_transaction(self,res):
        if res:
            self.transaction.status = Transaction.TransactionStatus.SUCCESS
        else:   
            self.transaction.status = Transaction.TransactionStatus.FAILED
        self.transaction.save()
class SendRecievePayment(Payment):
    def __init__(self, from_wallet: Wallet, amount: Decimal, to_wallet: Wallet):
        super().__init__(from_wallet, amount, to_wallet, Transaction.TransactionType.SEND)

    def execute(self) -> str:
        error = self._validate()
        if error:
            self.update_transaction(False)
            return error

        self.from_wallet.balance -= Decimal(self.amount)
        self.from_wallet.save()
        self.to_wallet.balance += Decimal(self.amount)
        self.to_wallet.save()

        self.update_transaction(True)
        return f"✅ {self.tx_type} successful"
class DonationPayment(Payment):
    def __init__(self, from_wallet: Wallet, amount: Decimal, to_wallet: Wallet):
        super().__init__(from_wallet, amount, to_wallet, Transaction.TransactionType.DONATE)

    def execute(self) -> str:
        error = self._validate()
        if error:
            self.update_transaction(False)
            return error


        self.from_wallet.balance -= self.amount
        self.from_wallet.save()
        self.to_wallet.balance += self.amount
        self.to_wallet.save()

        self.update_transaction(True)
        return f"✅ {self.tx_type} successful"

class BillPayment(Payment):
    def __init__(self, from_wallet: Wallet, amount: Decimal, to_wallet: Wallet, bill):
        super().__init__(from_wallet, amount, to_wallet, Transaction.TransactionType.BILL_PAY)
        self.bill = bill

    def execute(self) -> str:
        error = self._validate()
        if error:
            self.update_transaction(False)
            return error, None
        if self.bill.is_paid:
            self.update_transaction(False)
            return f"⚠️ Bill {self.bill.id} is already paid.", None

        self.from_wallet.balance -= self.amount
        self.from_wallet.save()

        self.to_wallet.balance += self.amount
        self.to_wallet.save()

        self.bill.mark_paid()
        self.bill.save()

        self.update_transaction(True)
        return f"✅ Bill Payment of {self.amount} EGP to organization {self.bill.organization_id} successful"
class PaymentFactory:
    @staticmethod
    def create_payment(payment_type, from_wallet, amount, to_wallet, bill=None) -> Payment:
        if payment_type == Transaction.TransactionType.SEND:
            return SendRecievePayment(from_wallet, amount, to_wallet)
        elif payment_type == Transaction.TransactionType.DONATE:
            return DonationPayment(from_wallet, amount, to_wallet)
        elif payment_type == Transaction.TransactionType.BILL_PAY:
            return BillPayment(from_wallet, amount, to_wallet, bill)
        else:
            raise ValueError("❌ Invalid payment type")
class TransactionOperation:
    """ To apply any operation send, receive, donate, bill pay """
    def __init__(self, from_user, to_user):
        self.from_wallet = from_user
        self.to_wallet = to_user

    def execute_transaction(self, payment_type, amount, bill=None):       
        payment: Payment = PaymentFactory.create_payment(payment_type, self.from_wallet, amount, self.to_wallet, bill)
        msg = payment.execute()
        return msg
    
class CollectMoney:
    def __init__(self, from_user: User, amount: Decimal, to_user: User):
        self.from_user = from_user
        self.to_user = to_user
        self.amount = amount

    def can_collect(self):
        if self.to_user.role == Role.USER.value:
            return self.from_user.role in CollectionMoneyOptions.USER.value
        elif self.to_user.role == Role.PARENT.value:
            return self.from_user.role in CollectionMoneyOptions.PARENT.value
        elif self.to_user.role == Role.CHILD.value:
            return self.from_user.role in CollectionMoneyOptions.CHILD.value
        return False

    def execute(self, req_type):
        if self.can_collect():
            return "✅ Request sent successfully"
        else:
            return "❌ Request not allowed"

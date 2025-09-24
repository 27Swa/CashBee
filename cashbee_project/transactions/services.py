from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Tuple
from wallet.models import Wallet
from .models import Transaction
from users.models import User
from enums import PaymentType, Role, CollectionMoneyOptions

class Payment(ABC):
    def __init__(self, from_wallet: Wallet, amount: Decimal, to_wallet: Wallet, tx_type: PaymentType):
        self.from_wallet = from_wallet
        self.amount = amount
        self.to_wallet = to_wallet
        self.tx_type = tx_type
        self.date = datetime.now()

    @abstractmethod
    def execute(self) -> Tuple[str, Transaction]:
        pass

    def _validate(self) -> str | None:
        if self.amount <= 0:
            return "❌ Invalid amount"
        if self.amount > self.from_wallet.balance:
            return "❌ Insufficient balance"
        if self.amount > self.from_wallet.transaction_limit:
            return "❌ Exceeds transaction limit"
        return None

    def _create_transaction(self):
        return Transaction(
            from_wallet=self.from_wallet,
            to_wallet=self.to_wallet,
            amount=self.amount,
            type=self.tx_type.value,
            date=self.date
        )

class SendReceivePayment(Payment):
    def __init__(self, from_wallet, amount, to_wallet):
        super().__init__(from_wallet, amount, to_wallet, PaymentType.SEND)

    def execute(self) -> Tuple[str, Transaction]:
        error = self._validate()
        if error:
            return error, None

        self.from_wallet.balance -= Decimal(self.amount)
        self.to_wallet.balance += Decimal(self.amount)

        transaction = self._create_transaction()
        return f"✅ {self.tx_type.value} successful", transaction

class DonationPayment(Payment):
    def __init__(self, from_wallet, amount, to_wallet):
        super().__init__(from_wallet, amount, to_wallet, PaymentType.DONATE)

    def execute(self) -> Tuple[str, Transaction]:
        error = self._validate()
        if error:
            return error, None

        self.from_wallet.balance -= Decimal(self.amount)
        self.to_wallet.balance += Decimal(self.amount)

        transaction = self._create_transaction()
        return f"✅ {self.tx_type.value} successful", transaction

class BillPayment(Payment):
    def __init__(self, from_wallet, amount, to_wallet, bill):
        super().__init__(from_wallet, amount, to_wallet, PaymentType.BILL_PAY)
        self.bill = bill

    def execute(self) -> Tuple[str, Transaction]:
        error = self._validate()
        if error:
            return error, None

        if self.bill.is_paid:
            return f"⚠️ Bill {self.bill.id} is already paid.", None

        self.from_wallet.balance -= Decimal(self.amount)
        self.to_wallet.balance += Decimal(self.amount)

        transaction = self._create_transaction()

        self.bill.mark_paid()  # هتسويها لاحقًا

        return f"✅ Bill Payment of {self.amount} EGP to organization {self.bill.organization_id} successful", transaction

class CollectMoney:
    def __init__(self, from_user: User, amount: Decimal, to_user: User):
        self.from_user = from_user
        self.to_user = to_user
        self.amount = amount
        self.subject = None  # skip notifications for now

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
        return "❌ Request not allowed"

class PaymentFactory:
    @staticmethod
    def create_payment(payment_type, from_wallet, amount, to_wallet, bill=None) -> Payment:
        if payment_type == PaymentType.SEND:
            return SendReceivePayment(from_wallet, amount, to_wallet)
        elif payment_type == PaymentType.DONATE:
            return DonationPayment(from_wallet, amount, to_wallet)
        elif payment_type == PaymentType.BILL_PAY:
            return BillPayment(from_wallet, amount, to_wallet, bill)
        else:
            raise ValueError("❌ Invalid payment type")

class TransactionOperation:
    """ To apply any operation send, receive, donate, bill pay """
    def __init__(self, from_user: User, to_user: User):
        self.from_wallet = from_user.wallet
        self.to_wallet = to_user.wallet

    def execute_transaction(self, payment_type, amount, bill=None):
        payment: Payment = PaymentFactory.create_payment(payment_type, self.from_wallet, amount, self.to_wallet, bill)
        msg, transaction = payment.execute()

        if transaction:
            self.from_wallet.save()
            self.to_wallet.save()

            transaction.save()

        return msg

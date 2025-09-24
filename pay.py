from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Tuple
from data import Transaction, Wallet
from enums import PaymentType,Role,CollectionMoneyOptions
from mappers import TransactionMapper, WalletMapper
from person import User
from postgres import QueryHandling


class WalletRepresentation:
    @staticmethod
    def display(walletid):
        # View Wallet use case
        wallet = QueryHandling.retrieve_data('Wallet',WalletMapper,"","wallet_id = %s",(walletid,))
        if not wallet:
            raise ValueError("❌ Wallet not found")
        result = "\n--- Wallet Overview ---\n"
        result += f"Balance: {wallet.balance} EGP\n"
        result += f"Transaction Limit: {wallet.transaction_limit} EGP\n"
        result += f"Max Limit: {wallet.max_transaction_limit} EGP\n"
        return result

class Payment(ABC):
    def __init__(self, from_wallet, amount, to_wallet, tx_type):
        self.from_:Wallet = from_wallet  
        self.amount = amount
        self.to_:Wallet = to_wallet
        self.tx_type = tx_type
        self.date = datetime.now()

    @abstractmethod
    def execute(self) -> Tuple[str, Transaction]:
        pass

    def _validate(self) -> str | None:
        if self.amount <= 0:
            return "❌ Invalid amount"
        if self.amount > self.from_.balance:
            return "❌ Insufficient balance"
        if self.amount > self.from_.transaction_limit:
            return "❌ Exceeds transaction limit"
        return None

    def _create_transaction(self):
        return Transaction(
            from_wallet=self.from_.wallet,
            amount=self.amount,
            dt=self.date,
            tx_type=self.tx_type,
            to_wallet=self.to_.wallet,
        )

class SendRecievePayment(Payment):

    def __init__(self, from_wallet, amount, to_wallet):
        super().__init__(from_wallet, amount, to_wallet, PaymentType.SEND)

    def execute(self) -> Tuple[str, Transaction]:
        error = self._validate()
        if error:
            return error, None
        
        self.from_.balance -= Decimal(self.amount)
        self.to_.balance +=Decimal(self.amount)

        trans:Transaction = self._create_transaction()
        return f"✅ {self.tx_type.value} successful",trans
       
class DonationPayment(Payment):
    """Send money to different charities organizations"""
    def __init__(self, from_user_id, amount, to):
        super().__init__(from_user_id, amount, to, PaymentType.DONATE)

    def execute(self) -> Tuple[str, Transaction]:
        error = self._validate(self.from_user_id)
        if error:
            return error
        
        self.from_.balance -= Decimal(self.amount)
        self.to_.balance +=Decimal(self.amount)

        trans:Transaction = self._create_transaction()
        return f"✅ {self.tx_type.value} successful",trans

class BillPayment(Payment):
    def __init__(self, from_user_id, amount,to_wallet, to_bill):
        super().__init__(from_user_id, amount, to_wallet, PaymentType.BILL_PAY)
        self.bill = to_bill

    def execute(self) -> Tuple[str, Transaction]:
        error = self._validate(self.from_)
        if error:
            return error
        if self.bill.is_paid:
            return f"⚠️ Bill {self.bill.bill_id} is already paid.", None

        self.from_.balance -= Decimal(self.amount)
        self.to_.balance += Decimal(self.amount)
        
        transaction = self._create_transaction()

        self.bill.mark_paid()

        return f"✅ Bill Payment of {self.amount} EGP to organization {self.bill.organization_id} successful", transaction

class CollectMoney():
    def __init__(self, from_user, amount, to_me):
        self.from_ :User = from_user
        self.to_me:User = to_me
        self.amount = amount
        self.subject = RequestSubject()
    def can_collect(self):
        flag = False
        if self.to_me.role == Role.USER.value:
            if self.from_.role in CollectionMoneyOptions.USER.value:
                flag = True
        elif self.to_me.role == Role.PARENT.value:
            if self.from_.role in CollectionMoneyOptions.PARENT.value:
                flag = True
        elif self.to_me.role == Role.CHILD.value:
            if self.from_.role in CollectionMoneyOptions.CHILD.value:
                flag = True
        return flag
    def execute(self,req_type):
        """
        steps:
            - request options 
            - send request
        """
        if self.can_collect():
            self.subject.notify(self.from_, self.to_me, self.amount,req_type)
            return "✅ Request sent successfully"
        else:
            return "❌ Request not allowed"

class PaymentFactory:
    @staticmethod
    def create_payment(payment_type, from_user, amount, to_user) -> Payment:
        if payment_type == PaymentType.SEND:
            return SendRecievePayment(from_user, amount, to_user)       
        elif payment_type == PaymentType.DONATE:
            return DonationPayment(from_user, amount, to_user)
        elif payment_type == PaymentType.BILL_PAY:
            return BillPayment(from_user, amount, to_user)
        else:
            raise ValueError("❌ Invalid payment type")

class TransactionOperation:
    """ To apply any operation send, recieve,.... we need to get users data
        so that when apply any operation the money transfered will be substracted from
        one account and added to the other one
    """
    """
        steps:
        - get the right function
        - create payment
        - update both wallets
        - send observer
        - update transaction
    """
    def __init__(self, user1, user2):
        self.user1wid = user1.wallet
        self.user2wid = user2.wallet
        self.transaction_subject = TransactionSubject()
        
    def execute_transaction(self, payment_type, amount):
        # Get users' wallet
        user1_wallet:Wallet  = QueryHandling.retrieve_data('Wallet',WalletMapper,'','wallet_id = %s',(self.user1wid,))
        user2_wallet:Wallet  = QueryHandling.retrieve_data('Wallet',WalletMapper,'','wallet_id = %s',(self.user2wid,))      
     
        payment:Payment = PaymentFactory.create_payment(payment_type,user1_wallet, amount, user2_wallet)
        msg,transaction = payment.execute()
       
        if msg.startswith("✅"):
            # Update wallets in database
            col = ["balance"]
            data = (user1_wallet.balance,user1_wallet.wallet)
            QueryHandling.update_data('Wallet',col,'wallet_id = %s',data)  

            data = (user2_wallet.balance,user2_wallet.wallet)
            QueryHandling.update_data('Wallet',col,'wallet_id = %s',data)

            # Insert a transaction
            cols = ['from_wallet','to_wallet','amount','type_','date_']
            transaction.transaction_id = QueryHandling.add_data("Transactions",cols,transaction,TransactionMapper)                    
        
            # Notify observers
            self.transaction_subject.notify(transaction)
        return msg

class TransactionObserver(ABC):

    @abstractmethod
    def update(self, transaction: Transaction):
        pass
class SMSNotificationObserver(TransactionObserver):
    def update(self,  transaction: Transaction):
        print(f"Transaction {transaction.Transaction_type} of {transaction.amount} EGP from {transaction.from_wid} to {transaction.to_wid} completed")
class TransactionSubject:

    def __init__(self):
        self._observers = []
        
    def attach(self, observer: TransactionObserver):
        self._observers.append(observer)
        
    def detach(self, observer: TransactionObserver):
        self._observers.remove(observer)
        
    def notify(self, transaction: Transaction):
        for observer in self._observers:
            observer.update(transaction)

class RequestObserver(ABC):
    @abstractmethod
    def update(self, from_,to,amount):
        pass
class SMSNotificationObserver(RequestObserver):
    def update(self, from_,to,amount,req_type):
        print(f"Request: {req_type} with amount {amount} EGP from {from_} to {to} sent successfully")    
class RequestSubject:

    def __init__(self):
        self._observers = []
        
    def attach(self, observer: RequestObserver):
        self._observers.append(observer)
        
    def detach(self, observer: RequestObserver):
        self._observers.remove(observer)
        
    def notify(self, from_, to, amount,req_type):
        for observer in self._observers:
            observer.update(from_, to, amount,req_type)

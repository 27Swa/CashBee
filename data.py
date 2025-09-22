from datetime import datetime
from enums import TransactionLimits

class Transaction:
    """Any operation made will be saved as transaction 
        which contains the most important information about the operation
    """
    def __init__(self, from_wallet, amount, tx_type, to_wallet, dt,transaction_id = None):
        self.transaction_id = transaction_id
        self.from_wid = from_wallet
        self.amount = amount
        self.type = tx_type
        self.date = dt
        self.to_wid = to_wallet
        
    def show_details(self):
        return f"{self.date.strftime('%Y-%m-%d %H:%M')} | {self.type.value} | From Wallet {self.from_wid} -> To Wallet {self.to_wid} | {self.amount} EGP\n"

class Wallet:
    """This class contains important information about user wallet which are:
        balance, wallet_id, transaaction limit which the user put to himself,
        max_limit is the system maximum limit that the user shouldn't exceed
        and money has been used in payment process
    """
    def __init__(self, balance=0, transaction_limit=TransactionLimits.PER_OPERATION_LIMIT.value, 
                 
                 max_limit=TransactionLimits.MONTHLY_LIMIT.value,wid = None):
        self.walletid = wid
        self._balance = balance
        self._transaction_limit = transaction_limit
        self._max_limit = max_limit
    @property
    def balance(self):
        return self._balance        
    @property
    def transaction_limit(self):
        return self._transaction_limit         
    @property
    def max_transaction_limit(self):
        return self._max_limit    
    @property
    def wallet(self):
        return self.walletid
    @transaction_limit.setter
    def transaction_limit(self, amount):
        if amount > self.max_transaction_limit:
            raise ValueError("Limit exceeds maximum allowed")
        self._transaction_limit = amount        
    @balance.setter    
    def balance(self, amount):
        self._balance = amount
    @wallet.setter
    def wallet(self,value):
        self.walletid = value
    @max_transaction_limit.setter
    def max_transaction_limit(self,value: float):
        if value <=0:
            raise ValueError("Maximum limit can't be negative")
        self._max_limit = float(value)

class Request:
    def __init__(self,from_person,to_person,amount,status,id = None):
        self._request_id = id
        self.from_person_id = from_person
        self.to_person_id = to_person
        self.amount = amount
        self.status = status
    @property
    def request_id(self):
        return self._request_id   
    @request_id.setter
    def request_id(self,val):
        self._request_id = val

class Bill:
    def __init__(self, bill_id: int, organization_id: int, amount: float, due_date: datetime):
        self.bill_id = bill_id
        self.organization_id = organization_id
        self.amount = amount
        self.due_date = due_date
        self.is_paid = False

    def mark_paid(self):
        self.is_paid = True

class Family:
    """Contains the information about the 
    family wallet which are: family_id, parent_id, members_id"""
    def __init__(self,name, fid=None):
        self._family_id:int = fid
        self.name = name
    @property
    def family_id(self):
        return self._family_id   
    @family_id.setter
    def family_id(self,val):
        self._family_id = val

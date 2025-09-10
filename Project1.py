from abc import ABC, abstractmethod
from typing import Protocol, List, Dict
from enum import Enum
import phonenumbers
from phonenumbers import NumberParseException
import re
from datetime import datetime, timedelta, date
import json
import os
class ValidationCheck:
    def __init__(self,name,phone,password,national_id):
        self.validation_checks = [
            (name, ValidationsNames.NAME.value),
            (phone, ValidationsNames.PHONE.value),
            (password, ValidationsNames.PASSWORD.value),
            (national_id, ValidationsNames.NATIONALID.value)
        ]
    def check(self):  
        for value, validator in self.validation_checks:
            if not validator.validate(value):
                return f"❌ {validator.get_error()}"
# ========== DATABASE HANDLER ==========
class DatabaseHandler:
    def __init__(self, file_path="cashbee_db.json"):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            self._initialize_db()

    def _initialize_db(self):
        empty_structure = {
            "users": [],
            "wallets": [],
            "family_wallets": [],
            "organizations": [],
            "transactions": [],
            "counters": {
                "transaction_id": 0,
                "wallet_id": 0,
                "family_wallet_id": 0
            }
        }
        self._write_data(empty_structure)

    def _read_data(self):
        with open(self.file_path, "r") as f:
            return json.load(f)

    def _write_data(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4, default=str)

    # ---------- Generic Operations ----------
    def add_record(self, table, record, mapper):
        data = self._read_data()
        data[table].append(mapper.to_dict(record))
        self._write_data(data)

    def find_one(self, table, condition, mapper):
        data = self._read_data()
        for item in data[table]:
            if condition(item):
                return mapper.from_dict(item)
        return None

    def find_many(self, table, condition, mapper):
        data = self._read_data()
        results = []
        for item in data[table]:
            if condition(item):
                results.append(mapper.from_dict(item))
        return results

    def update_record(self, table, condition, update_func):
        data = self._read_data()
        updated = False
        for item in data[table]:
            if condition(item):
                update_func(item)
                updated = True
        if updated:
            self._write_data(data)
        return updated

    def delete_record(self, table, condition):
        data = self._read_data()
        initial_length = len(data[table])
        data[table] = [item for item in data[table] if not condition(item)]
        if len(data[table]) != initial_length:
            self._write_data(data)
            return True
        return False

    def read_data(self, table_name):
        data = self._read_data()
        return data.get(table_name, [])

    def save_data(self, table_name, record_data):
        data = self._read_data()
        data[table_name].append(record_data)
        self._write_data(data)

    def get_next_id(self, counter_name):
        data = self._read_data()
        if "counters" not in data:
            data["counters"] = {"transaction_id": 0, "wallet_id": 0, "family_wallet_id": 0}
        
        data["counters"][counter_name] += 1
        next_id = data["counters"][counter_name]
        self._write_data(data)
        return next_id

# Singleton for database handler
class DatabaseHandlerSingleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = DatabaseHandler()
        return cls._instance

# ========== ENUMS ==========
class PaymentType(Enum):
    SEND = "Send"
    RECEIVE = "Receive"
    DONATE = "Donate"
    BILL_PAY = "Bill Pay"

class BillOrganization(Enum):
    GAS = "Gas"
    WATER = "Water"
    ELECTRICITY = "Electricity"

class CharityOrganization(Enum):
    MISR_EL_KHEIR = "Misr El Kheir Foundation"
    RESALA = "Resala Charity Organization"
    FOOD_BANK = "Egyptian Food Bank"
    MAGDI_YACOUB = "Magdi Yacoub Heart Foundation"
    HOSPITAL_57357 = "57357 Children's Cancer Hospital Foundation"
    BAHEYA = "Baheya Foundation"
    COPTIC_ORTHODOX = "Coptic Orthodox"
    RED_CRESCENT = "Egyptian Red Crescent"

class Role(Enum):
    PARENT = "Parent"
    CHILD = "Child"
    USER = "User"

class RegexPattern(Enum):
    LOWERCASE_ENGLISH = r"[a-z]"
    UPPERCASE_ENGLISH = r"[A-Z]"
    NUMBERS = r"[0-9]+"
    SPECIAL_CHARACTERS = r"[!@#$%^&*(),.?\":{}|<>]"

class TransactionLimits(Enum):
    PER_OPERATION_LIMIT = 500
    DAILY_LIMIT = 1500
    WEEKLY_LIMIT = 10500
    MONTHLY_LIMIT = 315000

# ========== STRATEGY PATTERN: VALIDATORS ==========
class ValidationStrategy(ABC):
    @abstractmethod
    def is_valid(self, value) -> bool:
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        pass

class NationalIDValidationStrategy(ValidationStrategy):
    def is_valid(self, nid) -> bool:
        if len(nid) != 14 or not nid.isdigit():
            return False

        century_digit = int(nid[0])
        if century_digit not in [2, 3]:
            return False

        year = int(nid[1:3])
        month = int(nid[3:5])
        day = int(nid[5:7])

        if century_digit == 2:
            year += 1900
        else:
            year += 2000

        try:
            date(year, month, day)
        except ValueError:
            return False
            
        today = date.today()
        age = today.year - year
        if (today.month, today.day) < (month, day):
            age -= 1
            
        return age > 18

    def get_error_message(self) -> str:
        return "Invalid National ID or under 18 years old"

class ChildNationalIDValidationStrategy(ValidationStrategy):
    def is_valid(self, nid) -> bool:
        if len(nid) != 14 or not nid.isdigit():
            return False

        century_digit = int(nid[0])
        if century_digit not in [2, 3]:
            return False

        year = int(nid[1:3])
        month = int(nid[3:5])
        day = int(nid[5:7])

        if century_digit == 2:
            year += 1900
        else:
            year += 2000

        try:
            date(year, month, day)
        except ValueError:
            return False
            
        today = date.today()
        age = today.year - year
        if (today.month, today.day) < (month, day):
            age -= 1
            
        return 0 <= age < 18  # Child must be under 18

    def get_error_message(self) -> str:
        return "Invalid National ID or not a child (must be under 18 years old)"

class PhoneValidationStrategy(ValidationStrategy):
    def is_valid(self, value) -> bool:
        try:
            parsed = phonenumbers.parse(value, "EG")
            return phonenumbers.is_valid_number(parsed)
        except NumberParseException:
            return False

    def get_error_message(self) -> str:
        return "Invalid phone number format"

class PasswordValidationStrategy(ValidationStrategy):
    def is_valid(self, password) -> bool:
        if len(password) != 10:
            return False
        if not re.search(RegexPattern.LOWERCASE_ENGLISH.value, password):
            return False
        if not re.search(RegexPattern.UPPERCASE_ENGLISH.value, password):
            return False
        if not re.search(RegexPattern.NUMBERS.value, password):
            return False
        if not re.search(RegexPattern.SPECIAL_CHARACTERS.value, password):
            return False
        return True

    def get_error_message(self) -> str:
        return "Password must be 10 characters with uppercase, lowercase, number, and special character"

class EnglishNameValidationStrategy(ValidationStrategy):
    def is_valid(self, val) -> bool:
        pattern = rf"^{RegexPattern.UPPERCASE_ENGLISH.value}{RegexPattern.LOWERCASE_ENGLISH.value}+ {RegexPattern.UPPERCASE_ENGLISH.value}{RegexPattern.LOWERCASE_ENGLISH.value}+$"
        return bool(re.fullmatch(pattern, val))

    def get_error_message(self) -> str:
        return "Name must contain exactly two English words, each starting with a capital letter"

# Validator Context using Strategy Pattern
class ValidatorContext:
    def __init__(self, strategy: ValidationStrategy):
        self._strategy = strategy
        
    def set_strategy(self, strategy: ValidationStrategy):
        self._strategy = strategy
        
    def validate(self, value) -> bool:
        return self._strategy.is_valid(value)
        
    def get_error(self) -> str:
        return self._strategy.get_error_message()
class ValidationsNames(Enum):
    NAME = ValidatorContext(EnglishNameValidationStrategy())
    PHONE = ValidatorContext(PhoneValidationStrategy())
    PASSWORD = ValidatorContext(PasswordValidationStrategy())
    NATIONALID = ValidatorContext(ChildNationalIDValidationStrategy())
# ========== DOMAIN MODELS ==========
class Transaction:
    transaction_id = 0
    def __init__(self, userid, amount, tx_type, to, dt, transaction_id):
        self.transaction_id = transaction_id
        self.userid = userid
        self.amount = amount
        self.type = tx_type
        self.date = dt or datetime.now()
        self.to = to
        
    def show_details(self):
        return f"{self.date.strftime('%Y-%m-%d %H:%M')} | {self.type.value} | {self.to} | {self.amount} EGP"

class User:
    def __init__(self, phone, uid, name, password, role=Role.USER,fm = -1):
        self._phone_number = phone
        self._user_identifier = uid
        self._name = name
        self._password = password
        self._role = role
        self.walletid = -1
        self.family_wallet_id = fm 
        self.failed_attempts = 0
        self.lock_until = None        
    @property
    def phone_number(self):
        return self._phone_number        
    @property
    def user_identifier(self):
        return self._user_identifier       
    @property
    def name(self):
        return self._name        
    @property
    def role(self):
        return self._role        
    @property
    def password(self):
        return self._password        
    @property
    def wallet(self):
        return self.walletid
        
    @property
    def family_wallet(self):
        return self.family_wallet_id        
    @phone_number.setter
    def phone_number(self, value):
        validator = ValidatorContext(PhoneValidationStrategy())
        if validator.validate(value):
            self._phone_number = value
            print("Telephone number updated successfully")
        else:
            print(f"❌ {validator.get_error()}")          
    @wallet.setter
    def wallet(self, val):
        if self.walletid == -1:
            self.walletid = val
        else:
            raise ValueError("You already have a wallet")           
    @family_wallet.setter
    def family_wallet(self,val):
        if self.family_wallet_id == -1:
            self.family_wallet_id = val
        else:
            raise ValueError("You already have a family wallet")

class Wallet:
    def __init__(self, balance=0, transaction_limit=TransactionLimits.PER_OPERATION_LIMIT.value, 
                 max_limit=TransactionLimits.MONTHLY_LIMIT.value, wallet_id=None):
        if wallet_id is None:
            db_handler = DatabaseHandlerSingleton()
            self.walletid = db_handler.get_next_id("wallet_id")
        else:
            self.walletid = wallet_id
        self._balance = balance
        self._transaction_limit = transaction_limit
        self._max_limit = max_limit
        self._transactions = []        
    @property
    def balance(self):
        return self._balance        
    @property
    def transaction_limit(self):
        return self._transaction_limit        
    @property
    def transactions(self):
        return self._transactions      
    @property
    def max_transaction_limit(self):
        return self._max_limit    
    @transaction_limit.setter
    def transaction_limit(self, amount):
        if amount > self.max_transaction_limit:
            raise ValueError("Limit exceeds maximum allowed")
        self._transaction_limit = amount        
    @transactions.setter
    def transactions(self, transaction):
        self._transactions.append(transaction)
    @balance.setter    
    def balance(self, amount):
        self._balance += amount

# ========== FACTORY METHOD PATTERN: PAYMENTS ==========
class Payment(ABC):
    def __init__(self, from_user_id, amount, to, tx_type):
        self.from_user_id = from_user_id  
        self.amount = amount
        self.to = to
        self.tx_type = tx_type
        self.date = datetime.now()

    @abstractmethod
    def execute(self, wallet: Wallet) -> str:
        pass

    def _validate(self, wallet:Wallet) -> str | None:
        """مشتركة بين كل العمليات"""
        if self.amount <= 0:
            return "❌ Invalid amount"
        if self.tx_type != PaymentType.RECEIVE:  
            if self.amount > wallet.balance:
                return "❌ Insufficient balance"
            if self.amount > wallet.transaction_limit:
                return "❌ Exceeds transaction limit"
        return None

    def _create_transaction(self):
        Transaction.tid += 1
        return Transaction(
            id=Transaction.tid,
            userid=self.from_user_id,
            amount=self.amount,
            dt=self.date,
            tx_type=self.tx_type,
            to=self.to,
        )
# ===== Implementations =====
class SendPayment(Payment):
    def __init__(self, from_user_id, amount, to):
        super().__init__(from_user_id, amount, to, PaymentType.SEND)

    def execute(self, wallet: "Wallet") -> str:
        error = self._validate(wallet)
        if error:
            return error
        wallet.balance(-self.amount)
        wallet.transactions(self._create_transaction())
        return f"✅ {self.tx_type.value} successful"
class ReceivePayment(Payment):
    def __init__(self, from_user_id, amount, to):
        super().__init__(from_user_id, amount, to, PaymentType.RECEIVE)

    def execute(self, wallet: "Wallet") -> str:
        wallet.balance(self.amount)
        wallet.transactions(self._create_transaction())
        return f"✅ {self.tx_type.value} successful"
class DonationPayment(Payment):
    def __init__(self, from_user_id, amount, to):
        super().__init__(from_user_id, amount, to, PaymentType.DONATE)

    def execute(self, wallet: "Wallet") -> str:
        error = self._validate(wallet)
        if error:
            return error
        wallet.balance(-self.amount)
        wallet.transactions(self._create_transaction())
        return f"✅ {self.tx_type.value} successful"
class BillPayment(Payment):
    def __init__(self, from_user_id, amount, to):
        super().__init__(from_user_id, amount, to, PaymentType.BILL_PAY)

    def execute(self, wallet: "Wallet") -> str:
        error = self._validate(wallet)
        if error:
            return error
        wallet.balance(-self.amount)
        wallet.transactions(self._create_transaction())
        return f"✅ {self.tx_type.value} successful"
# ===== Factory =====
class PaymentFactory:
    @staticmethod
    def create_payment(payment_type, from_user_id, amount, to) -> Payment:
        if payment_type == PaymentType.SEND:
            return SendPayment(from_user_id, amount, to)
        elif payment_type == PaymentType.RECEIVE:
            return ReceivePayment(from_user_id, amount, to)
        elif payment_type == PaymentType.DONATE:
            return DonationPayment(from_user_id, amount, to)
        elif payment_type == PaymentType.BILL_PAY:
            return BillPayment(from_user_id, amount, to)
        else:
            raise ValueError("❌ Invalid payment type")

class UserSession:
    _instance = None
    _current_user = None    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserSession, cls).__new__(cls)
        return cls._instance        
    @classmethod
    def set_user(cls, user):
        cls._current_user = user
        
    @classmethod
    def get_user(cls):
        return cls._current_user
        
    @classmethod
    def clear_user(cls):
        cls._current_user = None

# ========== OBSERVER PATTERN: TRANSACTION NOTIFICATIONS ==========
class TransactionObserver(ABC):
    @abstractmethod
    def update(self, transaction: Transaction):
        pass
class SMSNotificationObserver(TransactionObserver):
    def update(self, transaction: Transaction):
        print(f"SMS: Transaction {transaction.transaction_id} of {transaction.amount} EGP completed")
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

# ========== ROLE MANAGEMENT ==========
class RoleManager:
    @staticmethod
    def calculate_age_from_national_id(national_id: str) -> int:
        """Calculate age from Egyptian national ID"""
        if len(national_id) != 14 or not national_id.isdigit():
            return -1
            
        century_digit = int(national_id[0])
        year = int(national_id[1:3])
        month = int(national_id[3:5])
        day = int(national_id[5:7])
        
        if century_digit == 2:
            year += 1900
        elif century_digit == 3:
            year += 2000
        else:
            return -1
            
        try:
            birth_date = date(year, month, day)
        except ValueError:
            return -1
            
        today = date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
            
        return age
    
    @staticmethod
    def can_change_to_parent(user: User) -> tuple[bool, str]:
        """Check if user can change role to parent based on age"""
        age = RoleManager.calculate_age_from_national_id(user.user_identifier)
        
        if age < 0:
            return False, "Invalid National ID"
        
        if user.role == Role.PARENT:
            return False, "Already a parent"
            
        if age < 25:
            return False, f"Must be at least 25 years old to become a parent. Current age: {age}"
            
        return True, f"Age {age} - Eligible to become a parent"
    
    @staticmethod
    def change_user_role(user: User, new_role: Role, db_handler) -> str:
        """Change user role with validation"""
        if new_role == Role.PARENT:
            can_change, message = RoleManager.can_change_to_parent(user)
            if not can_change:
                return f"❌ Cannot change to parent: {message}"
        
        # Update user role
        user._role = new_role
        
        # Update in database
        db_handler.update_record("users", 
                               lambda u: u.get("phone_number") == user.phone_number,
                               lambda item: item.update({"role": new_role.value}))
        
        return f"✅ Role changed to {new_role.value} successfully"

# ========== DATA MAPPER PATTERN ==========
class UserMapper:
    @staticmethod
    def to_dict(user: User):
        return {
            "name": user.name,
            "phone_number": user.phone_number,
            "national_id": user.user_identifier,
            "password": user.password,
            "role": user.role.value,
            "walletid": user.walletid,
            "family_wallet_id": user.family_wallet_id,
            "failed_attempts": user.failed_attempts,
            "lock_until": user.lock_until.isoformat() if user.lock_until else None
        }

    @staticmethod
    def from_dict(data: dict):
        user = User(
            phone=data["phone_number"],
            uid=data["national_id"],
            name=data["name"],
            password=data["password"],
            role=Role(data["role"])
        )
        user.walletid = data.get("walletid", -1)
        user.family_wallet_id = data.get("family_wallet_id", -1)
        user.failed_attempts = data.get("failed_attempts", 0)
        lock_until = data.get("lock_until")
        user.lock_until = datetime.fromisoformat(lock_until) if lock_until else None
        return user

class WalletMapper:
    @staticmethod
    def to_dict(wallet: Wallet):
        return {
            "wallet_id": wallet.walletid,
            "balance": wallet.balance,
            "transaction_limit": wallet.transaction_limit,
            "max_limit": wallet.max_transaction_limit,
            "transactions": [TransactionMapper.to_dict(tx) for tx in wallet.transactions]
        }

    @staticmethod
    def from_dict(data: dict):
        wallet = Wallet(
            balance=data["balance"],
            transaction_limit=data["transaction_limit"],
            max_limit=data["max_limit"],
            wallet_id=data["wallet_id"]
        )
        wallet._transactions = [TransactionMapper.from_dict(tx) for tx in data.get("transactions", [])]
        return wallet

class TransactionMapper:
    @staticmethod
    def to_dict(tx: Transaction):
        return {
            "transaction_id": tx.transaction_id,
            "user_id": tx.userid,
            "amount": tx.amount,
            "t_type": tx.type.value,
            "date": tx.date.isoformat(),
            "to": tx.to
        }

    @staticmethod
    def from_dict(data: dict):
        return Transaction(
            userid=data["user_id"],
            amount=data["amount"],
            tx_type=PaymentType(data["t_type"]),
            to=data["to"],
            dt=datetime.fromisoformat(data["date"]),
            transaction_id=data["transaction_id"]
        )

# ========== FAMILY WALLET OPERATIONS ==========
PREDEFINED_PASSWORD = 123456

class FamilyWallet:
    def __init__(self, parent_phone_number, family_id=None):
        if family_id is None:
            db_handler = DatabaseHandlerSingleton()
            self.family_id = db_handler.get_next_id("family_wallet_id")
        else:
            self.family_id = family_id
        self.parent = parent_phone_number
        self.members = {}  # national_id -> member info

# ========== FAMILY WALLET MAPPER ==========
class FamilyWalletMapper:
    @staticmethod
    def to_dict(fw: FamilyWallet) -> dict:
        """
        Convert FamilyWallet object to dictionary for storage
        """
        return {
            "family_id": fw.family_id,
            "parent_phone": fw.parent,
            "members": fw.members,
            "created_date": datetime.now().isoformat()
        }

    @staticmethod
    def from_dict(data: dict) -> FamilyWallet:
        """
        Convert dictionary to FamilyWallet object
        """
        if not data:
            return None
            
        family_wallet = FamilyWallet(data["parent_phone"], data["family_id"])
        family_wallet.members = data.get("members", {})
        
        return family_wallet

    @staticmethod
    def update_member_in_family_wallet(db_handler, family_id, member_id, member_data):
        """
        Update a specific member in the family wallet
        """
        def update_func(item):
            if item["family_id"] == family_id:
                if "members" not in item:
                    item["members"] = {}
                item["members"][member_id] = member_data
        
        db_handler.update_record("family_wallets", 
                               lambda item: item["family_id"] == family_id, 
                               update_func)

    @staticmethod
    def remove_member_from_family_wallet(db_handler, family_id, member_id):
        """
        Remove a member from the family wallet
        """
        def update_func(item):
            if item["family_id"] == family_id and "members" in item and member_id in item["members"]:
                del item["members"][member_id]
        
        db_handler.update_record("family_wallets", 
                               lambda item: item["family_id"] == family_id, 
                               update_func)

# ========== CHILD ACCOUNT MANAGER ==========
class ChildAccountManager:
    def __init__(self, db_handler):
        self.db_handler = db_handler
        
    def create_child_account(self, parent_user:User, child_phone, child_national_id, child_name, child_password):
        """Create child account 
        with child-specific validation"""
        # Validate parent role
        if parent_user.role != Role.PARENT:
            return "❌ Only parents can create child accounts"
        
        # Check if child already exists
        existing_child = self.db_handler.find_one("users", 
                                                 lambda u: u.get("national_id") == child_national_id, 
                                                 UserMapper)
        if existing_child:
            return "❌ Child account already exists"
        
        # Check validations
        vc = ValidationCheck(phone=child_phone,national_id=child_national_id,name=child_name,password=child_password)
        msg = vc.check()
        if msg:
            return msg
        
        child_user = User(child_phone,child_national_id,child_name,child_password,Role.CHILD,parent_user.family_wallet_id)
        # Save child user to database
        self.db_handler.add_record("users", child_user, UserMapper)
        
        # Create wallet for child
        child_wallet = Wallet()
        self.db_handler.add_record("wallets", child_wallet, WalletMapper)
        
        # Update child user with wallet ID
        child_user.wallet = child_wallet.walletid
        self.db_handler.update_record("users", 
                                    lambda u: u.get("national_id") == child_national_id,
                                    lambda item: item.update({"walletid": child_wallet.walletid}))
        
        return child_user, f"✅ Child account created successfully for {child_name}"

# ========== ENHANCED FAMILY WALLET FACADE ==========
class FamilyWalletFacade:
    def __init__(self, family_wallet: FamilyWallet):
        self.family_wallet = family_wallet
        self.db_handler = DatabaseHandler()
        self.child_account_manager = ChildAccountManager(self.db_handler)
        
    def add_member(self, parent_user, child_phone=None, child_national_id=None, 
                   child_name=None, child_password=None, initial_limit=500):
        """
        Add member to family wallet - can be existing user or create new child account
        If child_phone is provided without other details, looks for existing user
        If all child details are provided, creates new account if needed
        """
        # If only phone is provided, look for existing user
        if child_phone and not child_national_id:
            existing_user = self.db_handler.find_one("users", 
                                                   lambda u: u.get("phone_number") == child_phone, 
                                                   UserMapper)
            if not existing_user:
                return "❌ User not found. Please provide complete details to create new child account."
            
            child_user = existing_user
            
        # If all details provided, check if user exists or create new one
        elif child_phone and child_national_id and child_name and child_password:
            # First check if user already exists
            existing_user = self.db_handler.find_one("users", 
                                                   lambda u: u.get("national_id") == child_national_id, 
                                                   UserMapper)
            
            if existing_user:
                child_user = existing_user
            else:
                # Create new child account
                result = self.child_account_manager.create_child_account(
                    parent_user, child_phone, child_national_id, child_name, child_password
                )
                
                if isinstance(result, tuple):
                    child_user, creation_message = result
                    print(creation_message)  # Show creation success message
                else:
                    return result  # Return error message
        else:
            return "❌ Invalid parameters. Provide either phone number only (for existing user) or all details (for new account)"
        
        # Check if member already exists in family wallet
        if child_user.user_identifier in self.family_wallet.members:
            return "❌ Member already exists in family wallet"
            
        # Ensure child has a wallet
        if child_user.walletid == -1:
            child_wallet = Wallet()
            self.db_handler.add_record("wallets", child_wallet, WalletMapper)
            child_user.wallet = child_wallet.walletid
            self.db_handler.update_record("users", 
                                        lambda u: u.get("national_id") == child_user.user_identifier,
                                        lambda item: item.update({"walletid": child_wallet.walletid}))
            
        member_data = {
            "user": child_user.name,
            "limit": initial_limit,
            "wallet": child_user.walletid,
            "password": PREDEFINED_PASSWORD,
            "added_date": datetime.now().isoformat(),
            "phone": child_user.phone_number
        }
        
        # Update in memory
        self.family_wallet.members[child_user.user_identifier] = member_data
        
        # Update in database
        FamilyWalletMapper.update_member_in_family_wallet(
            self.db_handler,
            self.family_wallet.family_id,
            child_user.user_identifier,
            member_data
        )
        
        return f"✅ {child_user.name} added to family wallet successfully"
        
    def get_member_info(self, child_id):
        member = self.family_wallet.members.get(child_id)
        if not member:
            return "❌ Member not found"
            
        return (f"Member: {member['user']}\n"
                f"Phone: {member.get('phone', 'N/A')}\n"
                f"Spending Limit: {member['limit']} EGP\n"
                f"Wallet ID: {member['wallet']}\n"
                f"Added: {member.get('added_date', 'N/A')}")
        
    def remove_member(self, child_id):
        if child_id not in self.family_wallet.members:
            return "❌ Member not found"
            
        # Remove from memory
        del self.family_wallet.members[child_id]
        
        # Remove from database
        FamilyWalletMapper.remove_member_from_family_wallet(
            self.db_handler,
            self.family_wallet.family_id,
            child_id
        )
        
        return "✅ Member removed successfully"
        
    def set_limit(self, child_id, new_limit):
        if child_id not in self.family_wallet.members:
            return "❌ Member not found"
            
        # Update in memory
        self.family_wallet.members[child_id]["limit"] = new_limit
        
        # Update in database
        FamilyWalletMapper.update_member_in_family_wallet(
            self.db_handler,
            self.family_wallet.family_id,
            child_id,
            self.family_wallet.members[child_id]
        )
        
        return "✅ Spending limit updated"
        
    def see_history(self, child_id):
        if child_id not in self.family_wallet.members:
            print("❌ Member not found")
            return
            
        member_info = self.family_wallet.members[child_id]
        wallet_data = self.db_handler.find_one("wallets", 
                                             lambda t: t["wallet_id"] == member_info["wallet"], 
                                             WalletMapper)
        
        if wallet_data:
            print(f"\nTransaction History for {member_info['user']}:")
            print("=" * 60)
            if wallet_data.transactions:
                for tx in wallet_data.transactions:
                    print(tx.show_details())
            else:
                print("No transactions found")
            print("=" * 60)
        else:
            print("❌ No wallet found for this member")
                
    def see_all_children_history(self):
        if not self.family_wallet.members:
            print("❌ Your family members are empty")
            return
            
        print("\n=== Family Members Transaction History ===")
        for child_id, member_info in self.family_wallet.members.items():
            self.see_history(child_id)
            print()  # Add spacing between members
            
    def list_all_members(self):
        """List all family members with their basic info"""
        if not self.family_wallet.members:
            return "❌ No family members found"
        
        result = "=== Family Members ===\n"
        for child_id, member_info in self.family_wallet.members.items():
            result += f"ID: {child_id}\n"
            result += f"Name: {member_info['user']}\n"
            result += f"Phone: {member_info.get('phone', 'N/A')}\n"
            result += f"Limit: {member_info['limit']} EGP\n"
            result += f"Added: {member_info.get('added_date', 'N/A')}\n"
            result += "-" * 30 + "\n"
        
        return result

# ========== FACADE PATTERN: REGISTRATION ==========
class RegistrationFacade:
    def __init__(self):
        self.db_handler = DatabaseHandlerSingleton()
              
    def register_user(self, user: User):
        # Check if user already exists
        existing_user = self.db_handler.find_one("users", 
                                                lambda u: u.get("national_id") == user.user_identifier, 
                                                UserMapper)
        if existing_user:
            return "❌ National ID already exists, Go to login"
        
        # Validate using Strategy Pattern
        vc = ValidationCheck(phone=user.phone,national_id=user.user_identifier,name=user.name,password=user.password)
        msg = vc.check()
        if msg:
            return msg
        
        # Save user to database
        self.db_handler.add_record("users", user, UserMapper)
        return "✅ Account has been created successfully"
        
    def login_user(self, phone, password):
        user_data = self.db_handler.find_one("users", 
                                           lambda u: u.get("phone_number") == phone, 
                                           UserMapper)
        if not user_data:
            return "❌ User does not exist, Sign Up first"
            
        user = user_data
        
        # Check if account is locked
        if user.lock_until and datetime.now() < user.lock_until:
            remaining = (user.lock_until - datetime.now()).seconds // 60
            return f"⛔ Account locked. Try again after {remaining} minutes"
            
        # Check password
        if user.password != password:
            user.failed_attempts += 1
            if user.failed_attempts >= 3:
                user.lock_until = datetime.now() + timedelta(minutes=30)
                user.failed_attempts = 0
                # Update user in database
                self.db_handler.update_record("users", 
                                            lambda u: u.get("phone_number") == phone,
                                            lambda item: item.update(UserMapper.to_dict(user)))
                return "⛔ Too many failed attempts. Account locked for 30 minutes"
            else:
                remaining = 3 - user.failed_attempts
                # Update user in database
                self.db_handler.update_record("users", 
                                            lambda u: u.get("phone_number") == phone,
                                            lambda item: item.update(UserMapper.to_dict(user)))
                return f"❌ Invalid password. You have {remaining} attempt(s) left"
                
        # Successful login
        user.failed_attempts = 0
        user.lock_until = None
        # Update user in database
        self.db_handler.update_record("users", 
                                    lambda u: u.get("phone_number") == phone,
                                    lambda item: item.update(UserMapper.to_dict(user)))
        UserSession.set_user(user)
        return f"✅ Login successful! Hello {user.name}"

# ========== TRANSACTION OPERATIONS WITH OBSERVER ==========
class TransactionOperation:
    def __init__(self, user1: User,dbhandler, user2: User = None):
        self.user1 = user1
        self.user2 = user2
        self.db_handler = dbhandler
        self.transaction_subject = TransactionSubject()
        # Attach observers
        self.transaction_subject.attach(SMSNotificationObserver())
        
    def execute_transaction(self, payment_type, amount, to):
        # Get sender's wallet
        sender_wallet = self.db_handler.find_one("wallets", 
                                                lambda w: w["wallet_id"] == self.user1.walletid, 
                                                WalletMapper)
        if not sender_wallet:
            return "❌ Sender wallet not found"
            
        payment = PaymentFactory.create_payment(payment_type, amount, to)
        result = payment.execute(sender_wallet)
        
        if result.startswith("✅"):
            # Update wallet in database
            self.db_handler.update_record("wallets", 
                                        lambda w: w["wallet_id"] == sender_wallet.walletid,
                                        lambda item: item.update(WalletMapper.to_dict(sender_wallet)))
            
            # Handle receive payment for recipient
            if payment_type == PaymentType.SEND and self.user2:
                recipient_wallet = self.db_handler.find_one("wallets", 
                                                          lambda w: w["wallet_id"] == self.user2.walletid, 
                                                          WalletMapper)
                if recipient_wallet:
                    receive_payment = ReceivePayment(amount, self.user1.phone_number)
                    receive_payment.execute(recipient_wallet)
                    # Update recipient wallet in database
                    self.db_handler.update_record("wallets", 
                                                lambda w: w["wallet_id"] == recipient_wallet.walletid,
                                                lambda item: item.update(WalletMapper.to_dict(recipient_wallet)))
            
            # Notify observers
            if sender_wallet.transactions:
                transaction = sender_wallet.transactions[-1]
                transaction.userid = self.user1.user_identifier
                self.transaction_subject.notify(transaction)
            
        return result

def main():
    # Initialize components
    db_handler = DatabaseHandlerSingleton()
    registration = RegistrationFacade()
    user_session = UserSession()
    
    while True:
        print("\n=== CashBee - Family Wallet Management ===")
        if user_session.get_user() is None:
            print("1. Register")
            print("2. Login")
            print("3. Exit")
            
            try:
                choice = input("Please choose an option: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nThank you for using CashBee!")
                break
                
            if choice == "1":
                # Registration use case
                print("\n--- Registration ---")
                try:
                    phone = input("Phone number: ").strip()
                    national_id = input("National ID: ").strip()
                    name = input("Full name (First Last): ").strip()
                    password = input("Password: ").strip()
                    
                    user = User(phone,national_id,name, password,Role.USER)
                    
                    result = registration.register_user(user)
                    print(result)
                except (EOFError, KeyboardInterrupt):
                    print("\nOperation cancelled.")
                    
            elif choice == "2":
                # Login use case
                print("\n--- Login ---")
                try:
                    phone = input("Phone number: ").strip()
                    password = input("Password: ").strip()
                    
                    result = registration.login_user(phone, password)
                    print(result)
                except (EOFError, KeyboardInterrupt):
                    print("\nOperation cancelled.")
                    
            elif choice == "3":
                print("Thank you for using CashBee!")
                break
            else:
                print("Invalid option. Please try again.")
                
        else:
            current_user = user_session.get_user()
            print(f"Welcome, {current_user.name} ({current_user.role.value})!")
            print("1. View Wallet")
            print("2. Make Transaction")
            print("3. View Transaction History")
            print("4. Change Role")
            
            if current_user.role == Role.PARENT:
                print("5. Family Wallet Operations")
                print("6. Logout")
            else:
                print("5. Logout")
            
            try:
                choice = input("Please choose an option: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nThank you for using CashBee!")
                break
            
            if choice == "1":
                # View Wallet use case
                print("\n--- Wallet Overview ---")
                wallet = db_handler.find_one("wallets", 
                                           lambda w: w["wallet_id"] == current_user.walletid, 
                                           WalletMapper)
                if wallet:
                    print(f"Balance: {wallet.balance} EGP")
                    print(f"Transaction Limit: {wallet.transaction_limit} EGP")
                    print(f"Max Limit: {wallet.max_transaction_limit} EGP")
                else:
                    print("No wallet found. Would you like to create one?")
                    try:
                        create_wallet = input("Create wallet? (y/n): ").strip().lower()
                        if create_wallet == 'y':
                            new_wallet = Wallet()
                            db_handler.add_record("wallets", new_wallet, WalletMapper)
                            current_user.wallet = new_wallet.walletid
                            # Update user in database
                            db_handler.update_record("users", 
                                                   lambda u: u.get("phone_number") == current_user.phone_number,
                                                   lambda item: item.update({"walletid": new_wallet.walletid}))
                            print("Wallet created successfully!")
                    except (EOFError, KeyboardInterrupt):
                        print("\nOperation cancelled.")
                
            elif choice == "2":
                # Make Transaction use case
                print("\n--- Make Transaction ---")
                print("1. Send Money")
                print("2. Receive Money")
                print("3. Donate to Charity")
                print("4. Pay Bill")
                
                try:
                    tx_choice = input("Choose transaction type: ").strip()
                    amount = float(input("Amount: ").strip())
                    
                    wallet = db_handler.find_one("wallets", 
                                               lambda w: w["wallet_id"] == current_user.walletid, 
                                               WalletMapper)
                    
                    if not wallet:
                        print("❌ No wallet found. Please create a wallet first.")
                        continue
                    
                    if tx_choice == "1":
                        # Send money use case
                        recipient_phone = input("Recipient phone number: ").strip()
                        
                        # Validate recipient phone
                        phone_validator = ValidatorContext(PhoneValidationStrategy())
                        if not phone_validator.validate(recipient_phone):
                            print(f"❌ {phone_validator.get_error()}")
                            continue
                        
                        # Check if recipient exists
                        recipient = db_handler.find_one("users", 
                                                      lambda u: u.get("phone_number") == recipient_phone, 
                                                      UserMapper)
                        if not recipient:
                            print("❌ Recipient not found")
                            continue
                        
                        # Create transaction operation
                        tx_operation = TransactionOperation(current_user, db_handler,recipient)
                        result = tx_operation.execute_transaction(PaymentType.SEND, amount, recipient_phone)
                        print(result)
                        
                    elif tx_choice == "2":
                        # Receive money use case (simplified - usually triggered by sender)
                        sender_phone = input("Sender phone number: ").strip()
                        tx_operation = TransactionOperation(current_user,db_handler)
                        result = tx_operation.execute_transaction(PaymentType.RECEIVE, amount, sender_phone)
                        print(result)
                        
                    elif tx_choice == "3":
                        # Donate to charity use case
                        print("Available charities:")
                        charities = list(CharityOrganization)
                        for i, charity in enumerate(charities, 1):
                            print(f"{i}. {charity.value}")
                        
                        charity_choice = int(input("Choose charity: ").strip()) - 1
                        if 0 <= charity_choice < len(charities):
                            selected_charity = charities[charity_choice]
                            tx_operation = TransactionOperation(current_user,db_handler)
                            result = tx_operation.execute_transaction(PaymentType.DONATE, amount, selected_charity.value)
                            print(result)
                        else:
                            print("❌ Invalid charity selection")
                            
                    elif tx_choice == "4":
                        # Pay bill use case
                        print("Available bill organizations:")
                        orgs = list(BillOrganization)
                        for i, org in enumerate(orgs, 1):
                            print(f"{i}. {org.value}")
                        
                        org_choice = int(input("Choose organization: ").strip()) - 1
                        if 0 <= org_choice < len(orgs):
                            selected_org = orgs[org_choice]
                            tx_operation = TransactionOperation(current_user,db_handler)
                            result = tx_operation.execute_transaction(PaymentType.BILL_PAY, amount, selected_org.value)
                            print(result)
                        else:
                            print("❌ Invalid organization selection")
                            
                    else:
                        print("Invalid transaction type")
                        
                except (ValueError, EOFError, KeyboardInterrupt):
                    print("❌ Invalid input or operation cancelled")
                    
            elif choice == "3":
                # View Transaction History use case
                print("\n--- Transaction History ---")
                wallet = db_handler.find_one("wallets", 
                                           lambda w: w["wallet_id"] == current_user.walletid, 
                                           WalletMapper)
                if wallet and wallet.transactions:
                    print("Date & Time         | Type     | To/From              | Amount (EGP)")
                    print("-" * 70)
                    for transaction in wallet.transactions:
                        print(transaction.show_details())
                else:
                    print("No transactions found")
                    
            elif choice == "4":
                # Change Role use case
                print("\n--- Change Role ---")
                print(f"Current role: {current_user.role.value}")
                
                age = RoleManager.calculate_age_from_national_id(current_user.user_identifier)
                print(f"Your age: {age} years")
                
                print("\nAvailable roles:")
                print("1. User")
                print("2. Parent")
                  
                try:
                    role_choice = input("Choose new role: ").strip()
                    
                    if role_choice == "1":
                        result = RoleManager.change_user_role(current_user, Role.USER, db_handler)
                        print(result)
                    elif role_choice == "2":
                        result = RoleManager.change_user_role(current_user, Role.PARENT, db_handler)
                        print(result)
                    else:
                        print("❌ Invalid role selection")
                        
                except (EOFError, KeyboardInterrupt):
                    print("\nOperation cancelled.")
                    
            elif choice == "5":
                if current_user.role == Role.PARENT:
                   # Family Wallet Operations use case (for parents only)
                    print("\n--- Family Wallet Operations ---")
                    family_wallet = db_handler.find_one("family_wallets", 
                                                    lambda fw: fw.get("parent_phone") == current_user.phone_number, 
                                                    FamilyWalletMapper)
                    
                    if not family_wallet:
                        print("No family wallet found. Creating one...")
                        family_wallet = FamilyWallet(current_user.phone_number)
                        db_handler.add_record("family_wallets", family_wallet, FamilyWalletMapper)
                        current_user.family_wallet = family_wallet.family_id
                        
                        # Update user record with family wallet ID
                        db_handler.update_record("users", 
                                            lambda u: u.get("phone_number") == current_user.phone_number,
                                            lambda item: item.update({"family_wallet_id": family_wallet.family_id}))
                        
                        print("Family wallet created successfully!")
                    
                    family_ops = FamilyWalletFacade(family_wallet)
                    
                    print("\n1. Add Family Member")
                    print("2. View Member Info")
                    print("3. Remove Member")
                    print("4. Set Spending Limit")
                    print("5. View Member Transaction History")
                    print("6. View All Members History")
                    print("7. List All Members")
                    print("8. Back to Main Menu")
                    
                    try:
                        family_choice = input("Choose option: ").strip()
                        
                        if family_choice == "1":
                            # Add family member - enhanced to handle both existing and new users
                            print("\n--- Add Family Member ---")
                            print("1. Add existing user by phone")
                            print("2. Create new child account and add to family")
                            
                            add_type = input("Choose option: ").strip()
                            
                            if add_type == "1":
                                # Add existing user
                                member_phone = input("Member phone number: ").strip()
                                initial_limit = float(input("Initial spending limit: ").strip())
                                
                                result = family_ops.add_member(
                                    current_user, 
                                    child_phone=member_phone, 
                                    initial_limit=initial_limit
                                )
                                print(result)
                                
                            elif add_type == "2":
                                # Create new child and add to family
                                print("Enter new child's information:")
                                child_name = input("Child's full name (First Last): ").strip()
                                child_phone = input("Child's phone number: ").strip()
                                child_national_id = input("Child's National ID: ").strip()
                                child_password = input("Child's password: ").strip()
                                initial_limit = float(input("Initial spending limit: ").strip())
                                
                                result = family_ops.add_member(
                                    current_user,
                                    child_phone=child_phone,
                                    child_national_id=child_national_id,
                                    child_name=child_name,
                                    child_password=child_password,
                                    initial_limit=initial_limit
                                )
                                print(result)
                            else:
                                print("❌ Invalid option")
                                
                        elif family_choice == "2":
                            # View member info
                            member_id = input("Member National ID: ").strip()
                            info = family_ops.get_member_info(member_id)
                            print(info)
                            
                        elif family_choice == "3":
                            # Remove member
                            member_id = input("Member National ID: ").strip()
                            result = family_ops.remove_member(member_id)
                            print(result)
                            
                        elif family_choice == "4":
                            # Set spending limit
                            member_id = input("Member National ID: ").strip()
                            new_limit = float(input("New spending limit: ").strip())
                            result = family_ops.set_limit(member_id, new_limit)
                            print(result)
                            
                        elif family_choice == "5":
                            # View member transaction history
                            member_id = input("Member National ID: ").strip()
                            family_ops.see_history(member_id)
                            
                        elif family_choice == "6":
                            # View all members history
                            family_ops.see_all_children_history()
                            
                        elif family_choice == "7":
                            # List all members
                            members_list = family_ops.list_all_members()
                            print(members_list)
                            
                        elif family_choice == "8":
                            continue
                        else:
                            print("Invalid option")
                            
                    except (ValueError, EOFError, KeyboardInterrupt):
                        print("❌ Invalid input or operation cancelled")        
                else:
                    # Logout for non-parent users
                    user_session.clear_user()
                    print("Logged out successfully!")

            elif choice == "6" and current_user.role == Role.PARENT:
                # Logout use case for parents
                user_session.clear_user()
                print("Logged out successfully!")
                
            else:
                print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
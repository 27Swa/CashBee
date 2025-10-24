from data import Family, Transaction, Wallet
from enums import PaymentType
from person import User

class WalletMapper:
    """Handling wallet data when reading/writing in DB"""
    @staticmethod
    def to_dict(wallet: Wallet):
        return (
            wallet.balance,
            wallet.max_transaction_limit,
            wallet.transaction_limit,
        )

    @staticmethod
    def from_dict(data: tuple):
        wallet = Wallet(
               wid=data.get("wallet_id"),
            balance=data.get("balance"),
            max_limit=data.get("max_limit"),
            transaction_limit=data.get("transaction_limit"),           
        )
 
        return wallet

class TransactionMapper:
    """Handling transaction data when reading/writing in DB"""
    @staticmethod
    def to_dict(tx: Transaction):
        return ( 
            tx.from_wid,
            tx.to_wid,
            tx.amount,
            tx.Transaction_type.value,
            tx.date,
            )
        

    @staticmethod
    def from_dict(data: tuple):
        return Transaction(
           transaction_id=data.get("transaction_id"),
            from_wallet=data.get("from_wallet"),
            to_wallet=data.get("to_wallet"),
            amount=data.get("amount"),
            tx_type=PaymentType(data.get("type_")),
            dt=data.get("date_")
        )

class UserMapper:
    """Handling user data when reading and writing in DB"""
    @staticmethod
    def to_dict(user: User):
        return (
                user.phone_number,   
                user.national_id,    
                user.name,           
                user.password,       
                user.role.value,     
                user._family_id,     
                user._walletid,       

        )

    @staticmethod
    def from_dict(data):
        user = User(
            uid=data.get("national_id"),
            name=data.get("name_"),
            phone=data.get("phone_number"),
            password=data.get("password_"),
            fa=data.get("failed_attempts"),
            lu=data.get("lock_time"),
            fm=data.get("family_id"),
            wid=data.get("wallet_id"),
            role=data.get("role_")
        )
        return user

class FamilyMapper:
    """Handling family wallet data when reading/writing in DB"""
    @staticmethod
    def to_dict(fw: Family) -> tuple:

        """
        Convert FamilyWallet object to dictionary for storage
        """
        return (
            fw.name,
        )

    @staticmethod
    def from_dict(data: tuple) -> Family:
        """
        Convert dictionary to FamilyWallet object
        """
        if not data:
            return None
        return Family(
             fid=data.get("family_id"),
            name=data.get("family_name")
        )    

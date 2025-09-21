
from datetime import datetime, timedelta
from Validations import AgeCalculation, ValidationCheck
from data import Wallet
from enums import Role
from mappers import *
from person import User, UserSession
from postgres import QueryHandling


class RegistrationFacade:

    def __init__(self,db):
        self.db = db          
    def register_user(self, user: User):
        # Check if user already exists
        existing_user = QueryHandling.retrieve_data("User_",UserMapper,"","national_id = %s", (user.national_id,))
        if existing_user:
            return "❌ National ID already exists, Go to login"
        
        # Validate using Strategy Pattern
        vc = ValidationCheck(phone=user.phone_number,national_id=user.national_id,name=user.name,password=user.password)
        msg = vc.check()
        if msg:
            return msg
        
        wallet = Wallet(balance=0)
        # adding data into the database
        cols = ["balance",'transaction_limit','max_limit']
        wallet.wallet_id = QueryHandling.add_data("Wallet",cols,wallet,WalletMapper,"wallet_id")
    
        user.wallet = wallet.wallet_id
        cols = ["phone_number",'national_id','name_','password_','role_','family_id','wallet_id']
        user_add = QueryHandling.add_data("User_",cols,user,UserMapper)   
        return "✅ Account has been created successfully"
        
    def login_user(self, phone, password):
        user = QueryHandling.retrieve_data('User_',UserMapper,'','phone_number = %s',(phone,))      
        if not user:
            return "❌ User does not exist, Sign Up first"
        
                # Check if account is locked
        if user._lock_until and datetime.now() < user._lock_until:
            remaining = (user._lock_until - datetime.now()).seconds // 60
            return f"⛔ Account locked. Try again after {remaining} minutes"
        
        # Check password
        if user.password != password:
            user.failed_attempts += 1
            if user.failed_attempts == 3:
                user._lock_until = datetime.now() + timedelta(minutes=30)
                user.failed_attempts = 0
                # Update user in database
                msg = "⛔ Too many failed attempts. Account locked for 30 minutes"
            else:
                remaining = 3 - user.failed_attempts
                msg = f"❌ Invalid password. You have {remaining} attempt(s) left"

            col = ["failed_attempts", "lock_time" ]
            data = (user.failed_attempts, user._lock_until, phone)
            QueryHandling.update_data('User_',col,'phone_number = %s',data)  
            return msg
        # Successful login
        user.failed_attempts = 0
        user._lock_until = None
        # Update user in database
        col = ["failed_attempts", "lock_time" ]
        data = (user.failed_attempts, user._lock_until, phone)
        QueryHandling.update_data('User_',col,'phone_number = %s',data)  

        UserSession.set_user(user)
        return f"✅ Login successful!"

class RoleManager:
   
    @staticmethod
    def can_change_to_parent(user: User) -> tuple[bool, str]:
        """Check if user can change role to parent based on age"""
        if user.role == Role.PARENT:
            return False, "Already a parent"       
        try:
            age = AgeCalculation.calculate_age_from_nid(user.national_id)
        except:
            return False,"Invalid National ID"
        # written as calculations can give as age <= 0
        if age is None or age <= 0:
            return False, "Invalid National ID"           
    
        if age < 22:
            return False, f"Must be at least 22 years old to become a parent. Current age: {age}"
            
        return True, f" {age} - Eligible to become a parent"

    @staticmethod
    def change_user_role(user: User, new_role: Role, db) -> str:
        """Change user role with validation"""
        if new_role == Role.PARENT:
            can_change, message = RoleManager.can_change_to_parent(user)
            if not can_change:
                return f"❌ Cannot change to parent: {message}"
        
        # Update user role
        user._role = new_role
        
        update_query = """
            UPDATE User_
            SET role_ = %s
            WHERE phone_number = %s
            """
        db.execute(update_query, values =(new_role.value, user.phone_number))
        return f"✅ Role changed to {new_role.value} successfully"

class UserHandling:
    @staticmethod
    def get_user_info(id,db):
        query_user = "SELECT * FROM User_ WHERE national_id = %s"
        user:User = db.execute(query_user, UserMapper, (id,))  # هيرجع list of tuples
        if not user:
            raise ValueError("User not found")
        
        query_wallet = "SELECT * FROM Wallet WHERE wallet_id = %s"
        wallet:Wallet =  db.execute(query_wallet, WalletMapper, (user.wallet,))

        res = f"Name: {user.name}\n"
        res += f"Role: {user.role}\n"
        res += f"Phone number: {user.phone_number}\n"
        res += f"Balance: {wallet.balance}\n"
        res += f"Money spent: {wallet.money}\n"
        res += f"Transaction Limit: {wallet.transaction_limit}\n"
        res += f"Max transaction Limit: {wallet.max_transaction_limit}\n"
        return res
    @staticmethod
    def get_user_transactions(user):
        """
        Fetch all transactions for a given user
        """
        transactions = QueryHandling.retrieve_data('Transactions',TransactionMapper,'','from_wallet = %s OR to_wallet = %s',(user.wallet,user.wallet))
        res = f"\nTransaction History for {user.name}:\n"
        res += ("=" * 60)
        res += "\n"
        if transactions:
            for tx in transactions:
                    res += tx.show_details()
        else:
            res += "No transactions found\n"
            res += ("=" * 60)     

        return res

class FamilyWalletFacade:

    def __init__(self, family_wallet: Family,db_handler,p):
        self.family_wallet = family_wallet
        self.db = db_handler
        self.parent:User = p._current_user
    
    def create_child_account(self, child_phone, child_national_id, child_name, child_password,maxlimit):
        """Create child account 
        with child-specific validation"""
        # Validate parent role
        if  self.parent.role != Role.PARENT:
            return "❌ Only parents can create child accounts"
        
        # Check if child already exists
        query_user = "SELECT * FROM User_ WHERE national_id = %s"
        user:User = self.db.execute(query_user, UserMapper, (child_national_id,))  # هيرجع list of tuples        
        if user:
            return "❌ Child account already exists"
        
        # Check validations
        vc = ValidationCheck(phone=child_phone,national_id=child_national_id,name=child_name,password=child_password,child=True)
        msg = vc.check()
        if msg:
            return msg
        
        # Create wallet for child
        child_wallet = Wallet(self.db)
        child_wallet.max_transaction_limit = maxlimit

       # INSERT wallet without wallet_id (generated automatically)
        query_wallet = "INSERT INTO wallets (balance, max_limit) VALUES (%s,%s)"
        self.db.execute(query_wallet, values=(child_wallet.balance,child_wallet.max_transaction_limit))
        
        # Get generated wallet_id
        self.cursor.execute("SELECT LASTVAL()")
        child_wallet.wallet_id = self.cursor.fetchone()[0]
        
        # 2️⃣ Create child user and link wallet
        child_user = User(phone=child_phone,
                        uid=child_national_id, 
                        name=child_name,
                        password=child_password,
                        role=Role.CHILD.value, 
                        family_id=self.parent.family_id,
                        wallet=child_wallet.wallet_id)
        
        # INSERT user
        query_user = """
        INSERT INTO users (phone_number, national_id, name_, password_, role_, family_id, wallet_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values_user = (
            child_user.phone_number,
            child_user.national_id,
            child_user.name,
            child_user.password,
            child_user.role,
            child_user.family_id,
            child_user.wallet
        )
        self.db.execute(query_user, values=values_user)
        return f"✅ Child account created successfully for {child_name}"
    
    def get_member_info(self, id):
        if id not in self.family_wallet.members:
            print(self.family_wallet.members)
            return "❌ Member not found"
        return UserHandling.get_user_info(id,self.db)
    def set_max_limit(self, child_id, new_limit, fid):
        query_user = "SELECT * FROM users WHERE national_id = %s and family_id = %s"
        row_user = self.db.execute(query_user, values=(child_id,fid))
        if not row_user:
            return "❌ User not found"

        user_dict = dict(zip([desc[0] for desc in self.db.cursor.description], row_user))
        user: User = UserMapper.from_dict(user_dict)

        query_wallet = "SELECT * FROM wallets WHERE wallet_id = %s"
        row_wallet = self.db.execute(query_wallet, values=(user.wallet,))
        if not row_wallet:
            return "❌ Wallet not found"
        
        wallet_dict = dict(zip([desc[0] for desc in self.db.cursor.description], row_wallet))
        wallet: Wallet = WalletMapper.from_dict(wallet_dict)
     
      
        wallet.max_transaction_limit = new_limit

        query_update = "UPDATE wallets SET max_transaction_limit = %s WHERE wallet_id = %s"
        self.db.execute(query_update, values=(wallet.max_transaction_limit, wallet.wallet_id))

        return "✅ Spending limit updated"
        
    def see_transactions(self,id):
        if id not in self.family_wallet.members:
            return "❌ Member not found"
        
        user:User = self.db.find_one("users", 
                                        lambda u: u.get("national_id") == id, 
                                            UserMapper)  
        res = UserHandling.get_user_transactions(user)   
         
        return res                  
    def see_all_children_history(self):
        if not self.family_wallet.members:
            return "❌ Your family members are empty"
            
            
        res = "\n=== Family Members Transaction History ===\n"
        for child_id in self.family_wallet.members:
            res += self.see_transactions(child_id)
        return res
    def get_family_details(self):
        result = "Family members \n"
        result += UserHandling.get_user_info(self.parent.national_id,self.db)
        result += self.get_children_details()
        return result
    def get_children_details(self):
        """List all children in the family with their basic info"""
        if not self.family_wallet.members:
            return "❌ No children found"
        result = "----Family children----\n"
        for child_id in self.family_wallet.members:
            result += UserHandling.get_user_info(child_id,self.db)
        return result

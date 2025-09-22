
from datetime import datetime, timedelta
from Validations import AgeCalculation, ValidationCheck
from data import Wallet
from enums import Role
from mappers import *
from pay import WalletRepresentation
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
        new_role = new_role.value
        if new_role == user.role:
            return " You Already have this role !!!"
        if new_role == Role.PARENT:
            can_change, message = RoleManager.can_change_to_parent(user)
            if not can_change:
                return f"❌ Cannot change to parent: {message}"
        # Update user role
        user._role = new_role
        QueryHandling.update_data('User_',['role_'],'phone_number = %s',(new_role, user.phone_number))
        return f"✅ Role changed to {new_role} successfully"

class UserHandling:
    @staticmethod
    def get_user_info(user):
        if not user:
            return "❌ User not found"
        res = f"***************User***************"     
        res += f"Name: {user.name}\n"
        res += f"Role: {user.role}\n"
        res += f"Phone number: {user.phone_number}\n"
        res += WalletRepresentation.display(user.wallet)
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

class FamilyFacade:

    def __init__(self,p):
        self.family = None
        self.user:User = p._current_user
        self.family_members = []
    
    def create_family(self,fname):
            self.family = Family(fname)
            cols = ["family_name"]
            self.family.family_id = QueryHandling.add_data("Family_",cols,self.family,FamilyMapper,"family_id")
            print(f'{self.family.family_id}::: {type(self.family.family_id)}')

            # Update user record with family wallet ID
            self.user.family_id = self.family.family_id
            col = ["family_id"]
            data = (self.user.family_id, self.user.phone_number)
            QueryHandling.update_data('User_',col,'phone_number = %s',data)  

            return "Family wallet created successfully!"

    def create_child_account(self, user:User,maxlimit):
        """Create child account 
        with child-specific validation"""

        # Check if child already exists
        user1 = QueryHandling.retrieve_data("User_",UserMapper,"","national_id = %s", (user.national_id,))      
        if user1:
            return "❌ Child account already exists"
        
        # Check validations
        vc = ValidationCheck(phone=user.phone_number,national_id=user.national_id,name=user.name,password=user.password,child=True)
        msg = vc.check()
        if msg:
            return msg
        
        wallet = Wallet(balance=0,max_limit=maxlimit)
        # adding data into the database
        cols = ["balance",'transaction_limit','max_limit']
        wallet.wallet_id = QueryHandling.add_data("Wallet",cols,wallet,WalletMapper,"wallet_id")
    
        user.wallet = wallet.wallet_id
        user.family_id = self.user.family_id
        cols = ["phone_number",'national_id','name_','password_','role_','family_id','wallet_id']
        user_add = QueryHandling.add_data("User_",cols,user,UserMapper)
        self.family_members.append(user.phone_number)   
        return f"✅ Child account created successfully for {user.name}"
    
    def get_member_info(self, phone):
        user:User = QueryHandling.retrieve_data("User_",UserMapper,"","phone_number = %s and family_id = %s", (phone,self.user.family_id))       
        return UserHandling.get_user_info(user)
    
    def set_max_limit(self, phone_number, new_limit):
        user:User = QueryHandling.retrieve_data("User_",UserMapper,"","phone_number = %s and family_id = %s", (phone_number,self.user.family_id))       
        if not user:
            return "❌ User not found"

        col = ["max_limit" ]
        data = (new_limit, user.wallet)
        QueryHandling.update_data('Wallet',col,'wallet_id = %s',data)  
        
        return "✅ Spending limit updated"




    def see_transactions(self,phone):

        user:User = QueryHandling.retrieve_data("User_",UserMapper,"","phone_number = %s and family_id = %s", (phone,self.user.family_id)) 

        if not user:
            return "❌ Member not found"
    
        res = UserHandling.get_user_transactions(user)   
         
        return res                  
    def see_all_children_history(self):      
        users = QueryHandling.retrieve_data("User_",UserMapper,"","family_id = %s", (self.user.family_id,)) 
        if not users:
            return "❌ Your family members are empty"    
            
        res = "\n=== Family Members Transaction History ===\n"
        for child_phone in users:
            res += self.see_transactions(child_phone.phone_number)
        return res
    def get_family_details(self):
        result = "Family members \n"
        result += UserHandling.get_user_info(self.user)
        result += self.get_children_details()
        return result
    def get_children_details(self):
        """List all children in the family with their basic info"""
        users = QueryHandling.retrieve_data("User_",UserMapper,"","family_id = %s", (self.user.family_id,)) 
        if not users:
            return "❌ Your family members are empty"  
        result = "----Family children----\n"
        for child in users:
            result += UserHandling.get_user_info(child)
        return result

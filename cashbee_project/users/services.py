from django.db import IntegrityError
from .models import User,Family,UsersRole
from .validations import ValidationCheck  
from django.utils.timezone import now
from datetime import timedelta

class RegistrationFacade:

    def register_user(self, user_data: dict):
        """
        user_data dict expected keys: 
        name, phone_number, national_id, password
        """
        # check if user already exists
        if User.objects.filter(national_id=user_data["national_id"]).exists():
            return "❌ National ID already exists, Go to login"

        try:
            user = User.objects.create(
                name=user_data["name"],
                phone_number=user_data["phone_number"],
                national_id=user_data["national_id"],
                role=UsersRole.USER,
                failed_attempts=0,
                password = user_data["password"]

            )
            user.full_clean()
            user.save()
        except IntegrityError:
            return "❌ Phone number or National ID already in use"

        return "✅ Account has been created successfully"
    def login_user(self, phone, password):
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return "❌ User does not exist, Sign Up first"
        # check lock time
        if user.lock_time and now() < user.lock_time:
            remaining = (user.lock_time - now()).seconds // 60
            return f"⛔ Account locked. Try again after {remaining} minutes"

        # check password
        if not user.check_password(password):   
            user.failed_attempts += 1
            if user.failed_attempts >= 3:
                user.lock_time = now() + timedelta(minutes=30)
                user.failed_attempts = 0
                msg = "⛔ Too many failed attempts. Account locked for 30 minutes"
            else:
                remaining = 3 - user.failed_attempts
                msg = f"❌ Invalid password. You have {remaining} attempt(s) left"
            user.save()
            return msg

        # successful login
        user.failed_attempts = 0
        user.lock_time = None
        user.save()

        return f"✅ Login successful!"
class RoleManager:

    @staticmethod
    def can_change_to_parent(user: User) -> tuple[bool, str]:
        from Validations import AgeCalculation
        try:
            age = AgeCalculation.calculate_age_from_nid(user.national_id)
        except:
            return False, "Invalid National ID"
        
        if not age or age <= 0:
            return False, "Invalid National ID"

        if age < 22:
            return False, f"Must be at least 22 years old to become a parent. Current age: {age}"

        return True, f"{age} - Eligible to become a parent"

    @staticmethod
    def change_user_role(user: User, new_role: str) -> str:
        if new_role == user.role:
            return "You already have this role!"

        if new_role == UsersRole.PARENT:
            can_change, message = RoleManager.can_change_to_parent(user)
            if not can_change:
                return f"❌ Cannot change to parent: {message}"

        user.role = new_role
        user.save()
        return f"✅ Role changed to {new_role} successfully"
class FamilyFacade:

    def __init__(self, user: User):
        self.user = user
        self.family = user.family

    def create_family(self, fname):
        family = Family.objects.create(name=fname)
        self.user.family = family
        self.user.save()
        return "Family wallet created successfully!"
    
    def create_child_account(self, child_data: dict):
        if User.objects.filter(national_id=child_data["national_id"]).exists():
            return "❌ Child account already exists"

        child = User.objects.create(
            name=child_data["name"],
            phone_number=child_data["phone_number"],
            national_id=child_data["national_id"],
            role= UsersRole.CHILD,
            family=self.family,
            password = child_data["password"]

        )
        child.full_clean()        
        child.save()

        return f"✅ Child account created successfully for {child.name}"
    def get_family_details(self):
        members = User.objects.filter(family=self.user.family)
        result = f"Family: {self.user.family.name}\n"
        for member in members:
            result += f"- {member.name} ({member.role})\n"
        return result

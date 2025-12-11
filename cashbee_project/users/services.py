from django.db import IntegrityError
from .models import User, Family, UsersRole
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from .validations import AgeCalculation

class RoleManager:

    @staticmethod
    def can_change_to_parent(user: User) -> tuple[bool, str]:
        if not user.national_id:
            return False, "National ID is required to become a parent"
        
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
    def change_user_role(user: User, new_role: str) -> tuple[bool, str]:
        if new_role == user.role:
            return False, "You already have this role"

        if new_role == UsersRole.PARENT:
            can_change, message = RoleManager.can_change_to_parent(user)
            if not can_change:
                return False, f"Cannot change to parent: {message}"

        user.role = new_role
        user.save(skip_validation=True)
        return True, f"✅ Role changed to {new_role} successfully"


class FamilyFacade:

    def __init__(self, user: User):
        self.user = user
        self.family = user.family

    def create_family(self, fname):
        family = Family.objects.create(name=fname)
        self.user.family = family
        self.user.save(skip_validation=True)
        return "Family created successfully!"
    
    def create_child_account(self, child_data: dict):
        phone = child_data.get("phone_number")
        national_id = child_data.get("national_id")
        
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("Phone number already registered")
        
        if national_id and User.objects.filter(national_id=national_id).exists():
            raise ValidationError("❌ Child account with this National ID already exists")

        # Create user with hashed password
        child = User.objects.create_user(
            username=None,  # Will be auto-generated
            first_name=child_data.get("first_name"),
            last_name=child_data.get("last_name"),
            phone_number=phone,
            national_id=national_id,
            email=child_data.get("email", ""),
            password=child_data.get("password"),
            role=UsersRole.CHILD,
            family=self.family
        )
        
        return child
    
    def get_family_details(self):
        """Get formatted family details"""
        if not self.family:
            return "User is not part of any family"
        
        members = User.objects.filter(family=self.family)
        result = f"Family: {self.family.name}\n"
        result += f"Total Members: {members.count()}\n\n"
        
        # List parents
        parents = members.filter(role=UsersRole.PARENT)
        if parents.exists():
            result += "Parents:\n"
            for parent in parents:
                result += f"  - {parent.name} ({parent.phone_number})\n"
        
        # List children
        children = members.filter(role=UsersRole.CHILD)
        if children.exists():
            result += "\nChildren:\n"
            for child in children:
                result += f"  - {child.name} ({child.phone_number})\n"
        
        return result
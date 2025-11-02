from abc import ABC, abstractmethod
from datetime import date
from enum import Enum
import re
from phonenumbers import NumberParseException
import phonenumbers

class ValidationStrategy(ABC):

    @abstractmethod
    def is_valid(self, value) -> bool:
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        pass

class AgeCalculation:
    @staticmethod
    def calculate_age_from_nid(nid):
        if len(nid) != 14 or not nid.isdigit():
            raise ValueError("Invalid national id")
        century_digit = int(nid[0])
        if century_digit not in [2, 3]:
            raise ValueError("Invalid national id")

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
            raise ValueError("Invalid National ID")
            
        today = date.today()
        age = today.year - year
        if (today.month, today.day) < (month, day):
            age -= 1
        return age

class NationalIDValidationStrategy(ValidationStrategy):
    def is_valid(self, nid) -> bool:
        try:
            age = AgeCalculation.calculate_age_from_nid(nid)
        except:
            return False
        return age >= 18

    def get_error_message(self) -> str:
        return "Invalid National ID or under 18 years old"

class ChildNationalIDValidationStrategy(ValidationStrategy):

    def is_valid(self, nid) -> bool:
        try:
            age = AgeCalculation.calculate_age_from_nid(nid)
        except Exception as e:
            print(e)
            return False   
        print(age) 
        return 8 <= age < 18  

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
        if len(password) < 10:
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

class ValidatorContext:

    def __init__(self, strategy: ValidationStrategy):
        self._strategy = strategy
        
    def set_strategy(self, strategy: ValidationStrategy):
        self._strategy = strategy
        
    def validate(self, value) -> bool:
        return self._strategy.is_valid(value)
        
    def get_error(self) -> str:
        return self._strategy.get_error_message()

class ValidationCheck:

    def __init__(self,name,phone,password,national_id,child = False):
        if child:
            x = ValidationsNames.NATIONALIDCHILD.value
        else:
            x = ValidationsNames.NATIONALIDUSER.value
        self.validation_checks = [
            (name, ValidationsNames.NAME.value),
            (phone, ValidationsNames.PHONE.value),
            (password, ValidationsNames.PASSWORD.value),
            (national_id, x)
        ]
    def check(self):  
        for value, validator in self.validation_checks:
            if not validator.validate(value):
                return f"❌ {validator.get_error()}"
            
class RegexPattern(Enum):
    """
        Regular expressions are used when handling password and user name
    """
    LOWERCASE_ENGLISH = r"[a-z]"
    UPPERCASE_ENGLISH = r"[A-Z]"
    NUMBERS = r"[0-9]+"
    SPECIAL_CHARACTERS = r"[!@#$%^&*(),.?\":{}|<>]"
class ValidationsNames(Enum):
    """ 
        Used when handling data entered by the user (used in signup and login)
    """
    NAME = ValidatorContext(EnglishNameValidationStrategy())
    PHONE = ValidatorContext(PhoneValidationStrategy())
    PASSWORD = ValidatorContext(PasswordValidationStrategy())
    NATIONALIDUSER = ValidatorContext(NationalIDValidationStrategy())
    NATIONALIDCHILD = ValidatorContext(ChildNationalIDValidationStrategy())

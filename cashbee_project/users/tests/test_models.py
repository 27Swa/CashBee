from django.test import TestCase
from ..models import UsersRole
from django.core.exceptions import ValidationError
from users.models import User,Family
class FamilyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.family = Family(name = "Mansour")
    
    def test_string_family(self):
        self.assertEqual(str(self.family), "Mansour")

    def test_empty_family(self):
        self.assertEqual(self.family.name, "Mansour")
        self.family.name = ""
        with self.assertRaises(ValidationError):
            self.family.full_clean()
            
class UserTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(phone_number = "01009710555",
                         national_id = "30206280101092",
                         first_name = "Sondos", last_name = "Wael",
                         password = "So@1234567")
    
    def test_check_user_family(self):
        self.assertIsNone(self.user.family)    
        self.user.family = Family(name ="Mansour")
        self.assertEqual(self.user.family.name, "Mansour")
    
    def test_user_phone_number(self):
        self.user.phone_number="123" 
        with self.assertRaises(Exception):
            self.user.clean()

    def test_user_national_id(self):
        self.user.national_id="111"
        with self.assertRaises(Exception):
            self.user.clean()
    
    def test_user_has_wallet(self):
        self.assertIsNotNone(self.user.wallet)
    
    def test_admin(self):
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.user.is_staff = True
        self.user.is_superuser = True     
        self.assertTrue(self.user.is_staff)
        self.assertTrue(self.user.is_superuser)

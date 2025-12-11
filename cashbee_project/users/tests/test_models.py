from django.test import TestCase
from users.models import UsersRole, User, Family
from django.core.exceptions import ValidationError


class FamilyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.family = Family.objects.create(name="Mansour")
    
    def test_string_family(self):
        self.assertEqual(str(self.family), "Mansour")

    def test_family_name_exists(self):
        self.assertEqual(self.family.name, "Mansour")
    
    def test_empty_family_name(self):
        family = Family(name="")
        with self.assertRaises(ValidationError):
            family.full_clean()
    
    def test_short_family_name(self):
        family = Family(name="Ab")
        with self.assertRaises(ValidationError):
            family.full_clean()
            
            
class UserTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            phone_number="+201009710555",
            national_id="30206280101092",
            first_name="Sondos",
            last_name="Wael",
            password="So@1234567"
        )
    
    def test_check_user_family(self):
        self.assertIsNone(self.user.family)    
        family = Family.objects.create(name="Mansour")
        self.user.family = family
        self.user.save(skip_validation=True)
        self.assertEqual(self.user.family.name, "Mansour")
    
    def test_user_has_username(self):
        """Test that username is auto-generated"""
        self.assertIsNotNone(self.user.username)
        self.assertTrue(len(self.user.username) > 0)
    
    def test_user_name_property(self):
        """Test the name property returns full name"""
        self.assertEqual(self.user.name, "Sondos Wael")
    
    def test_user_invalid_national_id(self):
        user = User(
            phone_number="+201009710556",
            national_id="111",
            first_name="Test",
            last_name="User"
        )
        with self.assertRaises(ValidationError):
            user.full_clean()
    
    def test_user_has_wallet(self):
        """Test that wallet is created via signal"""
        # Refresh from DB to get wallet
        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, 'wallet'))
    
    def test_user_default_role(self):
        """Test default role is USER"""
        self.assertEqual(self.user.role, UsersRole.USER)
    
    def test_admin_permissions(self):
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save(skip_validation=True)
        self.assertTrue(self.user.is_staff)
        self.assertTrue(self.user.is_superuser)
    
    def test_date_of_birth_from_national_id(self):
        """Test that date_of_birth is extracted from national_id"""
        self.user.full_clean()
        self.assertIsNotNone(self.user.date_of_birth)
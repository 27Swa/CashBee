from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, Family, UsersRole


class UserProfileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            phone_number="+201000000001",
            national_id="30305270989876",
            first_name="Sondos",
            last_name="Ali",
            password="So@1234567"
        )
    
    def setUp(self):
        self.client = APIClient()

    def test_authenticated_user_can_access_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/users/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["phone_number"]), str(self.user.phone_number))

    def test_unauthenticated_user_cannot_access_profile(self):
        response = self.client.get("/api/users/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserFamilyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.family = Family.objects.create(name="Mansour")

        cls.user_with_family = User.objects.create_user(
            phone_number="+201000000002",
            national_id="31305270989877",
            first_name="Nada",
            last_name="Hassan",
            password="Na@1234567",
            role=UsersRole.CHILD
        )
        cls.user_with_family.family = cls.family
        cls.user_with_family.save(skip_validation=True)

        cls.user_without_family = User.objects.create_user(
            phone_number="+201000000003",
            national_id="31305270989878",
            first_name="Sara",
            last_name="Mansour",
            password="Sa@1234567",
            role=UsersRole.CHILD
        )

        cls.family_member = User.objects.create_user(
            phone_number="+201000000004",
            national_id="30305270989879",
            first_name="Ali",
            last_name="Mansour",
            password="Al@1234567",
            role=UsersRole.PARENT
        )
        cls.family_member.family = cls.family
        cls.family_member.save(skip_validation=True)
    
    def setUp(self):
        self.client = APIClient()

    def test_user_with_family_sees_family_members(self):
        self.client.force_authenticate(user=self.user_with_family)
        response = self.client.get("/api/users/family/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_user_without_family_gets_message(self):
        self.client.force_authenticate(user=self.user_without_family)
        response = self.client.get("/api/users/family/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "This user is not linked to a family.")

    def test_unauthenticated_user_cannot_access_family(self):
        response = self.client.get("/api/users/family/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {
            "phone_number": "+201000000001",
            "national_id": "30305270989876",
            "first_name": "Sondos",
            "last_name": "Ali",
            "password": "So@1234567"
        }
        cls.user = User.objects.create_user(**cls.user_data)

    def setUp(self):
        self.client = APIClient()
        self.signup_url = "/api/signup/"
        self.login_url = "/api/login/"

    def test_signup_success(self):
        new_user_data = {
            "phone_number": "+201000000002",
            "first_name": "Nada",
            "last_name": "Hassan",
            "password": "Na@1234567",
            "date_of_birth": "2000-05-15"
        }
        response = self.client.post(self.signup_url, new_user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)

    def test_signup_missing_required_fields(self):
        """Test that signup fails when required fields are missing"""
        incomplete_data = {
            "phone_number": "+201000000003",
            "password": "Missing@123"
            # Missing first_name and last_name which are required
        }
        response = self.client.post(self.signup_url, incomplete_data, format="json")
        # Should fail because first_name and last_name are required in the serializer
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("first_name", response.data or str(response.content))

    def test_signup_duplicate_phone(self):
        duplicate_data = {
            "phone_number": self.user_data["phone_number"],
            "first_name": "Test",
            "last_name": "User",
            "password": "Test@12345"
        }
        response = self.client.post(self.signup_url, duplicate_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        login_data = {
            "phone_number": str(self.user_data["phone_number"]),
            "password": self.user_data["password"]
        }
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)

    def test_login_wrong_password(self):
        login_data = {
            "phone_number": str(self.user_data["phone_number"]),
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", str(response.data))

    def test_login_user_not_found(self):
        login_data = {
            "phone_number": "+201000009999",
            "password": "NoUser@123"
        }
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", str(response.data))
    
    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save(skip_validation=True)

        login_data = {
            "phone_number": str(self.user.phone_number),
            "password": self.user_data["password"]
        }
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Account isn't active", str(response.data))
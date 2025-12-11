from .models import User, UsersRole
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .validations import *  

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone_number',
            'password',
            'email',
            'date_of_birth',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True},  # Explicitly required
            'last_name': {'required': True},   # Explicitly required
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'date_of_birth': {'required': False, 'allow_null': True}
        }

    def validate_phone_number(self, value):
        # Check if phone number already exists
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already registered")
        
        validator = PhoneValidationStrategy()
        if not validator.is_valid(str(value)):
            raise serializers.ValidationError(validator.get_error_message())
        return value
    
    def validate_password(self, value):
        validator = PasswordValidationStrategy()
        if not validator.is_valid(value):
            raise serializers.ValidationError(validator.get_error_message())
        return value
    
    def validate_date_of_birth(self, value):
        if value:
            age = AgeCalculation.calculate_age_from_dob(value)
            if age < 18:
                raise serializers.ValidationError("⛔ Must be at least 18 years old")
        return value
    
    def create(self, validated_data):
        # Use create_user to properly hash password
        user = User.objects.create_user(
            username=None,  # Will be auto-generated
            password=validated_data.pop('password'),
            **validated_data
        )
        return user
       
class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, data):
        """Validate login credentials"""
        phone = data.get("phone_number")
        password = data.get("password")

        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "❌ Phone number not found"})

        if not user.check_password(password):
            raise serializers.ValidationError({"error": "❌ Incorrect password"})
    
        if not user.is_active:
            raise serializers.ValidationError({"error": "❌ Account isn't active"})

        token, _ = Token.objects.get_or_create(user=user)
        data["token"] = token.key
        data["user"] = user
        return data
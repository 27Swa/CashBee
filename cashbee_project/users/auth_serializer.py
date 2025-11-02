from .models import User,UsersRole
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .validations import *  

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'national_id',
            'first_name',
            'last_name',
            'phone_number',
            'password',
            'role',
            'email'
        ]

     # ✅ ADDED: Phone number validation   
    def validate_phone_number(self, value):
        validator = PhoneValidationStrategy()
        if not validator.is_valid(value):
            raise serializers.ValidationError(validator.get_error_message())
        return value
    
    # ✅ ADDED: Password validation
    def validate_password(self, value):
        validator = PasswordValidationStrategy()
        if not validator.is_valid(value):
            raise serializers.ValidationError(validator.get_error_message())
        return value
    
    # ✅ ADDED: National ID validation
    def validate_national_id(self, value):
        validator = NationalIDValidationStrategy()
        if not validator.is_valid(value):
            raise serializers.ValidationError(validator.get_error_message())
        return value
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
       
    def validate(self, data):
        if data.get('role') == UsersRole.CHILD:
            raise serializers.ValidationError({
                "error": "❌ Children cannot self-register. Must be created by parent."
            })
        
        """Make sure that this user isn't exist in the DB before"""
        if User.objects.filter(national_id=data['national_id']).exists():
            raise serializers.ValidationError({"error":"❌ National ID already exists"})
        if User.objects.filter(phone_number=data['phone_number']).exists():
            raise serializers.ValidationError({"error":"❌ Phone number already registered"})
        return data
    
class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, data):
        phone = data.get("phone_number")
        password = data.get("password")

        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error":"❌ Phone number not found"})

        if not user.check_password(password):
            raise serializers.ValidationError({"error":"❌ Incorrect password"})
    
        if not user.is_active:
            raise serializers.ValidationError({"error":"❌ Account isn't active"})

        token, _ = Token.objects.get_or_create(user=user)
        data["token"]   = token.key
        data["user_id"] = user.national_id
        data["role"]    = user.role
        data["name"]    = user.name
        data["user"]    = user
        data["wallet_id"] = user.wallet.id 
        return data

from rest_framework import serializers
from .models import User,UsersRole,Family
from .services import RoleManager,FamilyFacade
class UserSerializer(serializers.ModelSerializer):
    wallet_id = serializers.IntegerField(source='wallet.id', read_only=True)  
    wallet_balance = serializers.DecimalField(  
        source='wallet.balance', 
        read_only=True, 
        max_digits=15, 
        decimal_places=2
    )
    class Meta:
        model = User
        fields = ['name', 'phone_number','national_id', 'role',
                'family','email', 'wallet_id', 'wallet_balance']

class ChildSerializer(serializers.ModelSerializer):
    """
    Single serializer for creating and viewing child accounts.
    Password is write-only, wallet info is read-only.
    """
    wallet_id = serializers.IntegerField(source='wallet.id', read_only=True)
    wallet_balance = serializers.DecimalField(
        source='wallet.balance',
        read_only=True,
        max_digits=15,
        decimal_places=2
    )
    family_name = serializers.CharField(source='family.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'national_id',
            'name',
            'first_name',
            'last_name',
            'phone_number',
            'password',
            'email',
            'role',
            'family',
            'family_name',
            'wallet_id',
            'wallet_balance',
            'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True},
            'family': {'read_only': True},
            'name': {'read_only': True},
            'wallet_id': {'read_only': True},
            'wallet_balance': {'read_only': True},
            'family_name': {'read_only': True}
        }
  
    def validate(self, data):
        """Additional validations"""
        # Only check uniqueness on create
        if not self.instance:
            # Check if national ID already exists
            if User.objects.filter(national_id=data['national_id']).exists():
                raise serializers.ValidationError({
                    "national_id": "❌ National ID already exists"
                })
            
            # Check if phone number already exists
            if User.objects.filter(phone_number=data['phone_number']).exists():
                raise serializers.ValidationError({
                    "phone_number": "❌ Phone number already registered"
                })
        else:
            # On update, check phone uniqueness excluding current user
            phone = data.get('phone_number')
            if phone and User.objects.filter(phone_number=phone).exclude(
                national_id=self.instance.national_id
            ).exists():
                raise serializers.ValidationError({
                    "phone_number": "❌ Phone number already registered"
                })
        
        return data

class FamilySerializer(serializers.ModelSerializer):
    """
    Unified serializer for all Family operations:
    - Viewing family details
    - Creating new family
    - Joining existing family
    """
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Family
        fields = ['id', 'name', 'members_count']
        read_only_fields = ['id', 'members_count']
    
    def get_members_count(self, obj):
        """Get number of family members"""
        return User.objects.filter(family=obj).count()
    # used when creating new family
    def validate_family_name(self, value):
        """Validate family name for creation"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Family name must be at least 3 characters"
            )
        
        # Check if family name already exists (only on create)
        if not self.instance and Family.objects.filter(name=value.strip()).exists():
            raise serializers.ValidationError(
                "❌ Family name already exists. Please choose another name."
            )
        
        return value.strip()
      
    def validate(self, data):
        """Validate based on operation type"""
        user = self.context.get('request').user if self.context.get('request') else None
        action = self.context.get('action')  # 'create', 'join', or None (view/update)
        
        if not user or not action:
            return data
        
        # Common validation: check if user already in a family
        if user.family and action in ['create', 'join']:
            raise serializers.ValidationError({
                "error": "❌ You are already in a family. Leave it first to create or join another."
            })
        
        # CREATE FAMILY validations
        if action == 'create':
            if 'name' not in data:
                raise serializers.ValidationError({
                    "name": "Family name is required to create a family"
                })
            
            # Check if user is a child
            if user.role == UsersRole.CHILD:
                raise serializers.ValidationError({
                    "error": "❌ Children cannot create families. Must be upgraded to parent first."
                })
        
        # JOIN FAMILY validations
        elif action == 'join':
            if 'name' not in data:
                raise serializers.ValidationError({
                    "id": "Family name is required to join a family"
                })
        
        return data
    
    def create(self, validated_data):
        """Create family and optionally upgrade user to parent"""
        user = self.context['request'].user
        action = self.context.get('action')
        
        if action == 'create':
            # Extract family name from either source
            family_name = validated_data.get('name')

            # Upgrade user to parent if needed using RoleManager
            if user.role != UsersRole.PARENT:
                try:
                    can_change, message=   RoleManager.change_user_role(user, UsersRole.PARENT)
                except Exception as e:
                    raise serializers.ValidationError({
                        "error": f"❌ Failed to upgrade to parent: {str(e)}"
                    })
            
            # Use FamilyFacade to create the family
            family_facade = FamilyFacade(user)
            result = family_facade.create_family(family_name)
            return user.family
        
        elif action == 'join':
            # Join existing family
            family_name = validated_data.get('name')
            family = Family.objects.get(name=family_name)
            
            user.family = family
            user.save()
            
            return family
        
        return super().create(validated_data)
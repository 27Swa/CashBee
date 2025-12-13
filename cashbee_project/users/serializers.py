from rest_framework import serializers
from .models import User, UsersRole, Family
from .services import RoleManager, FamilyFacade
from .validations import NationalIDValidationStrategy, ChildNationalIDValidationStrategy, ValidatorContext

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with wallet information"""
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
            'id','username', 'is_staff', 'date_joined',
            'is_superuser',   
            'national_id', 'name', 'first_name', 'last_name',
            'phone_number', 'email', 'role', 'family', 'family_name',
            'wallet_id', 'wallet_balance', 'is_active', 'date_of_birth'
        ]
        read_only_fields = ['role', 'family', 'family_name', 'wallet_id', 'wallet_balance','username']


class ChildSerializer(serializers.ModelSerializer):
    """Serializer for Child accounts - creation and viewing"""
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
            'national_id', 'first_name', 'last_name', 'name',
            'phone_number', 'password', 'email',
            'role', 'family', 'family_name','date_of_birth',
            'wallet_id', 'wallet_balance', 'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True},
            'family': {'read_only': True},
            'name': {'read_only': True},
            'family_name': {'read_only': True},
            'wallet_id': {'read_only': True},
            'wallet_balance': {'read_only': True},
            'national_id': {'required': False, 'allow_null': True, 'allow_blank': True},
            'email': {'required': True, 'allow_null': True, 'allow_blank': True},
            'date_of_birth': {'required': False, 'allow_null': True}
        }
    
    def validate_national_id(self, value):
        """Validate child national ID if provided"""
        if not value:  # If not provided, skip validation
            return value

        validator = ValidatorContext(ChildNationalIDValidationStrategy())
        if not validator.validate(value):
            raise serializers.ValidationError(validator.get_error())
        
        return value
    
    def validate_phone_number(self, value):
        """Check phone uniqueness"""
        # On create
        if not self.instance:
            if User.objects.filter(phone_number=value).exists():
                raise serializers.ValidationError("Phone number already registered")
        # On update
        else:
            if User.objects.filter(phone_number=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("Phone number already registered")
        
        return value
    
    def validate(self, data):
        """Validate uniqueness on create"""
        national_id = data.get('national_id')
        if national_id:
            query = User.objects.filter(national_id=national_id)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise serializers.ValidationError({
                    "national_id": "National ID already exists"
                })
        
        return data
class FamilySerializer(serializers.ModelSerializer):
    """Serializer for Family operations: viewing, creating, joining"""
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Family
        fields = ['id', 'name', 'members_count', 'created_at']
        read_only_fields = ['id', 'members_count', 'created_at']
    
    def get_members_count(self, obj):
        """Get number of family members"""
        return obj.get_members_count()
    
    def validate_name(self, value):
        """Validate family name"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Family name must be at least 3 characters"
            )
        
        # Check uniqueness only on create
        if not self.instance and Family.objects.filter(name=value.strip()).exists():
            raise serializers.ValidationError(
                "Family name already exists. Please choose another name."
            )
        
        return value.strip()
      
    def validate(self, data):
        """Validate based on operation type (create/join)"""
        user = self.context.get('request').user if self.context.get('request') else None
        action = self.context.get('action')
        
        if not user or not action:
            return data
        
        # Check if user already in a family
        if user.family and action in ['create', 'join']:
            raise serializers.ValidationError({
                "error": "You are already in a family. Leave it first to create or join another."
            })
        
        # CREATE validations
        if action == 'create':
            if 'name' not in data:
                raise serializers.ValidationError({
                    "name": "Family name is required"
                })
            
            if user.role == UsersRole.CHILD:
                raise serializers.ValidationError({
                    "error": "Children cannot create families"
                })
        
        # JOIN validations
        elif action == 'join':
            if 'name' not in data:
                raise serializers.ValidationError({
                    "name": "Family name is required to join"
                })
            
            # Verify family exists
            if not Family.objects.filter(name=data['name']).exists():
                raise serializers.ValidationError({
                    "name": "Family not found"
                })
        
        return data
    
    def create(self, validated_data):
        """Handle family creation or joining"""
        user = self.context['request'].user
        action = self.context.get('action')
        family_name = validated_data.get('name')
        
        if action == 'create':
            # Upgrade to parent if needed
            if user.role != UsersRole.PARENT:
                success, message = RoleManager.change_user_role(user, UsersRole.PARENT)
                if not success:
                    raise serializers.ValidationError({"error": message})
            
            # Create family using facade
            family_facade = FamilyFacade(user)
            family_facade.create_family(family_name)
            return user.family
        
        elif action == 'join':
            # Join existing family
            family = Family.objects.get(name=family_name)
            user.family = family
            user.save()
            return family
        
        return super().create(validated_data)
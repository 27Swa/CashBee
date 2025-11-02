from django.shortcuts import render
from rest_framework import viewsets
from .models import User,UsersRole
from .serializers import UserSerializer,ChildSerializer,FamilySerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, permissions,generics
from rest_framework import status

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

   
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def family(self, request):
        user = request.user
        if not user.family:
            return Response({"message": "This user is not linked to a family."})
        family_members = User.objects.filter(family=user.family)
        serializer = self.get_serializer(family_members, many=True)
        return Response(serializer.data)

class ChildViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing children accounts.
    Only parents can create and manage children.
    """
    serializer_class = ChildSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return children based on user role:
        - Parents: see their own children
        - Superusers: see all children
        """
        user = self.request.user
        
        if user.is_superuser:
            return User.objects.filter(role=UsersRole.CHILD)
        
        # Only parents can see children
        if user.role == UsersRole.PARENT and user.family:
            return User.objects.filter(
                role=UsersRole.CHILD,
                family=user.family
            )
        
        # Other users see nothing
        return User.objects.none()
    
    def get_serializer_class(self):
        return ChildSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new child account (Parents only)"""
        # Check if user is a parent
        if request.user.role != UsersRole.PARENT:
            return Response(
                {"error": "❌ Only parents can create child accounts"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if parent has a family
        if not request.user.family:
            return Response(
                {"error": "❌ You must be in a family to create child accounts"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        child = serializer.save()
        
        return Response(
            {
                "message": "✅ Child account created successfully",
                "child": ChildDetailSerializer(child).data
            },
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, *args, **kwargs):
        """List all children in family"""
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response({
                "message": "No children found in your family",
                "children": []
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "children": serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get details of a specific child"""
        child = self.get_object()
        serializer = self.get_serializer(child)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update child information (partial update allowed)"""
        child = self.get_object()
        
        # Prevent changing certain fields
        protected_fields = ['national_id', 'role', 'family', 'wallet']
        for field in protected_fields:
            if field in request.data:
                return Response(
                    {"error": f"❌ Cannot modify {field}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(
            child,
            data=request.data,
            partial=kwargs.get('partial', False)
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            "message": "✅ Child account updated successfully",
            "child": serializer.data
        })
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH)"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Deactivate child account (soft delete)"""
        child = self.get_object()
        
        # Don't actually delete, just deactivate
        child.is_active = False
        child.save()
        
        return Response(
            {"message": "✅ Child account deactivated successfully"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='activate')
    def activate_child(self, request, pk=None):
        """Reactivate a deactivated child account"""
        child = self.get_object()
        
        if child.is_active:
            return Response(
                {"message": "Child account is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        child.is_active = True
        child.save()
        
        return Response({
            "message": "✅ Child account activated successfully"
        })
    
    @action(detail=True, methods=['get'], url_path='wallet')
    def child_wallet(self, request, pk=None):
        """Get child's wallet information"""
        child = self.get_object()
        
        if not child.wallet:
            return Response(
                {"error": "Wallet not found for this child"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from wallet.serializers import WalletSerializer
        serializer = WalletSerializer(child.wallet)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='transactions')
    def child_transactions(self, request, pk=None):
        """Get child's transaction history"""
        child = self.get_object()
        
        if not child.wallet:
            return Response(
                {"error": "Wallet not found for this child"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from transactions.models import Transaction
        from transactions.serializers import TransactionSerializer
        
        transactions = Transaction.objects.filter(
            models.Q(from_wallet=child.wallet) | 
            models.Q(to_wallet=child.wallet)
        ).order_by('-date')[:20]
        
        serializer = TransactionSerializer(transactions, many=True)
        return Response({
            "count": transactions.count(),
            "transactions": serializer.data
        })
    
    @action(detail=True, methods=['patch'], url_path='change-password')
    def change_password(self, request, pk=None):
        """Change child's password"""
        child = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {"error": "❌ new_password is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password
        from .validations import PasswordValidationStrategy
        validator = PasswordValidationStrategy()
        if not validator.is_valid(new_password):
            return Response(
                {"error": validator.get_error_message()},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        child.set_password(new_password)
        child.save()
        
        return Response({
            "message": "✅ Password changed successfully"
        })


from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models, transaction
from .models import User, UsersRole, Family
from .serializers import UserSerializer, ChildSerializer, FamilySerializer
from .services import RoleManager, FamilyFacade


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def family(self, request):
        """Get all family members"""
        user = request.user
        if not user.family:
            return Response({
                "message": "This user is not linked to a family."
            })
        family_members = User.objects.filter(family=user.family)
        serializer = self.get_serializer(family_members, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='create-family')
    def create_family(self, request):
        """
        Create a family and upgrade user to PARENT role.
        USER → PARENT + Create Family
        """
        serializer = FamilySerializer(
            data=request.data,
            context={'request': request, 'action': 'create'}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            family = serializer.save()
            
            # Refresh user to get updated info
            request.user.refresh_from_db()
            
            return Response({
                "message": "✅ Family created and role upgraded to PARENT successfully",
                "family": {
                    "id": family.id,
                    "name": family.name
                },
                "user": {
                    "national_id": request.user.national_id,
                    "name": request.user.name,
                    "role": request.user.role,
                    "family_id": family.id
                }
            }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {"error": f"❌ Failed to create family: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='upgrade-to-parent')
    def upgrade_to_parent(self, request):
        """
        Upgrade USER to PARENT without creating family.
        Can join a family later.
        """
        user = request.user
        
        # Check if already a parent
        if user.role == UsersRole.PARENT:
            return Response(
                {"error": "❌ You are already a parent"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is a child
        if user.role == UsersRole.CHILD:
            return Response(
                {"error": "❌ Children cannot upgrade to parent directly"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Use RoleManager to validate and upgrade
        can_change, message = RoleManager.can_change_to_parent(user)
        if not can_change:
            return Response(
                {"error": f"❌ {message}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = RoleManager.change_user_role(user, UsersRole.PARENT)
            user.refresh_from_db()
            
            return Response({
                "message": result,
                "user": {
                    "national_id": user.national_id,
                    "name": user.name,
                    "role": user.role,
                    "family": user.family.name if user.family else None
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"❌ Failed to upgrade role: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='join-family')
    def join_family(self, request):
        """
        Join an existing family.
        User must be PARENT or USER to join.
        """
        serializer = FamilySerializer(
            data=request.data,
            context={'request': request, 'action': 'join'}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            family = serializer.save()
            
            return Response({
                "message": f"✅ Successfully joined family '{family.name}'",
                "family": {
                    "id": family.id,
                    "name": family.name,
                    "members_count": User.objects.filter(family=family).count()
                }
            }, status=status.HTTP_200_OK)
                
        except Family.DoesNotExist:
            return Response(
                {"error": "❌ Family not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"❌ Failed to join family: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='leave-family')
    def leave_family(self, request):
        """
        Leave current family.
        Children cannot leave family.
        """
        user = request.user
        
        if not user.family:
            return Response(
                {"error": "❌ You are not in any family"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.role == UsersRole.CHILD:
            return Response(
                {"error": "❌ Children cannot leave family"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        family_name = user.family.name
        user.family = None
        user.save()
        
        return Response({
            "message": f"✅ Successfully left family '{family_name}'"
        }, status=status.HTTP_200_OK)


class ChildViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing children accounts.
    Only parents can create and manage children.
    """
    serializer_class = ChildSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'phone_number'
    lookup_url_kwarg = 'phone_number'

    def get_queryset(self):
        """
        Return children based on user role:
        - Parents: see their own children
        - Superusers: see all children
        """
        user = self.request.user
        
        if user.is_superuser:
            return User.objects.filter(role=UsersRole.CHILD)
        
        # Only parents can see children
        if user.role == UsersRole.PARENT and user.family:
            return User.objects.filter(
                role=UsersRole.CHILD,
                family=user.family
            )
        
        # Other users see nothing
        return User.objects.none()
    
    def get_object(self):
        """Override to get child by phone_number and verify access"""
        phone_number = self.kwargs.get('phone_number')
        queryset = self.get_queryset()
        
        try:
            obj = queryset.get(phone_number=phone_number)
        except User.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("❌ Child not found or you don't have access")
        
        # Check object permissions
        self.check_object_permissions(self.request, obj)
        return obj
    
    def create(self, request, *args, **kwargs):
        """Create a new child account (Parents only) using FamilyFacade"""
        # Check if user is a parent
        if request.user.role != UsersRole.PARENT:
            return Response(
                {"error": "❌ Only parents can create child accounts"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if parent has a family
        if not request.user.family:
            return Response(
                {"error": "❌ You must be in a family to create child accounts"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate data with serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Use FamilyFacade to create child
        try:
            family_facade = FamilyFacade(request.user)
            child_data = {
                'first_name': serializer.validated_data.get('first_name', ''),
                'last_name': serializer.validated_data.get('last_name', ''),
                'phone_number': serializer.validated_data['phone_number'],
                'national_id': serializer.validated_data['national_id'],
                'password': serializer.validated_data['password']
            }
            
            result = family_facade.create_child_account(child_data)
            
            # Get the created child
            child = User.objects.get(national_id=child_data['national_id'])
            
            return Response(
                {
                    "message": result,
                    "child": ChildSerializer(child).data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": f"❌ Failed to create child: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def list(self, request, *args, **kwargs):
        """List all children in family"""
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response({
                "message": "No children found in your family",
                "children": []
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "children": serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get details of a specific child"""
        child = self.get_object()
        serializer = self.get_serializer(child)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update child information (partial update allowed)"""
        child = self.get_object()
        
        # Prevent changing certain fields
        protected_fields = ['national_id', 'role', 'family', 'wallet','phone_number']
        for field in protected_fields:
            if field in request.data:
                return Response(
                    {"error": f"❌ Cannot modify {field}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(
            child,
            data=request.data,
            partial=kwargs.get('partial', False)
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            "message": "✅ Child account updated successfully",
            "child": serializer.data
        })
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH)"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Deactivate child account (soft delete)"""
        child = self.get_object()
        if child.is_active == False:
            return Response(
                {"message": "Child account is already deactivated"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Don't actually delete, just deactivate
        child.is_active = False
        child.save()
        
        return Response(
            {"message": "✅ Child account deactivated successfully"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='activate')
    def activate_child(self, request, phone_number=None):
        """Reactivate a deactivated child account"""
        child = self.get_object()
        
        if child.is_active:
            return Response(
                {"message": "Child account is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        child.is_active = True
        child.save()
        
        return Response({
            "message": "✅ Child account activated successfully"
        })
    
    @action(detail=True, methods=['patch'], url_path='change-password')
    def change_password(self, request, pk=None):
        """Change child's password"""
        child = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {"error": "❌ new_password is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password
        from .validations import PasswordValidationStrategy
        validator = PasswordValidationStrategy()
        if not validator.is_valid(new_password):
            return Response(
                {"error": validator.get_error_message()},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        child.set_password(new_password)
        child.save()
        
        return Response({
            "message": "✅ Password changed successfully"
        })


class FamilyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing families.
    Only authenticated users can view.
    """
    serializer_class = FamilySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return families based on user:
        - Superuser: all families
        - Regular user: only their family
        """
        user = self.request.user
        
        if user.is_superuser:
            return Family.objects.all()
        
        if user.family:
            return Family.objects.filter(id=user.family.id)
        
        return Family.objects.none()
    
    @action(detail=True, methods=['get'], url_path='members')
    def family_members(self, request, pk=None):
        """Get all members of a family"""
        family = self.get_object()
        members = User.objects.filter(family=family)
        
        # Group by role
        parents = members.filter(role=UsersRole.PARENT)
        children = members.filter(role=UsersRole.CHILD)
        
        return Response({
            "family": {
                "id": family.id,
                "name": family.name
            },
            "total_members": members.count(),
            "parents": UserSerializer(parents, many=True).data,
            "children": ChildSerializer(children, many=True).data,
        })
    
    @action(detail=True, methods=['get'], url_path='details')
    def family_details(self, request, pk=None):
        """Get detailed family information using FamilyFacade"""
        family = self.get_object()
        
        # Get any family member to create facade
        family_member = User.objects.filter(family=family).first()
        
        if not family_member:
            return Response({
                "error": "❌ No members found in this family"
            }, status=status.HTTP_404_NOT_FOUND)
        
        family_facade = FamilyFacade(family_member)
        details = family_facade.get_family_details()
        
        return Response({
            "details": details
        })

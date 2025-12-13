from django.shortcuts import render
from rest_framework import viewsets
from .models import User,UsersRole,Family
from .serializers import UserSerializer,ChildSerializer,FamilySerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, permissions,generics
from rest_framework import status
from .services import RoleManager, FamilyFacade
from django.core.exceptions import ValidationError
from wallet.serializers import WalletSerializer
from django.db.models import Q

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user accounts and family operations"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """
        List all users (Admin only)
        Supports filtering and searching
        """
        # Check if user is admin
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "❌ Admin privileges required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all users with related data
        users = User.objects.all().select_related('family').prefetch_related('wallet')
        
        # Filter by role if provided
        role = request.query_params.get('role', None)
        if role:
            users = users.filter(role=role)
        
        # Filter by active status if provided
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            users = users.filter(is_active=is_active_bool)
        
        # Search functionality
        search = request.query_params.get('search', None)
        if search:
            users = users.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(national_id__icontains=search)
            )
        
        # Order by most recent first
        users = users.order_by('-date_joined')
        
        serializer = self.get_serializer(users, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete - Deactivate user instead of deleting
        This preserves transaction history and data integrity
        """
        try:
            # 1. Check permissions
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {"error": "❌ Admin privileges required"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 2. Get user
            try:
                user = self.get_object()
            except User.DoesNotExist:
                return Response(
                    {"error": "❌ User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 3. Prevent self-deactivation
            if user.id == request.user.id:
                return Response(
                    {"error": "❌ You cannot deactivate your own account"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. Store user info before update
            username = user.username
            user_name = user.get_full_name() or user.username
            
            # 5. Perform soft delete using direct query (bypasses full validation)
            affected_rows = User.objects.filter(pk=user.pk).update(is_active=False)
            
            if affected_rows == 0:
                return Response(
                    {"error": "❌ Failed to update user status"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 6. Refresh and return
            user.refresh_from_db()
            
            return Response({
                "message": f"✅ User '{user_name}' has been deactivated successfully",
                "user": {
                    "id": user.id,
                    "username": username,
                    "is_active": user.is_active
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log the full error for debugging
            import traceback
            print("❌ Error in destroy method:")
            print(traceback.format_exc())
            
            return Response(
                {"error": f"❌ Server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """
        Update user - includes reactivation capability
        """
        try:
            partial = kwargs.pop('partial', False)
            
            # Check permissions
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {"error": "❌ Admin privileges required"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get user
            try:
                instance = self.get_object()
            except User.DoesNotExist:
                return Response(
                    {"error": "❌ User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Special handling for is_active only updates
            if 'is_active' in request.data and len(request.data) == 1:
                is_active = request.data['is_active']
                User.objects.filter(pk=instance.pk).update(is_active=is_active)
                instance.refresh_from_db()
                
                action = "reactivated" if is_active else "deactivated"
                user_name = instance.get_full_name() or instance.username
                
                return Response({
                    "message": f"✅ User '{user_name}' has been {action} successfully",
                    "user": {
                        "id": instance.id,
                        "username": instance.username,
                        "is_active": instance.is_active
                    }
                })
            
            # For other updates, use serializer
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            return Response(serializer.data)
            
        except ValidationError as e:
            return Response(
                {"error": f"❌ Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback
            print("❌ Error in update method:")
            print(traceback.format_exc())
            
            return Response(
                {"error": f"❌ Server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH)"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

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
            return Response({"message": "This user is not linked to a family."})
        family_members = User.objects.filter(family=user.family)
        serializer = self.get_serializer(family_members, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='create-family')
    def create_family(self, request):
        user = request.user

        if user.family:
            return Response(
                {"error": "⛔ You already belong to a family. Leave it first to create a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.role == UsersRole.CHILD:
            return Response({"error": "❌ Children cannot create a family"},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = FamilySerializer(
            data=request.data,
            context={'request': request, 'action': 'create'}
        )
        serializer.is_valid(raise_exception=True)

        try:
            if user.role != UsersRole.PARENT:
                success, message = RoleManager.change_user_role(user, UsersRole.PARENT)
                if not success:
                    return Response(
                        {"error": f"⛔ {message}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create the family
            family = serializer.save()

            user.refresh_from_db()

            return Response({
                "message": "✅ Family created and user upgraded to PARENT successfully",
                "family": {
                    "id": family.id,
                    "name": family.name
                },
                "user": {
                    "name": user.name,
                    "role": user.role,
                    "family_id": family.id
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"❌ Failed to create family: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'], url_path='join-family')
    def join_family(self, request):
        """Join an existing family"""
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
        """Leave current family (not allowed for children)"""
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
    
    @action(detail=False, methods=['post'], url_path='verify-national-id')
    def verify_national_id(self, request):
        """Verify and add national ID to user profile"""
        user = request.user
        national_id = request.data.get('national_id')
        
        if not national_id:
            return Response(
                {"error": "⛔ National ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check uniqueness
        if User.objects.filter(national_id=national_id).exclude(pk=user.pk).exists():
            return Response(
                {"error": "⛔ National ID already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user.national_id = national_id
            user.full_clean() 
            user.save()
            
            return Response({
                "message": "✅ National ID verified and added successfully",
                "user": {
                    "national_id": user.national_id,
                    "date_of_birth": user.date_of_birth
                }
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(
                {"error": f"⛔ {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        """
        Change password for the authenticated user
        """
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # Validate input
        if not old_password or not new_password:
            return Response(
                {'error': 'Both old_password and new_password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify old password
        if not user.check_password(old_password):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate new password
        if len(new_password) < 8:
            return Response(
                {'error': 'New password must be at least 8 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        # Use update_fields to skip full_clean validation
        user.save(update_fields=['password'])  # 👈 ADD update_fields parameter

        return Response(
            {'message': 'Password changed successfully'},
            status=status.HTTP_200_OK
        )
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
        if not request.user.family:
            return Response(
                {"error": "⛔ You must create or join a family first"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            facade = FamilyFacade(request.user)
            child = facade.create_child_account(request.data)
            
            return Response({
                "message": f"✅ Child account created successfully for {child.name}",
                "child": ChildSerializer(child).data
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(
                {"error": f"⛔ {str(e)}"},
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
        protected_fields = ['national_id', 'role', 'family', 'wallet',]
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

from rest_framework.permissions import BasePermission
from .models import UsersRole

class IsParent(BasePermission):
    """Allow access only to users with PARENT role"""
    message = "You must be a parent to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role == UsersRole.PARENT
        )


class IsParentOrReadOnly(BasePermission):
    """Allow read-only for all authenticated, write for parents only"""
    message = "You must be a parent to modify this resource."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow safe methods (GET, HEAD, OPTIONS) for all authenticated users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write operations only for parents
        return request.user.role == UsersRole.PARENT


class IsNotChild(BasePermission):
    """Prevent children from accessing certain endpoints"""
    message = "Children cannot perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role != UsersRole.CHILD
        )
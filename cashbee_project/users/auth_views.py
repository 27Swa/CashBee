from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from .models import User
from .auth_serializer import SignupSerializer, LoginSerializer

class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]  

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "message": "✅ Account created successfully",
            "user": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": str(user.phone_number),
                "email": user.email,
                "date_of_birth": user.date_of_birth,
                "role": user.role,
                "username": user.username
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]  

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            user = data.get("user")
            token = data.get("token")
            
            if user is not None:
                return Response({
                    "message": "✅ Login successful!",
                    "user": {
                        "name": user.name,
                        "phone_number": str(user.phone_number),
                        "role": user.role,
                        "date_of_birth": user.date_of_birth,
                        "username": user.username
                    },
                    "token": token,
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "❌ Invalid credentials"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            return Response({
                "error": "❌ User not found"
            }, status=status.HTTP_400_BAD_REQUEST)
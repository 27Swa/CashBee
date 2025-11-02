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
                "national_id": user.national_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "role": user.role,
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
                        "national_id": user.national_id,
                        "name": user.name,
                        "role": user.role,
                    },
                    "token": token,
                }, status=status.HTTP_200_OK)
            else:
                    return Response({
                        "error": "❌ Invalid password"
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except User.DoesNotExist:
            return Response({
                "error": "❌ User not found"
            }, status=status.HTTP_400_BAD_REQUEST)
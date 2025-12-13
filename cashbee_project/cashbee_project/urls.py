from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users import views as user_views
from wallet import views as wallet_views
from transactions import views as transaction_views
from users import auth_views as auth_views 

router = DefaultRouter()
router.register(r'users', user_views.UserViewSet)
router.register(r'transactions', transaction_views.TransactionViewSet)
router.register(r"collection-requests", transaction_views.CollectionRequestViewSet, basename="collection-request")
router.register(r'children', user_views.ChildViewSet, basename='child')
router.register(r'families', user_views.FamilyViewSet, basename='family')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/signup/', auth_views.SignupView.as_view(), name='signup'),
    path('api/login/', auth_views.LoginView.as_view(), name='login'),
    path('api/', include('wallet.urls'))
]

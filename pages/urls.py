from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name= 'HOME'),   
    path("about",views.about,name= 'ABOUT'),
    path("signup",views.signup,name= 'SIGNUP'),
    path("login",views.login,name= 'LOGIN'),
    path("family",views.family,name= 'FAMILY'),

]
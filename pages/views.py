from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request,"pages/home.html")

def about(request):
    return render(request,"pages/about.html")

def signup(request):
    return render(request,'pages/signup.html')

def login(request):
    return render(request,'pages/login.html')

def family(request):
    return render(request,'pages/family.html')

from django.shortcuts import render
from django.http import HttpResponse

def login_view(request):
    return HttpResponse("Login Page")

def logout_view(request):
    return HttpResponse("Logout Page")

def register_view(request):
    return HttpResponse("Register Page")

def profile_view(request):
    return HttpResponse("Profile Page")

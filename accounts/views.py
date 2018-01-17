from django.shortcuts import render
from .models import User, Profile
from django.views.generic import CreateView


class RegisterView(CreateView):



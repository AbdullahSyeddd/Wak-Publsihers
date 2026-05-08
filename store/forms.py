# store/forms.py
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms

class CustomerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
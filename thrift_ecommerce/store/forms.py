from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "preferred_size")
        widgets = {
            'preferred_size': forms.Select(attrs={
                'class': 'form-select mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring focus:ring-purple-200 focus:ring-opacity-50'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'
            }),
        }
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from accounts.models import User

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class":"form-control","placeholder":"Username"}))        
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control","placeholder":"Password"}))        
    # otp = forms.CharField(
    #     label="One-Time Password",
    #     required=True,
    #     widget=forms.TextInput(attrs={"placeholder": "Enter 6-digit OTP", "class": "form-control"})
    # )

    class Meta:
        model = User

        
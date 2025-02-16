from django import forms
from django.contrib.auth.models import User
from .models import Student, Event

# User Registration Form
from django import forms
from django.contrib.auth.models import User
from .models import Student

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    phone_number = forms.CharField(max_length=15, required=True)
    department = forms.CharField(max_length=100, required=True)
    batch = forms.CharField(max_length=10, required=True)
    year = forms.IntegerField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password','confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match!")

    def save(self, commit=True):
        user = super().save(commit=False)  # Don't save to DB yet
        user.set_password(self.cleaned_data["password"])  # Hash password
        if commit:
            user.save()  # Save user to DB
        return user

# Student Profile Form (Additional details)
class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['phone_number', 'department', 'batch', 'year']

# Login Form
class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

# Event Registration Form
class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'date', 'registration_fee']

from django import forms

class PaymentForm(forms.Form):
    name = forms.CharField(max_length=100)
    # Add more fields here as needed (e.g., phone number, email)

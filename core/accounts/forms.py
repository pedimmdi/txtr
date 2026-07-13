import re
from django import forms
from django.contrib.auth.password_validation import validate_password
from accounts.models import User, Profile


class RegisterForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        error_messages={
            'required': 'Email is required.',
            'invalid': 'Enter a valid email address.'
        }
    )
    username = forms.CharField(
        max_length=30,
        error_messages={'required': 'Username is required.'}
    )
    password1 = forms.CharField(
        error_messages={'required': 'Password is required.'}
    )
    password2 = forms.CharField(
        error_messages={'required': 'Please confirm your password.'}
    )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if not re.match(r'^\w+$', username):
            raise forms.ValidationError('Username can only contain letters, numbers, and underscores.')
        if Profile.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords don't match.")
        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        error_messages={
            'required': 'Email is required.',
            'invalid': 'Enter a valid email address.'
        }
    )
    password = forms.CharField(
        error_messages={'required': 'Password is required.'}
    )

    def clean(self):
        cleaned_data = super().clean()
        email    = cleaned_data.get('email', '').lower()
        password = cleaned_data.get('password')

        if not email or not password:
            return cleaned_data

        # Authenticate here so the error lands on the form, not the view
        from django.contrib.auth import authenticate
        user = authenticate(email=email, password=password)

        if user is None:
            raise forms.ValidationError('Incorrect email or password. Please try again.')

        if not user.is_active:
            raise forms.ValidationError('This account has been deactivated.')

        # Attach the authenticated user to the form for use in the view
        self.user = user
        return cleaned_data

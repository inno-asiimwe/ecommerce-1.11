from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import User, EmailActivation


class UserAdminCreationForm(forms.ModelForm):
    """ Form for creating users via django admin """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        """ Ensure password match """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('passwords do not match')
        return password2

    def save(self, commit=True):
        """ Hash Password """
        user = super(UserAdminCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    """ Form for Updating User """

    password = ReadOnlyPasswordHashField

    class Meta:
        model = User
        fields = ('email', 'password', 'is_active', 'admin')

    def clean_password(self):
        """ Return initial password """
        return self.initial["password"]


class RegisterForm(forms.ModelForm):
    """ Form for registering a user """
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('email',)
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }

    def clean_password2(self):
        """ Ensure password match """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('passwords do not match')
        return password2

    def save(self, commit=True):
        """ Hash Password """
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """ Form handles login """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class ReactivateEmailForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form_control'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = EmailActivation.objects.email_exists(email)
        if not qs.exists():
            raise forms.ValidationError("This email does not exist")
        return email

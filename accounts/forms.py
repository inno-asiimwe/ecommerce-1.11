from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth import login, authenticate
from .models import User, EmailActivation, Profile


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

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(RegisterForm, self).__init__(*args, **kwargs)


    def clean_password2(self):
        """ Ensure password match """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('passwords do not match')
        return password2

    def save(self, commit=True):
        """ Hash Password """
        request = self.request
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False
        if commit:
            user.save()
        # handle a user registering as a merchant
        if request.path == '/merchant/register':
            user_profile = Profile.objects.filter(user=user).first()
            user_profile.is_merchant = True
            user_profile.save()
        return user


class LoginForm(forms.Form):
    """ Form handles login """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        request = self.request
        data = self.cleaned_data
        email = data.get('email')
        password = data.get('password')
        qs = User.objects.filter(email=email)
        if qs.exists():
            qs_inactive = qs.filter(is_active=False).exists()
            if qs_inactive:
                resend_link = reverse("account:resend-email")
                reconfirm_msg = """
                Go to <a href={resend_link}>Resend activation link</a>
                """.format(resend_link=resend_link)
                confirm_email_qs = EmailActivation.objects.filter(email=email)
                confirmable_email = confirm_email_qs.confirmable().exists()
                if confirmable_email:
                    msg1 = """ 
                    Check your inbox for confirmation
                    email.
                    """ + reconfirm_msg
                    raise forms.ValidationError(mark_safe(msg1))
                confirm_email_exists = EmailActivation.objects.email_exists(
                    email=email).exists()
                if confirm_email_exists:
                    msg2 = "Please reactivate your email. " + reconfirm_msg
                    raise forms.ValidationError(mark_safe(msg2))
                if not confirmable_email and not confirm_email_exists:
                    raise forms.ValidationError("User is inactive")
        user = authenticate(request, username=email, password=password)
        if user is None:
            raise forms.ValidationError("Invalid logins")
        # raise an error when a regular user signs in as a merchant
        if request.path == '/merchant/login':
            if not user.profile_set.first().is_merchant:
                msg = """
                Please use a merchant account to login
                """
                raise forms.ValidationError(msg)
        login(request, user)
        self.user = user
        return data


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


class ProfileUpdateForm(forms.ModelForm):
    """ Form for updating a user profile """

    class Meta:
        model = Profile
        fields = ('full_name', 'location')
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'})
        }
        required = ('full_name', 'location')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)

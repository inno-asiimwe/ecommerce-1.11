from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.http import is_safe_url
from django.http import HttpResponse
from django.views.generic import CreateView, FormView, View, UpdateView
from django.views.generic.edit import FormMixin
from ecommerce.mixins import NextUrlMixin, RequestFormAttachMixin
from .models import User, Profile, EmailActivation
from .forms import (RegisterForm,
                    LoginForm,
                    ReactivateEmailForm,
                    ProfileUpdateForm)


class AccountEmailActivateView(FormMixin, View):
    """View activates an email or resends an activation link"""
    success_url = '/login/'
    form_class = ReactivateEmailForm
    key = None

    def get(self, request, key=None, *args, **kwargs):
        self.key = key
        if key is not None:
            qs = EmailActivation.objects.filter(key__iexact=key)
            confirm_qs = qs.confirmable()
            if confirm_qs.count() == 1:
                obj = confirm_qs.first()
                obj.activate()
                messages.success(request, "your email has been confirmed.")
                return redirect("login")
            activated_qs = qs.filter(activated=True)
            if activated_qs.exists():
                msg = "Already activated login"
                messages.success(request, msg)
                return redirect("login")
        context = {'form': self.get_form(), 'key': key}
        return render(
            request, 'accounts/registration/activation-error.html', context)

    def post(self, request, key=None, *args, **kwargs):
        # create form to receive an email for reactivation
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        request = self.request
        messages.success(request, 'Activation link sent to email')
        email = form.cleaned_data.get('email')
        obj = EmailActivation.objects.email_exists(email).first()
        user = obj.user
        new_activation = EmailActivation.objects.create(user=user, email=email)
        new_activation.send_activation()
        return super(AccountEmailActivateView, self).form_valid(form)

    def form_invalid(self, form):
        context = {'form': self.get_form(), 'key': self.key}
        return render(
            self.request,
            'accounts/registration/activation-error.html', context)


class RegisterView(RequestFormAttachMixin, CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = '/login/'


class LoginView(RequestFormAttachMixin, NextUrlMixin, FormView):
    """ View Logs in a user """
    form_class = LoginForm
    template_name = 'accounts/login.html'
    success_url = '/'
    default_next = '/'

    def get(self, *args, **kwargs):
        user = self.request.user
        path = self.request.path

        if path == reverse('merch_login') and user.is_authenticated():
            if user.profile_set.first().is_merchant:
                return redirect(reverse('merch_dashboard'))
            msg = """
            please login in with a merchant account to access this section.
            """
            messages.error(self.request, msg)
            return self.render_to_response(self.get_context_data())
        return self.render_to_response(self.get_context_data())

    def form_valid(self, form):
        next_path = self.get_next_url()
        if self.request.path == reverse('merch_login'):
            return redirect(reverse('merch_dashboard'))
        return redirect(next_path)


class ProfileUpdateView(RequestFormAttachMixin, UpdateView):
    """ View for updating profile """
    form_class = ProfileUpdateForm
    template_name = 'accounts/form.html'
    success_url = reverse_lazy('merch_dashboard')

    def get_object(self, *args, **kwargs):
        user = self.request.user
        profile = Profile.objects.filter(user=user).first()
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Profile Update'
        context['message'] = 'Update your profile before continuing!!'
        return context


class MerchantDashboardView(LoginRequiredMixin, View):
    """ View for the Merchant Dashboard """
    login_url = reverse_lazy('merch_login')

    def get(self, *args, **kwargs):
        user = self.request.user
        if user is not None:
            profile = user.profile_set.first()
            if not profile.completed():
                return redirect(reverse('account:profile-update'))
            return render(self.request, 'merchant/dashboard.html')

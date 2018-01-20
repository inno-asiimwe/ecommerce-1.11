from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.http import is_safe_url
from django.views.generic import CreateView, FormView, View
from django.views.generic.edit import FormMixin
from .models import User, Profile, EmailActivation
from .forms import RegisterForm, LoginForm, ReactivateEmailForm


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

    def post(self, request, key, *args, **kwargs):
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



class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = '/login/'


class LoginView(FormView):
    """ View Logs in a user """
    form_class = LoginForm
    template_name = 'accounts/login.html'
    success_url = '/'

    def form_valid(self, form):
        request = self.request
        next_ = request.GET.get('next')
        next_post = request.POST.get('next')
        redirect_path = next_ or next_post or None
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if is_safe_url(redirect_path, request.get_host()):
                    return redirect(redirect_path)
                return redirect('/')
            return super(LoginView, self).form_invalid(form)
        return super(LoginView, self).form_invalid(form)
        

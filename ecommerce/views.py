from django.views.generic import TemplateView
from django.shortcuts import render


class HomeView(TemplateView):
    """View for the home page"""
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        """set context variables for the home age"""
        context = super(HomeView, self).get_context_data(**kwargs)
        context['title'] = 'Home Page'
        context['content'] = 'Welcome to our Python Ecommerce site'
        return context

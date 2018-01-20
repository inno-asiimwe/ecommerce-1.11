from django.conf.urls import url

from .views import (
    AccountEmailActivateView,
    )

urlpatterns = [
    url(r'^email/confirm/(?P<key>[0-9A-Za-z]+)/$',
        AccountEmailActivateView.as_view(),
        name='email-activate'),
    url(r'^resend-email/$',
        AccountEmailActivateView.as_view(),
        name='resend-email')
]
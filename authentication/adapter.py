from allauth.account.adapter import DefaultAccountAdapter
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site

try:
    from allauth.account import app_settings as allauth_account_settings
except ImportError:
    raise ImportError("allauth needs to be added to INSTALLED_APPS.")


class CustomAccountAdapter(DefaultAccountAdapter):
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        current_site = get_current_site(request)
        client_domain = settings.CLIENT_DOMAIN
        client_verify_account_path = settings.CLIENT_VERIFY_ACCOUNT_PATH
        activate_url = f"https://{client_domain}/{client_verify_account_path}/{emailconfirmation.key}"
        # activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
            "full_name": emailconfirmation.email_address.user.username,
        }
        # if signup:
        #     email_template = "authentication/email_confirmation_signup"
        # else:
        email_template = "authentication/email_confirmation"
        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)

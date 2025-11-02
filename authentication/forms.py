from allauth.account.adapter import get_adapter
from allauth.account.forms import ResetPasswordForm
from allauth.account.utils import user_pk_to_url_str
from dal import autocomplete
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.forms import ModelForm


class CustomResetPasswordForm(ResetPasswordForm):
    def save(self, request, **kwargs):
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator")
        # raise Exception(f"kwargs: {kwargs}")
        # template = kwargs.get("email_template")
        extra = kwargs.get("extra_email_context", {})
        client_domain = settings.CLIENT_DOMAIN
        client_reset_path = settings.CLIENT_RESET_PATH
        for user in self.users:
            uid = user_pk_to_url_str(user)
            token = token_generator.make_token(user)
            reset_url = f"https://{client_domain}/{client_reset_path}/{uid}/{token}"
            context = {
                "user": user,
                "request": request,
                "email": email,
                "reset_url": reset_url,
            }
            context.update(extra)
            get_adapter(request).send_mail(
                "authentication/password_reset_key", email, context
            )
        return email


class TransactionAdminForm(ModelForm):
    class Meta:
        model = get_user_model()
        fields = "__all__"
        widgets = {
            "user": autocomplete.ModelSelect2(
                url="authentication:transaction-user-autocomplete",
                attrs={
                    # Set placeholder
                    "data-placeholder": "Enter User Email..",
                    # Only trigger autocompletion after 3 characters have been typed
                    "data-minimum-input-length": 3,
                },
            ),
        }

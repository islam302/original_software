from dal import autocomplete
from django import forms
from django.forms import ModelForm
from import_export.forms import ConfirmImportForm, ImportForm

from products.models import Product, ProductOption


class CustomProductKeyImportForm(ImportForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=True)


class CustomProductKeyConfirmImportForm(ConfirmImportForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=True)


class ProductOptionAdminForm(ModelForm):
    class Meta:
        model = ProductOption
        fields = "__all__"
        widgets = {
            "product": autocomplete.ModelSelect2(
                url="products:product_option_autocomplete",
                attrs={
                    # Set placeholder
                    "data-placeholder": "Enter Product Name..",
                    # Only trigger autocompletion after 3 characters have been typed
                    "data-minimum-input-length": 3,
                },
            ),
        }

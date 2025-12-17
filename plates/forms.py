from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Emirate, PlateType

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your Name')
        }),
        label=_('Name')
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your Email')
        }),
        label=_('Email')
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your Phone (Optional)')
        }),
        label=_('Phone')
    )
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Subject')
        }),
        label=_('Subject')
    )
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': _('Your Message')
        }),
        label=_('Message')
    )


class SellPlateForm(forms.Form):
    # Seller Information
    seller_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your Full Name')
        }),
        label=_('Your Name')
    )
    seller_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your Email')
        }),
        label=_('Your Email')
    )
    seller_phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your Phone Number')
        }),
        label=_('Phone Number')
    )
    seller_whatsapp = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('WhatsApp Number (Optional)')
        }),
        label=_('WhatsApp Number')
    )
    
    # Plate Details
    emirate = forms.ModelChoiceField(
        queryset=Emirate.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label=_('Emirate'),
        empty_label=_('Select Emirate')
    )
    plate_type = forms.ModelChoiceField(
        queryset=PlateType.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label=_('Plate Type'),
        empty_label=_('Select Plate Type')
    )
    code = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., F, AA, 1')
        }),
        label=_('Plate Code'),
        help_text=_('Letter/code e.g. F, AA, 1')
    )
    number = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Plate Number')
        }),
        label=_('Plate Number'),
        help_text=_('Digits/characters as displayed on the plate')
    )
    price_aed = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Price in AED (Optional)')
        }),
        label=_('Asking Price (AED)'),
        help_text=_('Leave blank if you want us to help determine the price')
    )
    plate_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label=_('Plate Image'),
        help_text=_('Upload a photo of your plate (Optional)')
    )
    additional_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Any additional information about the plate...')
        }),
        label=_('Additional Notes'),
        help_text=_('Any other details you want to share')
    )


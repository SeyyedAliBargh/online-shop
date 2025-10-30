from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import ShopUser


class ShopUserCreationForm(UserCreationForm):
    """
    this class creates a new ShopUser
    """
    class Meta(UserCreationForm.Meta):
        model = ShopUser
        fields = (
            'phone',
            'email',
            'is_staff',
            'is_active',
            'is_superuser',
            'is_verified',
        )

        def clean_phone(self):
            """
            checks if the phone number is valid
            :return:
            """
            phone = self.cleaned_data.get('phone')
            if self.instance.pk:
                if ShopUser.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError("Phone number already in use.")
            if not phone.isdigit():
                raise forms.ValidationError("Phone number must be all digits.")
            if not phone.startswith('09'):
                raise forms.ValidationError("Phone number must start with 09.")
            if len(phone) != 11:
                raise forms.ValidationError("Phone number must have exactly 11 digit.")
            return phone


class ShopUserChangeForm(UserChangeForm):
    """
    this class updates a ShopUser
    """
    class Meta(UserChangeForm.Meta):
        model = ShopUser
        fields = (
            'phone',
            'email',
            'is_staff',
            'is_active',
            'is_superuser',
            'is_verified',
        )

    def clean_phone(self):
        """
        checks if the phone number is valid
        :return:
        """
        phone = self.cleaned_data.get('phone')
        if self.instance.pk:
            if ShopUser.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Phone number already in use.")
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must be all digits.")
        if not phone.startswith('09'):
            raise forms.ValidationError("Phone number must start with 09.")
        if len(phone) != 11:
            raise forms.ValidationError("Phone number must have exactly 11 digit.")
        return phone

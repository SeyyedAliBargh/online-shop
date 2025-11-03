from django import forms

from order.models import Order


class PhoneVerificationForm(forms.Form):
    phone = forms.CharField(max_length=11, widget=forms.TextInput(attrs={"class": "phone_input"}), label="تلفن")
    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if phone.isdigit() and len(phone) == 11 and phone.startswith("09"):
            return phone
        else:
            raise forms.ValidationError("شماره تماس معتبر وارد کنید!")

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["first_name", "last_name", "phone", "address", "postal_code", "city",
                  "province"]
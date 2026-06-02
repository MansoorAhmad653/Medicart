from django import forms
from users.forms import validate_phone_number


class CheckoutForm(forms.Form):
    delivery_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your full delivery address'}),
        label='Delivery Address'
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number for delivery (03XX-XXXXXXX)'}),
        label='Contact Phone',
        validators=[validate_phone_number]
    )
    payment_method = forms.ChoiceField(
        choices=[('cod', 'Cash on Delivery'), ('card', 'Credit/Debit Card (Coming Soon)')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='cod',
        label='Payment Method'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Special instructions (optional)'}),
        label='Order Notes'
    )
    prescription_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
        label='Upload Prescription (Required for Rx medicines)'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

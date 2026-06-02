from django import forms
from .models import Medicine


class MedicineForm(forms.ModelForm):
    """Form for adding/editing medicines with Supabase image upload"""
    image_upload = forms.ImageField(
        required=False,
        label="Upload Medicine Image (JPG, PNG)",
        help_text="Upload image to Supabase Storage",
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Medicine
        fields = ['name', 'category', 'price', 'stock_quantity', 'description', 'image', 
                  'requires_prescription', 'manufacturer', 'dosage', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requires_prescription': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'image': '✅ Auto-uploaded to Supabase Storage when you upload a file above'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide the image field since we handle it separately
        self.fields['image'].widget = forms.HiddenInput()
        self.fields['image'].required = False
    
    def save(self, commit=True):
        from .services import upload_medicine_image, update_medicine_image
        
        medicine = super().save(commit=False)
        
        # Handle image upload to Supabase
        image_upload = self.cleaned_data.get('image_upload')
        if image_upload:
            # If editing existing medicine with image, update it
            if medicine.pk and medicine.image:
                image_url = update_medicine_image(medicine, image_upload)
            else:
                # New medicine or no existing image
                image_url = upload_medicine_image(image_upload, medicine.name.replace(' ', '_').lower())
            
            if image_url:
                medicine.image = image_url
        
        if commit:
            medicine.save()
        
        return medicine


class CheckoutForm(forms.Form):
    delivery_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your full delivery address'}),
        label='Delivery Address'
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number for delivery'}),
        label='Contact Phone'
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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

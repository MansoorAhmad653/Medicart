from django import forms
from .models import Prescription


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ('file', 'notes')
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any additional notes for the pharmacist (optional)'}),
        }
        labels = {
            'file': 'Prescription File (Image or PDF)',
            'notes': 'Notes for Pharmacist',
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            name = file.name.lower()
            allowed = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf')
            if not any(name.endswith(ext) for ext in allowed):
                raise forms.ValidationError('Only image files (JPG, PNG, GIF, WEBP) and PDF files are allowed.')
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 10MB.')
        return file

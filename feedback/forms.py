from django import forms
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        label='Rating'
    )

    class Meta:
        model = Feedback
        fields = ('rating', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your experience...'}),
        }

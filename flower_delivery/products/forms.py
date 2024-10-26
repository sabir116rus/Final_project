# products/forms.py

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.RadioSelect,
        label='Оценка'
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        labels = {
            'comment': 'Комментарий',
        }
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

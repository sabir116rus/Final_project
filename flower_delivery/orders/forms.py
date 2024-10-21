# orders/forms.py

from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['address', 'phone', 'comment']
        labels = {
            'address': 'Адрес доставки',
            'phone': 'Контактный телефон',
            'comment': 'Комментарий к заказу',
        }
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=20, initial=1)
# orders/forms.py

from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['address', 'phone', 'comment', 'delivery_date', 'delivery_time', 'delivery_place']
        labels = {
            'address': 'Адрес доставки',
            'phone': 'Контактный телефон',
            'comment': 'Комментарий к заказу',
            'delivery_date': 'Дата доставки',
            'delivery_time': 'Время доставки',
            'delivery_place': 'Место доставки',
        }
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'delivery_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'delivery_place': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=20, initial=1)
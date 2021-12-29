from django import forms
from .models import Order


class NewOrder(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['trader', 'type', 'btc', 'price']

from django import forms
from .models import Driver, Order


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        # Перечисляем новые поля
        fields = ['last_name', 'first_name', 'middle_name', 'iin', 'phone', 'experience', 'category']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Отчество'}),
            'iin': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
        }

class OrderForm(forms.ModelForm):
    distance = forms.IntegerField(
        required=False, 
        initial=5, 
        label="Расстояние (км)"
    )
    
    class Meta:
        model = Order
        fields = ['point_a', 'point_b', 'tariff']
        widgets = {
            'point_a': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Откуда'}),
            'point_b': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Куда'}),
            'tariff': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.com'})
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        label='Ваша роль в системе',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'phone')

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['phone', 'avatar']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (___) ___ __ __'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
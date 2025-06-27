from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

WARD_CHOICES = [
    ('Ward 1 – Ratnechaur', 'Ward 1 – Ratnechaur'),
    ('Ward 2 – Jyamrukot', 'Ward 2 – Jyamrukot'),
    ('Ward 3 – Bhakimli', 'Ward 3 – Bhakimli'),
    ('Ward 4 – Mangale', 'Ward 4 – Mangale'),
    ('Ward 5 – Naku', 'Ward 5 – Naku'),
    ('Ward 6 – Arthunge', 'Ward 6 – Arthunge'),
    ('Ward 7 – Purnagaun', 'Ward 7 – Purnagaun'),
    ('Ward 8 – Banethok Deurali', 'Ward 8 – Banethok Deurali'),
    ('Ward 9 – Thakle', 'Ward 9 – Thakle'),
    ('Ward 10 – Patlekhet', 'Ward 10 – Patlekhet'),
]

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phonenumber = forms.CharField(required=True, max_length=20)
    ward = forms.ChoiceField(choices=WARD_CHOICES, required=True)
    tole = forms.CharField(required=True, max_length=100, label="Tole (Neighborhood)")
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phonenumber', 'ward', 'tole', 'role', 'password1', 'password2')
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already taken. Please use a different one.")
        return email

    def clean_phonenumber(self):
        phonenumber = self.cleaned_data.get('phonenumber')
        if not phonenumber.isdigit():
            raise forms.ValidationError("Please enter digits only for the phone number.")
        if len(phonenumber) < 8:
            raise forms.ValidationError("Phone number must be at least 8 digits.")
        if Profile.objects.filter(phonenumber=phonenumber).exists():
            raise forms.ValidationError("Phone number is already taken. Please use a different one.")
        return phonenumber
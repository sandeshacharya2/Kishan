from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, FarmerProfile, CustomerProfile
from django.utils.translation import gettext_lazy as _

WARD_CHOICES = [
    ('Ward 1 – Ratnechaur', 'वडा १ – रातनेचौर'),
    ('Ward 2 – Jyamrukot', 'वडा २ – ज्यामरुकोट'),
    ('Ward 3 – Bhakimli', 'वडा ३ – भाकिम्ली'),
    ('Ward 4 – Singa', 'वडा ४ – सिङ्गा'),
    ('Ward 5 – Pulachaur', 'वडा ५ – पुलाचौर'),
    ('Ward 6 – Arthunge', 'वडा ६ – अर्थुङ्गे'),
    ('Ward 7 – Beni', 'वडा ७ – बेनी'),
    ('Ward 8 – Beni', 'वडा ८ – बेनी'),
    ('Ward 9 – Ghatan', 'वडा ९ – घतान'),
    ('Ward 10 – Patlekhet', 'वडा १० – पात्लेखेत'),
]

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        error_messages={'required': 'कृपया इमेल अनिवार्य रूपमा भर्नुहोस्।'}
    )
    phonenumber = forms.CharField(
        required=True,
        max_length=20,
        error_messages={'required': 'कृपया फोन नम्बर अनिवार्य रूपमा भर्नुहोस्।'}
    )
    ward = forms.ChoiceField(
        choices=WARD_CHOICES,
        required=True,
        error_messages={'required': 'कृपया वडा छान्नुहोस्।'}
    )
    first_name = forms.CharField(
    required=True,
    max_length=30,
    label="First Name",
    widget=forms.TextInput(attrs={'autofocus': True}),
    error_messages={'required': 'कृपया पहिलो नाम अनिवार्य रूपमा लेख्नुहोस्।'}
)

    last_name = forms.CharField(
        required=True,
        max_length=30,
        label="Last Name",
        error_messages={'required': 'कृपया अन्तिम नाम अनिवार्य रूपमा लेख्नुहोस्।'}
    )   

    tole = forms.CharField(
        required=True,
        max_length=100,
        label="Tole (Neighborhood)",
        error_messages={'required': 'कृपया टोल अनिवार्य रूपमा लेख्नुहोस्।'}
    )
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        required=True,
        error_messages={'required': 'कृपया भूमिका छान्नुहोस्।'}
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        error_messages={'required': 'पासवर्ड आवश्यक छ'}
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        error_messages={'required': 'पासवर्ड पुन दोहोर्याउनु होस् '}
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'phonenumber', 'ward', 'tole', 'role', 'password1', 'password2')
        error_messages = {
            'username': {
                'required': 'कृपया प्रयोगकर्ता नाम लेख्नुहोस्।'
            },
            'password1': {
                'required': 'कृपया पासवर्ड लेख्नुहोस्।'
            },
            'password2': {
                'required': 'कृपया पासवर्ड दोहोर्याउनुहोस्।'
            },
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("यो इमेल पहिले नै प्रयोग भैसकेको छ, कृपया नया इमेल प्रयोग गर्नुहोस्।")
        return email

    def clean_phonenumber(self):
        phonenumber = self.cleaned_data.get('phonenumber')
        if not phonenumber.isdigit():
            raise forms.ValidationError("फोन नम्बर अंकमा मात्र लेख्नुहोस्।")
        if len(phonenumber) < 8:
            raise forms.ValidationError("फोन नम्बर कम्तीमा ८ अंकको हुनु पर्छ।")
        if Profile.objects.filter(phonenumber=phonenumber).exists():
            raise forms.ValidationError("यो फोन नम्बर पहिले नै प्रयोग भैसकेको छ। कृपया अर्को प्रयोग गर्नुहोस्।")
        return phonenumber


class FarmerProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FarmerProfileForm, self).__init__(*args, **kwargs)
        # self.fields['first_name'].required = True
        # self.fields['last_name'].required = True

    class Meta:
        model = FarmerProfile
        fields = [ 'profile_picture']
        widgets = {
            # 'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            # 'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class CustomerProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CustomerProfileForm, self).__init__(*args, **kwargs)
   

    class Meta:
        model = CustomerProfile
        fields = ['profile_picture']
        widgets = {
          
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
from django import forms
from .models import FarmerReview

class FarmerReviewForm(forms.ModelForm):
    class Meta:
        model = FarmerReview
        fields = ['rating']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5})
        }

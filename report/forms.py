# reports/forms.py
from django import forms
from report.models import FarmerReport, CustomerReport

class FarmerReportForm(forms.ModelForm):
    class Meta:
        model = FarmerReport
        fields = ['category', 'subject', 'message']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your issue in detail...'}),
        }

class CustomerReportForm(forms.ModelForm):
    class Meta:
        model = CustomerReport
        fields = ['category', 'subject', 'message']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your issue in detail...'}),
        }
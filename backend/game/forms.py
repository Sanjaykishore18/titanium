
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Team, JoinRequest

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=200, required=True)
    phone = forms.CharField(max_length=15, required=False)
    college = forms.CharField(max_length=200, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'phone', 'college', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                email=self.cleaned_data['email'],
                phone=self.cleaned_data.get('phone', ''),
                college=self.cleaned_data.get('college', '')
            )
        return user

class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['team_name', 'max_members']
        widgets = {
            'team_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter team name'}),
            'max_members': forms.NumberInput(attrs={'class': 'form-control', 'min': 2, 'max': 10, 'value': 4})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['team_name'].help_text = 'Choose a unique team name'
        self.fields['max_members'].help_text = 'Maximum 10 members allowed'

class JoinTeamForm(forms.Form):
    team_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit team code',
            'pattern': '[A-Z0-9]{6}'
        })
    )

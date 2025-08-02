from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from django.contrib.auth import get_user_model

from .models import ShippingInfo

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email',
            'autocomplete': 'email',
            'name': 'email',
        }),
        label='Email',
    )
    nickname = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Nickname',
        }),
        label='Nickname',
    )
    username = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = ['email', 'nickname', 'username', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(f'Email "{email}" is already in use.')
        return email

    def clean_nickname(self):
        # Bypassing browser autofill bullshit: map a fake 'nickname' field to 'username'
        # so password managers save email instead of username
        nickname = self.cleaned_data.get('nickname')
        if User.objects.filter(username=nickname).exists():
            raise forms.ValidationError(f'Nickname "{nickname}" is already in use.')
        return nickname

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['username'] = cleaned_data.get('nickname')
        return cleaned_data


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'placeholder': 'Email',
            'autocomplete': 'email',
        }),
        label='Email',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        label='Password',
    )


class UserPasswordCheckForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Current password'}),
        label='Password',
    )


class UserPasswordResetForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'placeholder': 'Email',
            'autocomplete': 'email',
        }),
        label='Email',
    )


class UserSetPasswordForm(SetPasswordForm):
    pass


class UserEmailUpdateForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        label='Password',
    )
    new_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'New email'}),
        label='New email',
    )

    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email')
        if User.objects.filter(email=new_email).exists():
            raise forms.ValidationError(f'Email "{new_email}" is already in use.')
        return new_email


class ShippingInfoForm(forms.ModelForm):
    class Meta:
        model = ShippingInfo
        exclude = ['user']
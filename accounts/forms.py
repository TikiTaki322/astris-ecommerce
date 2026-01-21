from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from accounts.models import ShippingInfo

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email').lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(f'Email "{email}" already in use')
        return email

    def clean(self):
        cleaned = super().clean()

        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')

        if p1 and p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords don't match")

            try:
                validate_password(p1)
            except ValidationError as exc:
                self.add_error('password1', exc)

        return cleaned


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'autocomplete': 'email',
        }),
        label='Email',
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Password',
    )


class UserPasswordCheckForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Current password'}),
        label='Password',
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Wrong password')
        return password


class UserPasswordResetForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput)


class UserSetPasswordForm(SetPasswordForm):
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if self.user.check_password(password):
            raise forms.ValidationError('The new password cannot be the same as the old one')

        return password

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('new_password1')

        try:
            validate_password(password)
        except ValidationError as exc:
            self.add_error('new_password1', exc)

        return cleaned




class UserEmailUpdateForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Password',
    )
    new_email = forms.EmailField(
        widget=forms.EmailInput,
        label='New email',
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Wrong password')
        return password

    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email')
        if User.objects.filter(email=new_email).exists():
            raise forms.ValidationError(f'Email "{new_email}" already in use')
        return new_email


class ShippingInfoForm(forms.ModelForm):
    class Meta:
        model = ShippingInfo
        exclude = ['user', 'email']
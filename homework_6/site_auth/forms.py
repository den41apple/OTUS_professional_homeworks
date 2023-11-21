from django import forms
from django.contrib.auth.forms import (UserCreationForm as UserCreationFormGeneric,
                                       AuthenticationForm as AuthenticationFormGeneric)


class UserCreationForm(UserCreationFormGeneric):
    """
    Регистрация
    """
    avatar = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Login"
        self.fields['email'].label = "Email"
        self.fields['password2'].label = "Repeat Password"
        for name, field in self.fields.items():
            field.help_text = None

    class Meta(UserCreationFormGeneric.Meta):
        fields = "username", "email", "password1", "password2", "avatar"


class AuthenticationForm(AuthenticationFormGeneric):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field: forms.Field
            widget: forms.Widget = field.widget
            widget.attrs["class"] = "form-control my-2"

from django import forms

from .models import Profile


class UserProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = "username", "email",

    username = forms.CharField(label="Login")
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        # Установим значения
        self.initial = {"username": user.username,
                        "email": user.email}
        for name, field in self.fields.items():
            field: forms.Field
            widget: forms.Widget = field.widget
            if name == "username":
                widget.attrs["class"] = "disabled"
                widget.attrs["readonly"] = "readonly"

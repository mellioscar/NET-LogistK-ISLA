# usuarios/forms.py
from django import forms
from django.contrib.auth.models import User, Group

class CrearUsuarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmar contraseña")
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=True, label="Grupo")

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # Asignar el grupo seleccionado al usuario
            group = self.cleaned_data['group']
            user.groups.add(group)
        return user

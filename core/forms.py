from django import forms
from django.contrib.auth.hashers import make_password
from .models import Usuario, AuthIdentidad, Perfil, RegistroConsumo
import bcrypt
from .utils.crypto import encrypt_field

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['rut', 'nombres', 'apellidos', 'tipo_vivienda']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RegistroConsumoForm(forms.ModelForm):
    class Meta:
        model = RegistroConsumo
        fields = ['fecha', 'consumo_kwh', 'costo_clp', 'dispositivo', 'fuente']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'consumo_kwh': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo_clp': forms.NumberInput(attrs={'class': 'form-control'}),
            'dispositivo': forms.Select(attrs={'class': 'form-control'}),
            'fuente': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AdminRegisterUserForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico", required=True)
    nombres = forms.CharField(label="Nombres", max_length=100)
    apellidos = forms.CharField(label="Apellidos", max_length=100)
    rut = forms.CharField(label="RUT", max_length=12, required=False)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    def save(self, admin_user):
        """Crea Usuario, AuthIdentidad y Perfil"""
        from uuid import uuid4
        from django.utils import timezone
        from .models import Usuario, AuthIdentidad, Perfil

        usuario = Usuario.objects.create(
            id=uuid4(),
            activo=True,
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
        )

        # Generar hash bcrypt
        hashed_pw = bcrypt.hashpw(self.cleaned_data["password"].encode(), bcrypt.gensalt()).decode()

        AuthIdentidad.objects.create(
            usuario=usuario,
            email=self.cleaned_data["email"],
            contrasena_hash=hashed_pw,
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
        )

        Perfil.objects.create(
            usuario=usuario,
            rut=encrypt_field(self.cleaned_data.get("rut")),
            nombres=self.cleaned_data["nombres"],
            apellidos=self.cleaned_data["apellidos"],
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
        )

        # Auditoría básica (opcional)
        from .models import AuditoriaEvento
        AuditoriaEvento.objects.create(
            usuario_id=admin_user.id,
            entidad="Usuario",
            entidad_id=str(usuario.id),
            accion="CREAR",
            detalle={"email": self.cleaned_data["email"]},
            ocurrido_en=timezone.now(),
        )
        return usuario
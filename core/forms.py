import re, hashlib
from django.utils import timezone
from django import forms
from django.db import transaction
from django.contrib.auth.hashers import make_password
from .models import Usuario, AuthIdentidad, Perfil, RegistroConsumo, AuditoriaEvento
import bcrypt
from .utils.crypto import encrypt_field
from uuid import uuid4


def _normaliza_rut(rut: str) -> str:
    if not rut:
        return ""
    # elimina puntos/espacios y deja guión
    rut = rut.strip().replace(".", "").replace(" ", "")
    return rut

def _rut_hash_hex(rut: str) -> str:
    # normaliza a minúsculas para el dígito verificador
    norm = _normaliza_rut(rut).lower()
    return hashlib.sha256(norm.encode()).hexdigest()



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

    def clean_email(self):
        # normaliza a minúsculas para alinear con índice unique en BD (lower(email))
        return self.cleaned_data["email"].strip().lower()

    def clean_rut(self):
        # el RUT puede venir vacío; si no, normalizamos formato básico
        rut = self.cleaned_data.get("rut") or ""
        return _normaliza_rut(rut)

    @transaction.atomic
    def save(self, admin_user):
        email_norm = self.cleaned_data["email"]

        # Valida que no exista la identidad (case-insensitive)
        if AuthIdentidad.objects.filter(email__iexact=email_norm).exists():
            self.add_error("email", "Este correo ya está registrado.")
            raise forms.ValidationError("Correo duplicado")

        # Crea el sujeto Usuario (UUID PK definido también con default=uuid4 en el modelo recomendado)
        usuario = Usuario.objects.create(
            id=uuid4(),
            activo=True,
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
        )

        # Generar hash bcrypt de la contraseña
        hashed_pw = bcrypt.hashpw(
            self.cleaned_data["password"].encode(), bcrypt.gensalt()
        ).decode()

        # Crea identidad de login (email único CI + hash)
        AuthIdentidad.objects.create(
            # Si tu modelo ya tiene default=uuid4 en id, no hace falta pasar id aquí
            usuario=usuario,
            email=email_norm,
            contrasena_hash=hashed_pw,
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
        )

        # Cifra RUT y calcula hash determinístico para unicidad
        rut_plain = self.cleaned_data.get("rut") or ""
        rut_enc = encrypt_field(rut_plain) if rut_plain else None
        rut_hex = _rut_hash_hex(rut_plain) if rut_plain else None

        # Unicidad por hash (si definiste ux_perfiles_rut_hash)
        if rut_hex and Perfil.objects.filter(rut_hash=rut_hex).exists():
            self.add_error("rut", "Este RUT ya está registrado.")
            raise forms.ValidationError("RUT duplicado")

        # Crea perfil: guarda cifrado + hash
        Perfil.objects.create(
            usuario=usuario,
            rut=rut_enc,                  # 🔐 guardamos cifrado (Fernet)
            rut_hash=rut_hex,             # 🔎 unicidad por hash
            nombres=self.cleaned_data["nombres"],
            apellidos=self.cleaned_data["apellidos"],
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
        )

        # Auditoría
        AuditoriaEvento.objects.create(
            usuario_id=admin_user.id,
            entidad="Usuario",
            entidad_id=str(usuario.id),
            accion="CREAR",
            detalle={"email": email_norm},
            ocurrido_en=timezone.now(),
        )

        return usuario
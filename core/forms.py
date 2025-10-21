import re, hashlib
from django.utils import timezone
from django import forms
from django.db import transaction
from django.contrib.auth.hashers import make_password
from .models import Usuario, AuthIdentidad, Perfil, RegistroConsumo, AuditoriaEvento
import bcrypt
from .utils.crypto import encrypt_field
from uuid import uuid4
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'aria-label': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'aria-label': 'Apellido'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'aria-label': 'Correo electrónico'}),
        }

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
    


class AdminUpdateUserForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico", required=True)
    nombres = forms.CharField(label="Nombres", max_length=100, required=False)
    apellidos = forms.CharField(label="Apellidos", max_length=100, required=False)
    rut = forms.CharField(label="RUT", max_length=12, required=False)
    password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput, required=False)
    activo = forms.BooleanField(label="Usuario activo", required=False)

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop("usuario")  # instancia de Usuario
        self.identidad = kwargs.pop("identidad")  # instancia de AuthIdentidad
        self.perfil = kwargs.pop("perfil")  # instancia de Perfil (o None)
        super().__init__(*args, **kwargs)
        # iniciales
        self.fields["email"].initial = self.identidad.email
        self.fields["nombres"].initial = getattr(self.perfil, "nombres", "")
        self.fields["apellidos"].initial = getattr(self.perfil, "apellidos", "")
        self.fields["rut"].initial = ""  # seguridad: no mostramos el RUT; si cargamos, sería desencriptando
        self.fields["activo"].initial = bool(self.usuario.activo)

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    @transaction.atomic
    def save(self):
        import bcrypt
        from .utils.crypto import encrypt_field
        from .forms import _rut_hash_hex, _normaliza_rut  # reutilizamos helpers existentes

        # email único (excluir la identidad actual)
        new_email = self.cleaned_data["email"]
        if AuthIdentidad.objects.filter(email__iexact=new_email).exclude(pk=self.identidad.pk).exists():
            self.add_error("email", "Este correo ya está registrado.")
            raise forms.ValidationError("Correo duplicado")

        # actualizar identidad
        self.identidad.email = new_email
        # password opcional
        p1 = self.cleaned_data.get("password1")
        if p1:
            self.identidad.contrasena_hash = bcrypt.hashpw(p1.encode(), bcrypt.gensalt()).decode()
        self.identidad.actualizado_en = timezone.now()
        self.identidad.save()

        # actualizar usuario (activo)
        self.usuario.activo = bool(self.cleaned_data.get("activo"))
        self.usuario.actualizado_en = timezone.now()
        self.usuario.save()

        # actualizar/crear perfil
        rut_plain = _normaliza_rut(self.cleaned_data.get("rut") or "")
        rut_enc = encrypt_field(rut_plain) if rut_plain else None
        rut_hex = _rut_hash_hex(rut_plain) if rut_plain else None

        perfil = self.perfil
        if perfil is None:
            perfil = Perfil(usuario=self.usuario, creado_en=timezone.now())
        # unicidad RUT por hash (excluye actual)
        if rut_hex and Perfil.objects.filter(rut_hash=rut_hex).exclude(usuario=self.usuario).exists():
            self.add_error("rut", "Este RUT ya está registrado.")
            raise forms.ValidationError("RUT duplicado")

        perfil.rut = rut_enc
        perfil.rut_hash = rut_hex
        perfil.nombres = self.cleaned_data.get("nombres") or perfil.nombres
        perfil.apellidos = self.cleaned_data.get("apellidos") or perfil.apellidos
        perfil.actualizado_en = timezone.now()
        perfil.save()
        return self.usuario


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")

class SetNewPasswordForm(forms.Form):
    password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if not p1 or not p2 or p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned
    

class ContactPublicForm(forms.Form):
    nombre = forms.CharField(
        label="Nombre", max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Tu nombre"})
    )
    email = forms.EmailField(
        label="Correo",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "tucorreo@dominio.cl"})
    )
    tipo = forms.ChoiceField(
        label="Motivo",
        choices=[
            ("sugerencia", "Sugerencia"),
            ("reclamo", "Reclamo"),
            ("donacion", "Donación"),
            ("consulta", "Consulta general"),
        ],
        widget=forms.Select(attrs={"class": "form-select"})
    )
    asunto = forms.CharField(
        label="Asunto", max_length=160,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Breve asunto"})
    )
    mensaje = forms.CharField(
        label="Mensaje",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Cuéntanos en detalle"})
    )

    # anti-spam honeypot (campo oculto)
    hp = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_hp(self):
        v = self.cleaned_data.get("hp", "")
        if v:
            raise forms.ValidationError("Spam detectado.")
        return v
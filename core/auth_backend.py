# core/auth_backend.py
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import AuthIdentidad
import bcrypt

logger = logging.getLogger(__name__)
User = get_user_model()

class AuthIdentidadBackend:
    """
    Autentica usando la tabla auth_identidades (AuthIdentidad).
    Si la autenticación es exitosa, crea/actualiza un User de Django con username=email
    (set_unusable_password) para que django.contrib.auth.login() funcione.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        logger.debug("[AUTH BACKEND] authenticate called username=%s", username)
        if not username or not password:
            return None
        try:
            ident = AuthIdentidad.objects.get(email__iexact=username)
        except AuthIdentidad.DoesNotExist:
            logger.debug("[AUTH BACKEND] identidad no encontrada para %s", username)
            return None

        try:
            # bcrypt.checkpw retorna True/False
            ok = bcrypt.checkpw(password.encode(), ident.contrasena_hash.encode())
        except Exception as e:
            logger.exception("[AUTH BACKEND] error comprobando bcrypt: %s", e)
            return None

        if not ok:
            logger.debug("[AUTH BACKEND] password incorrecto para %s", username)
            return None

        # autenticado OK -> actualizar ultimo_acceso
        try:
            ident.ultimo_acceso = timezone.now()
            ident.save(update_fields=["ultimo_acceso"])
        except Exception:
            logger.exception("[AUTH BACKEND] fallo al actualizar ultimo_acceso")

        # Obtener o crear un django User para la sesión
        try:
            user, created = User.objects.get_or_create(
                username=ident.email,
                defaults={"email": ident.email, "is_active": True},
            )
            if created:
                # No guardamos la contraseña real en auth_user: marcamos unusable
                user.set_unusable_password()
                user.save()
                logger.debug("[AUTH BACKEND] Created django.User for %s", ident.email)
            return user
        except Exception as e:
            logger.exception("[AUTH BACKEND] error creando/obteniendo User: %s", e)
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

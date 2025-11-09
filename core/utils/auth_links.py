from django.db import transaction
from core.models import *

@transaction.atomic
def ensure_usuario_for_request(request):
    # Asumo que request.user.email es tu fuente de verdad.
    email = (getattr(request.user, "email", "") or "").strip().lower()
    if not email:
        return None  # o lanza excepción controlada

    identidad = AuthIdentidad.objects.select_related("usuario").filter(email__iexact=email).first()
    if identidad and identidad.usuario:
        return identidad.usuario  # ya existe

    # Si no hay identidad/usuario, los creamos mínimo-viable:
    usuario = Usuario.objects.create()  # genera UUID
    if not identidad:
        identidad = AuthIdentidad.objects.create(usuario=usuario, email=email, contrasena_hash="(external)")
    else:
        identidad.usuario = usuario
        identidad.save(update_fields=["usuario"])
    return usuario

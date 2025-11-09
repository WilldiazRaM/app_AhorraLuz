from django.db import transaction
from django.utils import timezone
from core.models import *

@transaction.atomic
def ensure_usuario_for_request(request):
    email = (getattr(request.user, "email", "") or "").strip().lower()
    if not email:
        return None

    identidad = AuthIdentidad.objects.select_related("usuario").filter(email__iexact=email).first()
    if identidad and identidad.usuario:
        return identidad.usuario

    # ⚠️ Setear campos obligatorios al crear
    usuario = Usuario.objects.create(
        activo=True,
        creado_en=timezone.now(),
        actualizado_en=timezone.now(),
    )

    if not identidad:
        AuthIdentidad.objects.create(
            usuario=usuario,
            email=email,
            contrasena_hash="(external)",
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
        )
    else:
        identidad.usuario = usuario
        identidad.actualizado_en = timezone.now()
        identidad.save(update_fields=["usuario", "actualizado_en"])

    return usuario

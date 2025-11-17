import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import user_passes_test, login_required
from django.urls import reverse
from .forms import *
from .models import *
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Avg
from django.utils import timezone
import logging
from django.core.mail import send_mail
from django.http import Http404
from django.views.decorators.http import require_http_methods
from django.db import transaction
import secrets, hashlib, datetime
import bcrypt
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.http import JsonResponse
from datetime import timedelta
import pytz, numpy as np
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .utils.ml_nowcast import build_row, predict_one
from core.utils.auth_links import ensure_usuario_for_request
from django.db.models import F, FloatField, ExpressionWrapper
from django.db.models.functions import Abs, Cast, NullIf
from django.db.models import F, FloatField, ExpressionWrapper, Avg, Count
import datetime
from .utils.auth_links import ensure_usuario_for_request
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import requests
import logging
from django.core.mail import send_mail
from django.conf import settings
import calendar
from django.db.models.functions import TruncMonth

logger = logging.getLogger("core.views")



def _metricas_precision_queryset(user_id, desde=None, hasta=None):
    from .models import PrediccionConsumo

    qs = PrediccionConsumo.objects.filter(
        usuario__id=user_id,
        consumo_real_kwh__isnull=False,
    )

    if desde:
        qs = qs.filter(periodo_inicio__gte=desde)
    if hasta:
        qs = qs.filter(periodo_fin__lte=hasta)

    # |error| = |real - predicho|
    err = Abs(
        Cast(F("consumo_real_kwh"), FloatField()) -
        Cast(F("consumo_predicho_kwh"), FloatField())
    )

    # (|error|)^2 para RMSE
    err2 = ExpressionWrapper(err * err, output_field=FloatField())

    # MAPE = (|err| / real) * 100 evitando dividir entre 0
    real_nz = NullIf(Cast(F("consumo_real_kwh"), FloatField()), 0.0)
    ape = ExpressionWrapper(err / real_nz * 100.0, output_field=FloatField())

    agg = qs.aggregate(
        n=Count("id"),
        mae=Avg(err),
        rmse=Avg(err2),
        mape=Avg(ape),
    )

    # Convertimos RMSE = sqrt(mean(err^2))
    if agg["rmse"] is not None:
        agg["rmse"] = agg["rmse"] ** 0.5

    return agg







class SoloSuperuserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser
    
# Helpers para context genérico
class GenericList(LoginRequiredMixin, SoloSuperuserMixin, ListView):
    template_name = "mantenedor/includes/crud_list_generic.html"
    paginate_by = 20
    ordering = ["-pk"]
    title = ""
    new_url = ""
    edit_base = ""
    delete_base = ""
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"title": self.title, "new_url": self.new_url, "edit_base": self.edit_base, "delete_base": self.delete_base})
        return ctx

class GenericCreate(LoginRequiredMixin, SoloSuperuserMixin, CreateView):
    template_name = "mantenedor/includes/crud_form_generic.html"
    title = ""
    list_url = ""
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"title": self.title, "list_url": self.list_url})
        return ctx

class GenericUpdate(LoginRequiredMixin, SoloSuperuserMixin, UpdateView):
    template_name = "mantenedor/includes/crud_form_generic.html"
    title = ""
    list_url = ""
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"title": self.title, "list_url": self.list_url})
        return ctx

class GenericDelete(LoginRequiredMixin, SoloSuperuserMixin, DeleteView):
    template_name = "mantenedor/includes/crud_confirm_delete_generic.html"
    title = ""
    list_url = ""
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"title": self.title, "list_url": self.list_url})
        return ctx



class ComunaListView(LoginRequiredMixin, SoloSuperuserMixin, ListView):
    model = Comuna
    template_name = "mantenedor/catalogos/comunas/comuna_list.html"    
    paginate_by = 20
    ordering = ["nombre"]

class ComunaCreateView(LoginRequiredMixin, SoloSuperuserMixin, CreateView):
    model = Comuna
    form_class = ComunaForm
    template_name = "mantenedor/catalogos/comunas/comuna_form.html"
    success_url = reverse_lazy("core:mant_comuna_list")

class ComunaUpdateView(LoginRequiredMixin, SoloSuperuserMixin, UpdateView):
    model = Comuna
    form_class = ComunaForm
    template_name = "mantenedor/catalogos/comunas/comuna_form.html"
    success_url = reverse_lazy("core:mant_comuna_list")

class ComunaDeleteView(LoginRequiredMixin, SoloSuperuserMixin, DeleteView):
    model = Comuna
    template_name = "mantenedor/catalogos/comunas/comuna_confirm_delete.html"
    success_url = reverse_lazy("core:mant_comuna_list")


# ---------- Catálogo: TipoDispositivo ----------
class TipoDispositivoList(GenericList):
    model = TipoDispositivo
    title = "Tipos de dispositivo"
    new_url = reverse_lazy("core:mant_tipodispositivo_new")
    edit_base = reverse_lazy("core:mant_tipodispositivo_edit_base")
    delete_base = reverse_lazy("core:mant_tipodispositivo_delete_base")

class TipoDispositivoCreate(GenericCreate):
    model = TipoDispositivo
    form_class = TipoDispositivoForm
    title = "Nuevo tipo de dispositivo"
    success_url = reverse_lazy("core:mant_tipodispositivo_list")
    list_url = success_url

class TipoDispositivoUpdate(GenericUpdate):
    model = TipoDispositivo
    form_class = TipoDispositivoForm
    title = "Editar tipo de dispositivo"
    success_url = reverse_lazy("core:mant_tipodispositivo_list")
    list_url = success_url

class TipoDispositivoDelete(GenericDelete):
    model = TipoDispositivo
    title = "Eliminar tipo de dispositivo"
    success_url = reverse_lazy("core:mant_tipodispositivo_list")
    list_url = success_url

# TipoVivienda :contentReference[oaicite:16]{index=16}
class TipoViviendaList(GenericList):
    model = TipoVivienda
    title = "Tipos de vivienda"
    new_url = reverse_lazy("core:mant_tipovivienda_new")
    edit_base = reverse_lazy("core:mant_tipovivienda_edit_base")
    delete_base = reverse_lazy("core:mant_tipovivienda_delete_base")

class TipoViviendaCreate(GenericCreate):
    model = TipoVivienda
    form_class = TipoViviendaForm
    title = "Nuevo tipo de vivienda"
    success_url = reverse_lazy("core:mant_tipovivienda_list")
    list_url = success_url

class TipoViviendaUpdate(GenericUpdate):
    model = TipoVivienda
    form_class = TipoViviendaForm
    title = "Editar tipo de vivienda"
    success_url = reverse_lazy("core:mant_tipovivienda_list")
    list_url = success_url

class TipoViviendaDelete(GenericDelete):
    model = TipoVivienda
    title = "Eliminar tipo de vivienda"
    success_url = reverse_lazy("core:mant_tipovivienda_list")
    list_url = success_url

# TipoNotificacion :contentReference[oaicite:17]{index=17}
class TipoNotificacionList(GenericList):
    model = TipoNotificacion
    title = "Tipos de notificación"
    new_url = reverse_lazy("core:mant_tiponotif_new")
    edit_base = reverse_lazy("core:mant_tiponotif_edit_base")
    delete_base = reverse_lazy("core:mant_tiponotif_delete_base")

class TipoNotificacionCreate(GenericCreate):
    model = TipoNotificacion
    form_class = TipoNotificacionForm
    title = "Nuevo tipo de notificación"
    success_url = reverse_lazy("core:mant_tiponotif_list")
    list_url = success_url

class TipoNotificacionUpdate(GenericUpdate):
    model = TipoNotificacion
    form_class = TipoNotificacionForm
    title = "Editar tipo de notificación"
    success_url = reverse_lazy("core:mant_tiponotif_list")
    list_url = success_url

class TipoNotificacionDelete(GenericDelete):
    model = TipoNotificacion
    title = "Eliminar tipo de notificación"
    success_url = reverse_lazy("core:mant_tiponotif_list")
    list_url = success_url

# NivelAlerta :contentReference[oaicite:18]{index=18}
class NivelAlertaList(GenericList):
    model = NivelAlerta
    title = "Niveles de alerta"
    new_url = reverse_lazy("core:mant_nivelalerta_new")
    edit_base = reverse_lazy("core:mant_nivelalerta_edit_base")
    delete_base = reverse_lazy("core:mant_nivelalerta_delete_base")

class NivelAlertaCreate(GenericCreate):
    model = NivelAlerta
    form_class = NivelAlertaForm
    title = "Nuevo nivel de alerta"
    success_url = reverse_lazy("core:mant_nivelalerta_list")
    list_url = success_url

class NivelAlertaUpdate(GenericUpdate):
    model = NivelAlerta
    form_class = NivelAlertaForm
    title = "Editar nivel de alerta"
    success_url = reverse_lazy("core:mant_nivelalerta_list")
    list_url = success_url

class NivelAlertaDelete(GenericDelete):
    model = NivelAlerta
    title = "Eliminar nivel de alerta"
    success_url = reverse_lazy("core:mant_nivelalerta_list")
    list_url = success_url

# Permiso :contentReference[oaicite:19]{index=19}
class PermisoList(GenericList):
    model = Permiso
    title = "Permisos"
    new_url = reverse_lazy("core:mant_permiso_new")
    edit_base = reverse_lazy("core:mant_permiso_edit_base")
    delete_base = reverse_lazy("core:mant_permiso_delete_base")

class PermisoCreate(GenericCreate):
    model = Permiso
    form_class = PermisoForm
    title = "Nuevo permiso"
    success_url = reverse_lazy("core:mant_permiso_list")
    list_url = success_url

class PermisoUpdate(GenericUpdate):
    model = Permiso
    form_class = PermisoForm
    title = "Editar permiso"
    success_url = reverse_lazy("core:mant_permiso_list")
    list_url = success_url

class PermisoDelete(GenericDelete):
    model = Permiso
    title = "Eliminar permiso"
    success_url = reverse_lazy("core:mant_permiso_list")
    list_url = success_url

# Rol :contentReference[oaicite:20]{index=20}
class RolList(GenericList):
    model = Rol
    title = "Roles"
    new_url = reverse_lazy("core:mant_rol_new")
    edit_base = reverse_lazy("core:mant_rol_edit_base")
    delete_base = reverse_lazy("core:mant_rol_delete_base")

class RolCreate(GenericCreate):
    model = Rol
    form_class = RolForm
    title = "Nuevo rol"
    success_url = reverse_lazy("core:mant_rol_list")
    list_url = success_url

class RolUpdate(GenericUpdate):
    model = Rol
    form_class = RolForm
    title = "Editar rol"
    success_url = reverse_lazy("core:mant_rol_list")
    list_url = success_url

class RolDelete(GenericDelete):
    model = Rol
    title = "Eliminar rol"
    success_url = reverse_lazy("core:mant_rol_list")
    list_url = success_url

class TipoDispositivoListView(LoginRequiredMixin, SoloSuperuserMixin, ListView):
    model = TipoDispositivo
    template_name = "mantenedor/catalogos/tipos_dispositivo/tipo_dispositivo_list.html"
    paginate_by = 20
    ordering = ["nombre"]

class TipoDispositivoCreateView(LoginRequiredMixin, SoloSuperuserMixin, CreateView):
    model = TipoDispositivo
    form_class = TipoDispositivoForm
    template_name = "mantenedor/catalogos/tipos_dispositivo/tipo_dispositivo_form.html"
    success_url = reverse_lazy("core:mant_tipodispositivo_list")

class TipoDispositivoUpdateView(LoginRequiredMixin, SoloSuperuserMixin, UpdateView):
    model = TipoDispositivo
    form_class = TipoDispositivoForm
    template_name = "mantenedor/catalogos/tipos_dispositivo/tipo_dispositivo_form.html"
    success_url = reverse_lazy("core:mant_tipodispositivo_list")

class TipoDispositivoDeleteView(LoginRequiredMixin, SoloSuperuserMixin, DeleteView):
    model = TipoDispositivo
    template_name = "mantenedor/catalogos/tipos_dispositivo/tipo_dispositivo_confirm_delete.html"
    success_url = reverse_lazy("core:mant_tipodispositivo_list")


# ---------- Operativo: Dispositivo ----------
class DispositivoList(GenericList):
    model = Dispositivo
    title = "Dispositivos"
    new_url = reverse_lazy("core:mant_dispositivo_new")
    edit_base = reverse_lazy("core:mant_dispositivo_edit_base")
    delete_base = reverse_lazy("core:mant_dispositivo_delete_base")

class DispositivoCreate(GenericCreate):
    model = Dispositivo
    form_class = DispositivoForm
    title = "Nuevo dispositivo"
    success_url = reverse_lazy("core:mant_dispositivo_list")
    list_url = success_url

class DispositivoUpdate(GenericUpdate):
    model = Dispositivo
    form_class = DispositivoForm
    title = "Editar dispositivo"
    success_url = reverse_lazy("core:mant_dispositivo_list")
    list_url = success_url

class DispositivoDelete(GenericDelete):
    model = Dispositivo
    title = "Eliminar dispositivo"
    success_url = reverse_lazy("core:mant_dispositivo_list")
    list_url = success_url

# Direccion :contentReference[oaicite:22]{index=22}
class DireccionList(GenericList):
    model = Direccion
    title = "Direcciones"
    new_url = reverse_lazy("core:mant_direccion_new")
    edit_base = reverse_lazy("core:mant_direccion_edit_base")
    delete_base = reverse_lazy("core:mant_direccion_delete_base")

class DireccionCreate(GenericCreate):
    model = Direccion
    form_class = DireccionForm
    title = "Nueva dirección"
    success_url = reverse_lazy("core:mant_direccion_list")
    list_url = success_url

class DireccionUpdate(GenericUpdate):
    model = Direccion
    form_class = DireccionForm
    title = "Editar dirección"
    success_url = reverse_lazy("core:mant_direccion_list")
    list_url = success_url

class DireccionDelete(GenericDelete):
    model = Direccion
    title = "Eliminar dirección"
    success_url = reverse_lazy("core:mant_direccion_list")
    list_url = success_url

# RegistroConsumo (modo admin) :contentReference[oaicite:23]{index=23}
class RegistroConsumoList(GenericList):
    model = RegistroConsumo
    title = "Registros de consumo"
    new_url = reverse_lazy("core:mant_registroconsumo_new")
    edit_base = reverse_lazy("core:mant_registroconsumo_edit_base")
    delete_base = reverse_lazy("core:mant_registroconsumo_delete_base")

class RegistroConsumoCreate(GenericCreate):
    model = RegistroConsumo
    form_class = RegistroConsumoAdminForm
    title = "Nuevo registro de consumo"
    success_url = reverse_lazy("core:mant_registroconsumo_list")
    list_url = success_url

class RegistroConsumoUpdate(GenericUpdate):
    model = RegistroConsumo
    form_class = RegistroConsumoAdminForm
    title = "Editar registro de consumo"
    success_url = reverse_lazy("core:mant_registroconsumo_list")
    list_url = success_url

class RegistroConsumoDelete(GenericDelete):
    model = RegistroConsumo
    title = "Eliminar registro de consumo"
    success_url = reverse_lazy("core:mant_registroconsumo_list")
    list_url = success_url

# Notificacion :contentReference[oaicite:24]{index=24}
class NotificacionList(GenericList):
    model = Notificacion
    title = "Notificaciones"
    new_url = reverse_lazy("core:mant_notificacion_new")
    edit_base = reverse_lazy("core:mant_notificacion_edit_base")
    delete_base = reverse_lazy("core:mant_notificacion_delete_base")

class NotificacionCreate(GenericCreate):
    model = Notificacion
    form_class = NotificacionForm
    title = "Nueva notificación"
    success_url = reverse_lazy("core:mant_notificacion_list")
    list_url = success_url

class NotificacionUpdate(GenericUpdate):
    model = Notificacion
    form_class = NotificacionForm
    title = "Editar notificación"
    success_url = reverse_lazy("core:mant_notificacion_list")
    list_url = success_url

class NotificacionDelete(GenericDelete):
    model = Notificacion
    title = "Eliminar notificación"
    success_url = reverse_lazy("core:mant_notificacion_list")
    list_url = success_url

# PrediccionConsumo :contentReference[oaicite:25]{index=25}
class PrediccionConsumoList(GenericList):
    model = PrediccionConsumo
    title = "Predicciones de consumo"
    new_url = reverse_lazy("core:mant_prediccion_new")
    edit_base = reverse_lazy("core:mant_prediccion_edit_base")
    delete_base = reverse_lazy("core:mant_prediccion_delete_base")

class PrediccionConsumoCreate(GenericCreate):
    model = PrediccionConsumo
    form_class = PrediccionConsumoForm
    title = "Nueva predicción de consumo"
    success_url = reverse_lazy("core:mant_prediccion_list")
    list_url = success_url

class PrediccionConsumoUpdate(GenericUpdate):
    model = PrediccionConsumo
    form_class = PrediccionConsumoForm
    title = "Editar predicción de consumo"
    success_url = reverse_lazy("core:mant_prediccion_list")
    list_url = success_url

class PrediccionConsumoDelete(GenericDelete):
    model = PrediccionConsumo
    title = "Eliminar predicción de consumo"
    success_url = reverse_lazy("core:mant_prediccion_list")
    list_url = success_url


class DispositivoListView(LoginRequiredMixin, SoloSuperuserMixin, ListView):
    model = Dispositivo
    template_name = "mantenedor/operativo/dispositivos/dispositivo_list.html"
    paginate_by = 20
    ordering = ["-id"]

class DispositivoCreateView(LoginRequiredMixin, SoloSuperuserMixin, CreateView):
    model = Dispositivo
    form_class = DispositivoForm
    template_name = "mantenedor/operativo/dispositivos/dispositivo_form.html"
    success_url = reverse_lazy("core:mant_dispositivo_list")

class DispositivoUpdateView(LoginRequiredMixin, SoloSuperuserMixin, UpdateView):
    model = Dispositivo
    form_class = DispositivoForm
    template_name = "mantenedor/operativo/dispositivos/dispositivo_form.html"
    success_url = reverse_lazy("core:mant_dispositivo_list")

class DispositivoDeleteView(LoginRequiredMixin, SoloSuperuserMixin, DeleteView):
    model = Dispositivo
    template_name = "mantenedor/operativo/dispositivos/dispositivo_confirm_delete.html"
    success_url = reverse_lazy("core:mant_dispositivo_list")




# ---------- Solo lectura: Auditoría ----------
class AuditoriaEventoListView(LoginRequiredMixin, SoloSuperuserMixin, ListView):
    model = AuditoriaEvento
    template_name = "mantenedor/solo_lectura/auditoria_eventos/auditoriaevento_list.html"
    paginate_by = 30
    ordering = ["-ocurrido_en"]

class AuditoriaEventoDetailView(LoginRequiredMixin, SoloSuperuserMixin, DetailView):
    model = AuditoriaEvento
    template_name = "mantenedor/solo_lectura/auditoria_eventos/auditoriaevento_detail.html"






logger = logging.getLogger(__name__)


def index(request):
    return render(request, "core/home.html", {})

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('core:dashboard')
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def dashboard(request):
    # Obtener el Usuario energético (UUID) asociado al user de Django
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        messages.error(request, "No se encontró tu registro de usuario en AhorraLuz.")
        return redirect("core:profile")

    # Últimos registros de consumo del usuario
    registros = RegistroConsumo.objects.filter(
        usuario=usuario
    ).order_by("-fecha")[:10]

    # Métricas de precisión de los últimos 90 días
    desde = timezone.now().date() - datetime.timedelta(days=90)
    met = _metricas_precision_queryset(usuario.id, desde=desde)

    context = {
        "title": "Dashboard AhorraLuz",
        "registros": registros,
        "metrics": met,
        "metrics_window_days": 90,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def profile_view(request):
    """
    Mostrar y editar datos básicos del usuario autenticado.
    Usa UserProfileForm que edita first_name, last_name, email.
    Además permite guardar comuna y dirección (modelo Direccion).
    """
    user = request.user
    # Usuario lógico de la app (tabla usuarios)
    usuario = ensure_usuario_for_request(request)

    # Comunas para el dropdown
    comunas = Comuna.objects.order_by("nombre")

    # Dirección actual (si existe)
    direccion = None
    if usuario:
        direccion = (
            Direccion.objects
            .filter(usuario=usuario)
            .select_related("comuna")
            .order_by("-creado_en")
            .first()
        )

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            with transaction.atomic():
                # 1) Guardar datos básicos del User
                form.save()

                # 2) Guardar comuna y dirección en Direccion
                if usuario:
                    comuna_id = request.POST.get("comuna_id") or None
                    texto_dir = (request.POST.get("direccion") or "").strip()

                    comuna = None
                    if comuna_id:
                        try:
                            comuna = Comuna.objects.get(pk=comuna_id)
                        except Comuna.DoesNotExist:
                            comuna = None

                    from django.utils import timezone

                    if direccion:
                        # Actualizar registro existente
                        direccion.calle = texto_dir or direccion.calle
                        direccion.comuna = comuna
                        direccion.actualizado_en = timezone.now()
                        direccion.save()
                    else:
                        # Crear nueva dirección solo si hay algo que guardar
                        if texto_dir or comuna:
                            Direccion.objects.create(
                                usuario=usuario,
                                calle=texto_dir or "",
                                comuna=comuna,
                                creado_en=timezone.now(),
                                actualizado_en=timezone.now(),
                            )

            messages.success(request, "Perfil actualizado correctamente.")
            logger.info("[PROFILE] Usuario %s actualizó su perfil", user.username)
            return redirect("core:profile")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
            logger.debug("[PROFILE] Errores en formulario: %s", form.errors.as_json())
    else:
        form = UserProfileForm(instance=user)

    return render(
        request,
        "core/profile.html",
        {
            "form": form,
            "user": user,
            "comunas": comunas,
            "direccion": direccion,
        },
    )


@login_required
def consumo_new(request):
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        messages.error(request, "No se encontró tu perfil de usuario interno.")
        return redirect("core:profile")

    if request.method == "POST":
        form = RegistroConsumoForm(request.POST)
        if form.is_valid():
            rc = form.save(commit=False)
            rc.usuario = usuario
            rc.creado_en = timezone.now()

            # --- Validar que no haya otra lectura ese MES ---
            existe_mes = RegistroConsumo.objects.filter(
                usuario=usuario,
                fecha__year=rc.fecha.year,
                fecha__month=rc.fecha.month,
            ).exists()
            if existe_mes:
                form.add_error(
                    "fecha",
                    "Ya registraste una lectura de boleta para este mes. "
                    "Si necesitas corregirla, edítala desde el historial."
                )
                return render(request, "core/consumo_form.html", {"form": form})

            # (opcional) validar pertenencia de dispositivo, igual que en consumo_new_and_predict
            if rc.dispositivo_id:
                pertenece = Dispositivo.objects.filter(
                    id=rc.dispositivo_id, usuario=usuario
                ).exists()
                if not pertenece:
                    form.add_error("dispositivo", "El dispositivo no pertenece a tu cuenta.")
                    return render(request, "core/consumo_form.html", {"form": form})

            rc.save()

            # --- Generar predicción, notificación y correo ---
            temp_c = form.cleaned_data.get("temp_c")
            try:
                _crear_prediccion_y_alerta_para_registro(
                    request=request,
                    usuario=usuario,
                    rc=rc,
                    temp_c=temp_c,
                )
            except Exception as e:
                logger.exception(
                    "[CONSUMO_NEW] Error generando predicción para registro %s: %s",
                    rc.id,
                    e,
                )
                # no rompemos el flujo del usuario, solo registramos en logs

            messages.success(
                request,
                "✅ Lectura registrada. "
                "Hemos generado una predicción para tu consumo y, si corresponde, una alerta."
            )
            return redirect("core:consumo_history")
    else:
        form = RegistroConsumoForm()

    return render(request, "core/consumo_form.html", {"form": form})

@login_required
def consumo_history(request):
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        messages.error(request, "No se encontró tu registro de usuario en AhorraLuz.")
        return redirect("core:profile")

    qs = RegistroConsumo.objects.filter(
        usuario=usuario
    ).order_by("-fecha")[:100]

    return render(request, "core/consumo_history.html", {"registros": qs})



@login_required
@user_passes_test(lambda u: u.is_superuser)
def register_user_admin(request):
    if request.method == "POST":
        form = AdminRegisterUserForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            messages.success(request, "✅ Usuario registrado exitosamente.")
            return redirect("core:home")
        else:
            messages.error(request, "⚠️ Revisa los datos ingresados.")
    else:
        form = AdminRegisterUserForm()
    return render(request, "mantenedor/admin/register_user.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_users_list(request):
    q = request.GET.get("q", "").strip()
    identidades = AuthIdentidad.objects.select_related("usuario").order_by("-creado_en")
    if q:
        identidades = identidades.filter(
            Q(email__icontains=q) |
            Q(usuario__id__icontains=q)
        )
    paginator = Paginator(identidades, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    # mapeo de perfiles por usuario (evita N+1 grande)
    perfiles = {p.usuario_id: p for p in Perfil.objects.filter(usuario__in=[i.usuario for i in page_obj])}
    context = {"page_obj": page_obj, "perfiles": perfiles, "q": q}
    return render(request, "mantenedor/admin/listar_users.html", context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_user_update(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    identidad = get_object_or_404(AuthIdentidad, usuario=usuario)
    perfil = Perfil.objects.filter(usuario=usuario).first()

    if request.method == "POST":
        form = AdminUpdateUserForm(request.POST, usuario=usuario, identidad=identidad, perfil=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Usuario actualizado.")
            return redirect("core:admin_users_list")
        messages.error(request, "⚠️ Revisa los datos.")
    else:
        form = AdminUpdateUserForm(usuario=usuario, identidad=identidad, perfil=perfil)

    return render(request, "mantenedor/admin/update_users.html", {"form": form, "usuario": usuario})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_user_deactivate(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    if request.method == "POST":
        usuario.activo = False
        usuario.actualizado_en = timezone.now()
        usuario.save()
        messages.info(request, "🛑 Usuario desactivado.")
        return redirect("core:admin_users_list")
    return render(request, "mantenedor/admin/remove_users.html", {"usuario": usuario, "mode": "deactivate"})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_user_delete(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    if request.method == "POST":
        # eliminación dura: borra dependencias (perfil, identidad); si prefieres soft-delete, usa admin_user_deactivate
        Perfil.objects.filter(usuario=usuario).delete()
        AuthIdentidad.objects.filter(usuario=usuario).delete()
        usuario.delete()
        messages.warning(request, "🗑️ Usuario eliminado definitivamente.")
        return redirect("core:admin_users_list")
    return render(request, "mantenedor/admin/remove_users.html", {"usuario": usuario, "mode": "delete"})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_user_reset_password(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    identidad = get_object_or_404(AuthIdentidad, usuario=usuario)
    if request.method == "POST":
        new = request.POST.get("password1", "").strip()
        confirm = request.POST.get("password2", "").strip()
        if new and new == confirm:
            import bcrypt
            identidad.contrasena_hash = bcrypt.hashpw(new.encode(), bcrypt.gensalt()).decode()
            identidad.actualizado_en = timezone.now()
            identidad.save()
            messages.success(request, "🔑 Contraseña actualizada.")
            return redirect("core:admin_users_list")
        messages.error(request, "⚠️ Las contraseñas no coinciden.")
    return render(request, "mantenedor/admin/update_users.html", {"reset_mode": True, "usuario": usuario})


# --- Solicitud de reset (pide email y envía link) ---
def password_reset_request_view(request):
    form = PasswordResetRequestForm(request.POST or None)

    # GET: solo mostrar el formulario
    if request.method == "GET":
        return render(request, "registration/password_reset_request.html", {"form": form})

    # POST: procesar
    if form.is_valid():
        email = form.cleaned_data["email"].strip().lower()

        # Mensaje siempre igual para no filtrar existencia
        msg_ok = "Si el correo existe, te enviaremos un enlace para restablecer la contraseña."
        try:
            identidad = AuthIdentidad.objects.get(email__iexact=email)
        except AuthIdentidad.DoesNotExist:
            messages.info(request, msg_ok)
            return redirect("core:password_reset_request")

        # Generar token y guardar hash
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expira = timezone.now() + datetime.timedelta(minutes=settings.PASSWORD_RESET_MINUTES)

        PasswordResetToken.objects.create(
            identidad=identidad,
            token_hash=token_hash,
            expira_en=expira,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )

        # Construir reset_link y correo HTML + texto
        reset_link = f"{settings.SITE_URL}{reverse('core:password_reset_confirm')}?token={raw_token}"
        subject = "Restablecer tu contraseña – AhorraLuz"
        ctx = {
            "minutes": settings.PASSWORD_RESET_MINUTES,
            "reset_link": reset_link,
            "now": timezone.now(),
        }
        html = render_to_string("emails/password_reset.html", ctx)
        text = strip_tags(html)

        try:
            send_mail(
                subject,
                text,  # fallback texto
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
                html_message=html,
            )
        except Exception as e:
            # No revelar detalles al usuario
            import logging
            logger = logging.getLogger("core.views")
            logger.exception("[RESET] Error enviando correo: %s", e)

        messages.info(request, msg_ok)
        return redirect("core:password_reset_request")

    # POST con errores de validación → re-render del form
    return render(request, "registration/password_reset_request.html", {"form": form})


# --- Confirmación de reset (valida token y setea nueva clave) ---
@require_http_methods(["GET", "POST"])
@transaction.atomic
def password_reset_confirm_view(request):
    raw_token = request.GET.get("token") or request.POST.get("token")
    if not raw_token:
        raise Http404("Token faltante")

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    try:
        prt = PasswordResetToken.objects.select_related("identidad").get(token_hash=token_hash)
    except PasswordResetToken.DoesNotExist:
        raise Http404("Token inválido")

    # válido: no usado y no expirado
    now = timezone.now()
    if prt.usado_en or prt.expira_en < now:
        messages.error(request, "El enlace ya fue usado o expiró. Solicita uno nuevo.")
        return redirect("core:password_reset_request")

    form = SetNewPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        new_pw = form.cleaned_data["password1"]
        # Actualiza hash bcrypt en AuthIdentidad
        identidad = prt.identidad
        identidad.contrasena_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
        identidad.actualizado_en = now
        identidad.save()

        # Marca usado, e invalida otros tokens activos de este usuario
        prt.usado_en = now
        prt.save(update_fields=["usado_en"])
        PasswordResetToken.objects.filter(
            identidad=identidad, usado_en__isnull=True, expira_en__gte=now
        ).exclude(pk=prt.pk).update(usado_en=now)

        messages.success(request, "Tu contraseña fue actualizada. Ya puedes iniciar sesión.")
        return redirect("core:login")

    return render(request, "registration/password_reset_confirm.html", {"form": form, "token": raw_token})



def contact_public_view(request):
    """
    Formulario de contacto público (empresas/personas).
    Envía correo a CONTACT_RECIPIENT o DEFAULT_FROM_EMAIL.
    """
    if request.method == "POST":
        form = ContactPublicForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            to_addr = os.environ.get("CONTACT_RECIPIENT") or settings.DEFAULT_FROM_EMAIL
            subject = f"[Contacto AhorraLuz] {data['tipo'].capitalize()} – {data['asunto']}"

            html = render_to_string("emails/contact_public.html", {
                "nombre": data["nombre"],
                "email": data["email"],
                "tipo": data["tipo"],
                "asunto": data["asunto"],
                "mensaje": data["mensaje"],
                "now": timezone.now(),
                "site_url": settings.SITE_URL,
            })
            text = strip_tags(html)

            # puedes agregar BCC opcional vía env
            bcc = []
            if os.environ.get("CONTACT_NOTIFY_BCC"):
                bcc = [addr.strip() for addr in os.environ["CONTACT_NOTIFY_BCC"].split(",") if addr.strip()]

            send_mail(
                subject,
                text,
                settings.DEFAULT_FROM_EMAIL,  # From verificado (SendGrid)
                [to_addr],
                fail_silently=False,
                html_message=html,
            )
            messages.success(request, "Gracias por escribirnos. Te contactaremos pronto.")
            return redirect("core:contacto")
    else:
        form = ContactPublicForm()

    return render(request, "contacto.html", {"form": form})




def _default_signals():
    return {
        "Global_reactive_power": 0.3,
        "Voltage": 230.0,
        "Global_intensity": 12.0,
        "Sub_metering_1": 0.1,
        "Sub_metering_2": 0.1,
        "Sub_metering_3": 0.3,
        "other_kwh_h": 0.2
    }

# === Calendario: SOLO las columnas que están en features.json
def _calendar_feats(dt_local):
    dow = dt_local.weekday()
    return {
        "Month": dt_local.month,
        "DayOfWeek": dow,
        "Hour": dt_local.hour,
        "Is_Weekday": int(dow < 5),
        # OJO: tu modelo actual NO usa Is_Holiday ni Is_DST (no están en features.json)
    }

# === Clima placeholder (más adelante reemplazamos por DMC/Meteostat/CR2)
def _climate_stub(_dt_local):
    return {"Temp_C": 14.0}



def _signals_from_dispositivos(usuario):
    """
    Calcula señales agregadas a partir de los dispositivos del usuario.
    Si no hay dispositivos activos, usa el default.
    """
    dispositivos = Dispositivo.objects.filter(usuario=usuario, activo=True)
    if not dispositivos.exists():
        return _default_signals()

    sub1 = sub2 = sub3 = other = 0.0
    total_kw_h = 0.0  # kWh por hora (aprox)

    for d in dispositivos:
        pot_w = float(d.potencia_promedio_w or 0.0)
        horas = float(d.horas_uso_diario or 0.0)

        # kWh consumidos en un día por este dispositivo
        # Ej: 500 W * 6 h = 3000 Wh = 3 kWh/día
        kwh_dia = pot_w * horas / 1000.0 if horas > 0 else 0.0

        # Promedio por hora repartido en las 24 h del día
        # Ej: 3 kWh/día / 24 ≈ 0.125 kWh/h
        kwh_prom_h = kwh_dia / 24.0

        # Clasificación muy simple por tipo
        tipo = (d.tipo_dispositivo.nombre or "").lower()
        nombre = (d.nombre or "").lower()

        if any(k in tipo for k in ["lavadora", "secadora", "lavavaj", "cocina", "horno", "microondas", "hervidor"]):
            sub1 += kwh_prom_h
        elif any(k in tipo for k in ["calefactor", "aire acondicionado", "termovent", "deshumidificador"]):
            sub2 += kwh_prom_h
        elif any(k in tipo for k in ["iluminación", "foco", "lámpara", "router", "modem", "consola", "tv", "televisor", "notebook", "computador"]):
            sub3 += kwh_prom_h
        else:
            other += kwh_prom_h

        total_kw_h += kwh_prom_h

    # En Chile asumimos ~230V monofásico
    voltage = 230.0
    intensity = (total_kw_h * 1000.0 / voltage) if voltage > 0 else 0.0

    return {
        "Global_reactive_power": round(total_kw_h * 0.2, 4),  # factor cos φ ~0.8 aprox
        "Voltage": voltage,
        "Global_intensity": round(intensity, 4),
        "Sub_metering_1": round(sub1, 4),
        "Sub_metering_2": round(sub2, 4),
        "Sub_metering_3": round(sub3, 4),
        "other_kwh_h": round(other, 4),
    }


def _climate_from_api(dt_local):
    """
    Consulta una API pública (Open-Meteo) para obtener la temperatura en °C.
    Por simplicidad, usamos coordenadas de Santiago.
    """
    try:
        base_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": -33.45,
            "longitude": -70.66,
            "hourly": "temperature_2m",
            "timezone": "America/Santiago",
        }
        r = requests.get(base_url, params=params, timeout=3)
        r.raise_for_status()
        data = r.json()
        temps = data.get("hourly", {}).get("temperature_2m", [])
        times = data.get("hourly", {}).get("time", [])

        # Buscar la hora más cercana a dt_local
        if not temps or not times:
            return _climate_stub(dt_local)

        target = dt_local.replace(minute=0, second=0, microsecond=0).isoformat()
        if target in times:
            idx = times.index(target)
            return {"Temp_C": float(temps[idx])}

        # Si no existe esa exacta, toma la primera
        return {"Temp_C": float(temps[0])}
    except Exception:
        # Fallback silencioso
        return _climate_stub(dt_local)

@login_required
def api_predict_next_24h(request):
    """
    Predicción de las próximas 24h:
    - Usa los dispositivos registrados del usuario para armar las señales.
    - Usa calendario local Chile (America/Santiago).
    - Usa clima stub (o API en el futuro).
    - Devuelve nivel de alerta + mensaje corto.
    """
    tz = pytz.timezone("America/Santiago")
    now_utc = timezone.now()
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        return JsonResponse(
            {"error": "No se encontró tu perfil de usuario energético."},
            status=400
        )

    # Baseline del usuario (kWh/día)
    baseline = _user_baseline_kwh(usuario, ref_dt=now_utc.date())

    # Señales en base a dispositivos activos
    signals = _signals_from_dispositivos(usuario)

    predicciones = []
    total_kwh = 0.0

    for h in range(1, 25):
        ts_local = (now_utc + timedelta(hours=h)).astimezone(tz)

        row = build_row(
            signals=signals,
            calendar=_calendar_feats(ts_local),
            climate=_climate_stub(ts_local)  # o _climate_from_api(ts_local) si lo activas
        )
        kwh = predict_one(row)
        total_kwh += kwh

        predicciones.append({
            "timestamp_local": ts_local.isoformat(),
            "kwh": round(kwh, 3),
        })

    
    nivel, mensaje_alerta, ratio = _classify_alert(total_kwh, baseline)

    resp = {
        "kwh_total_24h": round(total_kwh, 3),
        "consumo_promedio_h": round(total_kwh / 24.0, 3),
        "nivel_alerta": getattr(nivel, "codigo", str(nivel)),
        "mensaje_alerta": mensaje_alerta,
        "ratio_vs_baseline": ratio,
        "predicciones": predicciones,
    }
    return JsonResponse(resp)


@login_required
def api_predict_monthly(request):
    """
    Predicción de consumo mensual estimada a partir de:
      - Dispositivos activos del usuario
      - Modelo de 24h (se escala por días del mes actual)
    Guarda la predicción en PrediccionConsumo para uso posterior (ETL).
    """
    tz = pytz.timezone("America/Santiago")
    now_utc = timezone.now()
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        return JsonResponse(
            {"error": "No se encontró tu perfil de usuario energético."},
            status=400
        )

    # 1) Predicción 24h con el mismo esquema que la API actual
    signals = _signals_from_dispositivos(usuario)
    total_kwh_24h = 0.0

    for h in range(1, 25):
        ts_local = (now_utc + timedelta(hours=h)).astimezone(tz)
        row = build_row(
            signals=signals,
            calendar=_calendar_feats(ts_local),
            climate=_climate_stub(ts_local),
        )
        total_kwh_24h += predict_one(row)

    # 2) Escalamos al mes actual
    hoy = timezone.localdate()
    dias_mes = _days_in_month(hoy)
    kwh_mes = total_kwh_24h * dias_mes
    kwh_dia = kwh_mes / dias_mes if dias_mes > 0 else 0.0

    # 3) Baseline mensual del usuario
    baseline_mes = _user_monthly_baseline_kwh(usuario, ref_dt=hoy)

    # 4) Clasificación y mensaje
    nivel_code, mensaje_alerta, ratio_user = _classify_alert_monthly(kwh_mes, baseline_mes)

    # 5) Guardar predicción mensual en BD para ETL
    try:
        _crear_prediccion_mensual(usuario, hoy, kwh_mes, nivel_code)
    except Exception as e:
        logger.exception("[PRED_MENSUAL] Error guardando predicción mensual: %s", e)

    resp = {
        "month_label": hoy.strftime("%B %Y"),
        "days_in_month": dias_mes,
        "kwh_total_month": round(kwh_mes, 2),
        "kwh_daily": round(kwh_dia, 2),
        "nivel_alerta": nivel_code,
        "mensaje_alerta": mensaje_alerta,
        "ratio_vs_own_baseline": ratio_user,
        "from_24h_kwh": round(total_kwh_24h, 3),
    }
    return JsonResponse(resp)






# === NOWCAST: helpers === PREDICTS TEST 1


def _get_or_create_nivel_alerta(codigo: str, descripcion: str) -> NivelAlerta:
    obj, _ = NivelAlerta.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion})
    return obj

def _get_or_create_tipo_notificacion(codigo: str, descripcion: str) -> TipoNotificacion:
    obj, _ = TipoNotificacion.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion})
    return obj

def _crear_prediccion_mensual(usuario, fecha_referencia, kwh_mes, nivel_code):
    """
    Guarda una predicción mensual en PrediccionConsumo para ETL:
      periodo_inicio = primer día del mes
      periodo_fin    = último día del mes
    """
    from .models import PrediccionConsumo, NivelAlerta, TipoNotificacion, Notificacion

    # Rango del mes
    dias_mes = _days_in_month(fecha_referencia)
    mes_inicio = fecha_referencia.replace(day=1)
    mes_fin = fecha_referencia.replace(day=dias_mes)

    desc_map = {
        "VERDE": "Consumo mensual dentro de un rango esperado.",
        "AMARILLO": "Consumo mensual moderadamente alto.",
        "ROJO": "Consumo mensual alto.",
    }
    nivel = _get_or_create_nivel_alerta(
        nivel_code,
        desc_map.get(nivel_code, "Alerta de consumo mensual."),
    )

    pred = PrediccionConsumo.objects.create(
        usuario=usuario,
        fecha_prediccion=timezone.localdate(),
        periodo_inicio=mes_inicio,
        periodo_fin=mes_fin,
        consumo_predicho_kwh=kwh_mes,
        nivel_alerta=nivel,
        creado_en=timezone.now(),
    )

    # Tipo de notificación y mensaje cortito
    tipo = _get_or_create_tipo_notificacion(
        "PRED_MENSUAL",
        "Predicción mensual de consumo energético",
    )
    mensaje_notif = (
        f"Para el mes {mes_inicio.strftime('%B %Y')}, se estima un consumo de "
        f"≈{kwh_mes:.0f} kWh. Nivel de alerta: {nivel_code or 'SIN ALERTA'}."
    )
    Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo="Predicción mensual de consumo",
        mensaje=mensaje_notif,
        leida=False,
        creada_en=timezone.now(),
    )

    return pred


def _user_baseline_kwh(usuario, ref_dt):
    """Media de los últimos 7 días; si no hay datos, usa media de últimos 5 registros; si no, 1.0 kWh."""
    q = RegistroConsumo.objects.filter(usuario=usuario, fecha__gte=ref_dt - timedelta(days=7), fecha__lte=ref_dt)
    avg = q.aggregate(x=Avg("consumo_kwh"))["x"]
    if avg is None:
        q2 = RegistroConsumo.objects.filter(usuario=usuario).order_by("-fecha")[:5]
        avg = q2.aggregate(x=Avg("consumo_kwh"))["x"]
    return float(avg or 1.0)

# === Helpers para predicción mensual ===

def _days_in_month(dt):
    """Cantidad de días del mes de la fecha dt."""
    return calendar.monthrange(dt.year, dt.month)[1]


def _user_monthly_baseline_kwh(usuario, ref_dt):
    """
    Consumo mensual promedio del usuario (kWh/mes):

    - Promedio de los últimos 6 meses (agrupando por mes).
    - Si no hay suficientes datos, usa el promedio global de sus registros.
    """
    qs = (
        RegistroConsumo.objects
        .filter(usuario=usuario)
        .annotate(mes=TruncMonth("fecha"))
        .values("mes")
        .annotate(kwh_mes=Avg("consumo_kwh"))
        .order_by("-mes")
    )

    ultimos = list(qs[:6])
    if ultimos:
        prom = sum(float(x["kwh_mes"] or 0.0) for x in ultimos) / len(ultimos)
        return max(prom, 1.0)

    prom_global = RegistroConsumo.objects.filter(usuario=usuario).aggregate(
        x=Avg("consumo_kwh")
    )["x"]
    return float(prom_global or 1.0)


def _classify_alert_monthly(total_kwh_mes: float, baseline_kwh_mes: float | None):
    """
    Clasificación para predicción mensual.

    Devuelve:
      - nivel_code ('VERDE', 'AMARILLO', 'ROJO')
      - mensaje_alerta (texto para el usuario)
      - ratio_user (total_kwh_mes / baseline_mes_usuario)
    """
    baseline_user = float(baseline_kwh_mes or 1.0)
    baseline_user = max(baseline_user, 1.0)

    ratio_user = total_kwh_mes / baseline_user

    # Umbrales aproximados, ajústalos luego:
    # Hogar chileno ~ 7 kWh/día ≈ 210 kWh/mes
    if total_kwh_mes <= 180:
        nivel = "VERDE"
    elif total_kwh_mes <= 300:
        nivel = "AMARILLO"
    else:
        nivel = "ROJO"

    if ratio_user >= 5:
        detalle_user = "más de 5× tu promedio mensual reciente"
    elif ratio_user <= 0.5:
        detalle_user = "por debajo de tu promedio mensual"
    else:
        detalle_user = f"{(ratio_user - 1) * 100:.0f}% sobre tu promedio mensual"

    mensaje = (
        f"Consumo estimado del mes: {total_kwh_mes:.2f} kWh. "
        f"Esto es {detalle_user}. "
        "Revisa horarios de uso de artefactos intensivos (calefacción, cocina eléctrica, "
        "lavadora/secadora) para reducir el gasto."
    )

    return nivel, mensaje, ratio_user


NATIONAL_DAILY_KWH = 7.0  # kWh/día

def _classify_alert(total_kwh: float, baseline_kwh: float | None):
    """
    Devuelve:
      - nivel ('VERDE', 'AMARILLO', 'ROJO')  -> string simple o luego mapeable a NivelAlerta
      - mensaje_alerta (string listo para mostrar al usuario)
      - ratio_user (total_kwh / baseline_user) para mostrar % vs su propio promedio
    El mensaje viene contextualizado con hogar promedio en Chile.
    """
    # baseline del usuario (histórico). Si es muy chico, usamos 1 kWh para no explotar el %.
    baseline_user = float(baseline_kwh or 1.0)
    baseline_user = max(baseline_user, 1.0)

    # Comparación contra el propio usuario
    ratio_user = total_kwh / baseline_user

    # Comparación contra hogar promedio Chile
    ratio_cl = total_kwh / NATIONAL_DAILY_KWH if NATIONAL_DAILY_KWH > 0 else 1.0

    # Clasificación del nivel por consumo absoluto (ajusta umbrales a gusto)
    if total_kwh <= 5:
        nivel = "VERDE"
    elif total_kwh <= 15:
        nivel = "AMARILLO"
    else:
        nivel = "ROJO"

    # Texto “bonito” para el % vs su propio promedio
    if ratio_user >= 5:
        detalle_user = "más de 5× tu promedio reciente"
    elif ratio_user <= 0.5:
        detalle_user = "por debajo de tu promedio"
    else:
        detalle_user = f"{(ratio_user - 1) * 100:.0f}% sobre tu promedio"

    # Equivalencia en “días de hogar chileno”
    dias_equivalentes = ratio_cl  # porque total_kwh / 7 kWh/día

    # Mensaje final contextualizado a Chile
    mensaje = (
        f"Consumo estimado próximas 24 h: {total_kwh:.2f} kWh. "
        f"Esto es {detalle_user}. "
        f"En Chile, un hogar promedio consume alrededor de {NATIONAL_DAILY_KWH:.1f} kWh al día, "
        f"por lo que esta predicción equivale a ≈{dias_equivalentes:.1f} días de consumo "
        f"de un hogar residencial típico."
    )

    if nivel == "ROJO":
        mensaje += (
            " Nivel de alerta: ROJO. Revisa el uso de artefactos de alto consumo "
            "(calefactores eléctricos, horno, equipos encendidos 24/7) y evita "
            "concentrar cargas en horas punta."
        )
    elif nivel == "AMARILLO":
        mensaje += (
            " Nivel de alerta: AMARILLO. Hay margen para optimizar horarios y "
            "reducir el uso de los equipos más exigentes."
        )
    else:
        mensaje += (
            " Nivel de alerta: VERDE. Tu consumo está dentro de rangos moderados "
            "para un hogar chileno."
        )

    return nivel, mensaje, ratio_user



def _get_or_create_nivel_alerta(codigo: str, descripcion: str = ""):
    if not codigo:
        return None
    nivel, _ = NivelAlerta.objects.get_or_create(
        codigo=codigo,
        defaults={"descripcion": descripcion},
    )
    return nivel


def _get_or_create_tipo_notificacion(codigo: str, descripcion: str = ""):
    tipo, _ = TipoNotificacion.objects.get_or_create(
        codigo=codigo,
        defaults={"descripcion": descripcion},
    )
    return tipo


def _crear_prediccion_y_alerta_para_registro(request, usuario, rc, temp_c=None):
    """
    Dado un RegistroConsumo recién creado, genera:
      - predicción con el modelo HGBR (24h)
      - nivel de alerta (verde/amarillo/rojo)
      - Notificación in-app
      - correo de alerta al usuario

    Devuelve (pred, yhat, nivel_codigo)
    """
    # 1) Fecha de referencia para features de calendario
    dt_local = timezone.make_aware(
        datetime.datetime.combine(rc.fecha, datetime.time(hour=12)),
        timezone.get_current_timezone(),
    )

    # 2) Features de señales a partir de dispositivos del usuario
    signals = _signals_from_dispositivos(usuario)

    # 3) Calendario
    calendar = _calendar_feats(dt_local)

    # 4) Clima: usamos Temp_C del form si viene; si no, stub
    if temp_c is not None:
        try:
            temp_val = float(temp_c)
        except (TypeError, ValueError):
            temp_val = None
    else:
        temp_val = None

    if temp_val is not None:
        climate = {"Temp_C": temp_val}
    else:
        climate = _climate_stub(dt_local)

    # 5) Construir row y predecir
    row = build_row(signals, calendar, climate)
    yhat = float(predict_one(row))

    # 6) Comparar con baseline del usuario y clasificar alerta
    baseline = _user_baseline_kwh(usuario, ref_dt=rc.fecha)
    nivel_code, mensaje_alerta, ratio = _classify_alert(yhat, baseline)

    # 7) Nivel de alerta (catálogo)
    desc_map = {
        "VERDE": "Consumo dentro de un rango esperado según tu historial.",
        "AMARILLO": "Consumo moderadamente alto en comparación a tu historial.",
        "ROJO": "Consumo alto: revisa horarios y uso de equipos intensivos.",
    }
    nivel = _get_or_create_nivel_alerta(
        nivel_code,
        desc_map.get(nivel_code, "Alerta de consumo energético."),
    )

    # 8) Guardar predicción
    hoy = timezone.localdate()
    pred = PrediccionConsumo.objects.create(
        usuario=usuario,
        fecha_prediccion=hoy,
        periodo_inicio=rc.fecha,      # 24h ligadas a la fecha de la boleta
        periodo_fin=rc.fecha,
        consumo_predicho_kwh=yhat,
        nivel_alerta=nivel,
        creado_en=timezone.now(),
    )

    # 9) Notificación in-app
    tipo = _get_or_create_tipo_notificacion(
        "ALERTA_CONSUMO",
        "Alerta por predicción de consumo",
    )
    Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo="Predicción de consumo para las próximas 24 horas",
        mensaje=f"{mensaje_alerta} (≈ {yhat:.2f} kWh en 24 h).",
        leida=False,
        creada_en=timezone.now(),
    )

    # 10) Correo al usuario
    try:
        identidad = AuthIdentidad.objects.filter(usuario=usuario).first()
        to_email = identidad.email if identidad else getattr(request.user, "email", None)

        if to_email:
            subject = "AhorraLuz – alerta de consumo para tu hogar"
            cuerpo = (
                "Hola,\n\n"
                f"Nuestra app AhorraLuz estimó un consumo de aproximadamente "
                f"{yhat:.2f} kWh para las próximas 24 horas.\n"
                f"Nivel de alerta: {nivel_code or 'SIN ALERTA'}.\n"
                f"{mensaje_alerta}\n\n"
                "Puedes revisar los detalles e ingresar el consumo real desde tu panel,\n"
                "en la sección \"Predicciones pendientes\".\n\n"
                "Saludos,\n"
                "Equipo AhorraLuz"
            )

            send_mail(
                subject,
                cuerpo,
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
                fail_silently=True,
            )
    except Exception as e:
        logger.exception("[ALERTA_CONSUMO] Error enviando correo: %s", e)

    return pred, yhat, nivel_code

def _build_feature_row_from_form(form):
    """Arma signals/calendar/climate con defaults si el usuario no los ingresó."""
    dt = form.cleaned_data["fecha"]
    # calendario
    cal = {
        "Month": form.cleaned_data.get("Month") or dt.month,
        "DayOfWeek": form.cleaned_data.get("DayOfWeek") or dt.weekday(),
        "Hour": form.cleaned_data.get("Hour") or dt.hour,
        "Is_Weekday": form.cleaned_data.get("Is_Weekday")
            if form.cleaned_data.get("Is_Weekday") is not None else (1 if dt.weekday() < 5 else 0),
    }
    # señales (defaults seguros)
    sig = {
        "Global_reactive_power": form.cleaned_data.get("Global_reactive_power") or 0.0,
        "Voltage": form.cleaned_data.get("Voltage") or 220.0,
        "Global_intensity": form.cleaned_data.get("Global_intensity") or 5.0,
        "Sub_metering_1": form.cleaned_data.get("Sub_metering_1") or 0.0,
        "Sub_metering_2": form.cleaned_data.get("Sub_metering_2") or 0.0,
        "Sub_metering_3": form.cleaned_data.get("Sub_metering_3") or 0.0,
        "other_kwh_h": form.cleaned_data.get("other_kwh_h") or 0.0,
    }
    clima = {
        "Temp_C": form.cleaned_data.get("Temp_C") or 18.0
    }
    return build_row(sig, cal, clima)


@login_required
def consumo_new_and_predict(request):
    """
    1) Valida form y asegura el Usuario (UUID interno) vinculado al login
    2) Guarda RegistroConsumo
    3) Genera predicción y Notificación
    4) Devuelve misma vista con feedback
    """
    form = RegistroConsumoForm(request.POST or None)

    yhat = None
    alerta = None
    nivel = None

    if request.method == "POST":
        if not form.is_valid():
            # Devolvemos errores de validación de form, sin 500s
            return render(request, "core/consumo_form_predict.html", {"form": form})

        # Asegura el Usuario (UUID) de tu dominio, no el auth user
        usuario = ensure_usuario_for_request(request)
        if not usuario:
            form.add_error(None, "No fue posible asociar tu cuenta a un perfil de usuario interno.")
            return render(request, "core/consumo_form_predict.html", {"form": form})

        # Construye el registro sin grabar aún
        rc = form.save(commit=False)
        rc.usuario_id = usuario.id               # <- UUID correcto (tabla usuarios)
        rc.creado_en = timezone.now()

        # (opcional) Valida pertenencia del dispositivo
        if rc.dispositivo_id:
            pertenece = Dispositivo.objects.filter(
                id=rc.dispositivo_id, usuario_id=usuario.id
            ).exists()
            if not pertenece:
                form.add_error("dispositivo", "El dispositivo no pertenece a tu cuenta.")
                return render(request, "core/consumo_form_predict.html", {"form": form})

        # Guarda registro
        try:
            rc.save()
        except Exception as e:
            form.add_error(None, "No se pudo guardar el registro (revisa datos o duplicidad).")
            return render(request, "core/consumo_form_predict.html", {"form": form})

        # -------- Features para el modelo --------
        # Ajusta nombres a tu set real de features
        signals = {
            "Global_reactive_power": float(request.POST.get("global_reactive_power", 0) or 0),
            "Voltage": float(request.POST.get("voltage", 0) or 0),
            "Global_intensity": float(request.POST.get("global_intensity", 0) or 0),
            "Sub_metering_1": float(request.POST.get("sub_metering_1", 0) or 0),
            "Sub_metering_2": float(request.POST.get("sub_metering_2", 0) or 0),
            "Sub_metering_3": float(request.POST.get("sub_metering_3", 0) or 0),
            "other_kwh_h": float(request.POST.get("other_kwh_h", 0) or 0),
        }
        now = timezone.localtime()
        calendar = {
            "Month": now.month,
            "DayOfWeek": now.weekday(),  # 0=Lunes
            "Hour": now.hour,
            "Is_Weekday": 1 if now.weekday() < 5 else 0,
        }
        climate = {
            "Temp_C": float(request.POST.get("temp_c", 0) or 0),
        }

        row = build_row(signals, calendar, climate)
        yhat = float(predict_one(row))

        # -------- Reglas de alerta --------
        if yhat >= 3.5:
            nivel_code = "HIGH"
            alerta = "⚠️ Alto consumo estimado para el periodo."
        elif yhat >= 2.5:
            nivel_code = "MEDIUM"
            alerta = "Consumo medio-alto: considera posponer uso intensivo."
        elif yhat >= 1.5:
            nivel_code = "LOW"
            alerta = "Consumo moderado: optimiza calefacción/iluminación."
        else:
            nivel_code = None
            alerta = "Consumo proyectado bajo. ¡Buen momento para tareas eléctricas!"

        nivel = None
        if nivel_code:
            nivel = NivelAlerta.objects.filter(codigo=nivel_code).first()

        # -------- Guarda predicción (con los nombres REALES del modelo) --------
        hoy = timezone.localdate()
        PrediccionConsumo.objects.create(
            usuario=usuario,
            fecha_prediccion=hoy,
            periodo_inicio=rc.fecha,                 # ajusta si tu periodo es horario/diario
            periodo_fin=rc.fecha,                    # o hoy + timedelta(days=1) si corresponde
            consumo_predicho_kwh=yhat,
            nivel_alerta=nivel,
            creado_en=timezone.now(),
        )

        # -------- Notificación opcional --------
        tipo = TipoNotificacion.objects.filter(codigo="ALERTA_CONSUMO").first()
        if not tipo:
            tipo = TipoNotificacion.objects.create(codigo="ALERTA_CONSUMO", descripcion="Alerta por predicción de consumo")
        Notificacion.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo="Predicción de consumo",
            mensaje=alerta,
            leida=False,
            creada_en=timezone.now(),
        )

        messages.success(request, "✅ Registro guardado y predicción generada.")

    return render(request, "core/consumo_form_predict.html", {
        "form": form,
        "yhat": yhat,
        "alerta": alerta,
        "nivel": getattr(nivel, "codigo", None),
    })

@login_required
def nowcast_preview(request, pk: int):
    """Vista simple para mostrar el resultado y nivel de alerta ya guardado."""
    pred = get_object_or_404(PrediccionConsumo, pk=pk, usuario=request.user)
    return render(request, "core/nowcast_preview.html", {"pred": pred})


@login_required
def confirmar_consumo_real_list(request):
    """
    Lista de predicciones del usuario sin consumo_real_kwh (pendientes de confirmación).
    """
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        messages.error(request, "No se encontró tu perfil de usuario en el sistema.")
        return redirect("core:profile")

    pend = (
        PrediccionConsumo.objects
        .filter(usuario=usuario, consumo_real_kwh__isnull=True)
        .order_by("-fecha_prediccion")
    )
    page = Paginator(pend, 10).get_page(request.GET.get("page"))
    return render(request, "core/confirmar_real_list.html", {"page_obj": page})


@login_required
def confirmar_consumo_real_edit(request, pk: int):
    """
    Formulario para ingresar el consumo real a una predicción concreta.
    """
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        messages.error(request, "No se encontró tu perfil de usuario en el sistema.")
        return redirect("core:profile")

    pred = get_object_or_404(PrediccionConsumo, pk=pk, usuario=usuario)

    if request.method == "POST":
        form = PrediccionConsumoRealForm(request.POST, instance=pred)
        if form.is_valid():
            obj = form.save(commit=False)
            # si más adelante agregas un campo "confirmado_en", aquí lo setearías
            obj.save()
            messages.success(request, "✅ Consumo real confirmado.")
            return redirect("core:confirmar_real_list")
        messages.error(request, "⚠️ Revisa el valor ingresado.")
    else:
        form = PrediccionConsumoRealForm(instance=pred)

    return render(
        request,
        "core/confirmar_real_edit.html",
        {"form": form, "pred": pred},
    )




@login_required
def mis_dispositivos_list(request):
    """
    Lista de dispositivos del usuario final (no admin).
    """
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        messages.error(request, "No se encontró tu perfil de usuario en el sistema.")
        return redirect("core:profile")

    dispositivos = (
        Dispositivo.objects
        .filter(usuario=usuario)
        .order_by("-fecha_registro", "nombre")
    )
    return render(
        request,
        "usuarios/mis_dispositivos_list.html",        
        {"dispositivos": dispositivos},
    )


@login_required
def mis_dispositivo_new(request):
    """
    Crear un nuevo dispositivo asociado al usuario logueado.
    """
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        messages.error(request, "No se encontró tu perfil de usuario en el sistema.")
        return redirect("core:profile")

    if request.method == "POST":
        form = DispositivoUsuarioForm(request.POST, usuario=usuario)
        if form.is_valid():
            disp = form.save(commit=False)
            disp.usuario = usuario  # 🔗 vínculo al Usuario lógico
            disp.save()
            messages.success(request, "Dispositivo agregado correctamente.")
            return redirect("core:mis_dispositivos_list")
    else:
        form = DispositivoUsuarioForm(usuario=usuario)

    return render(
        request,
        "usuarios/mis_dispositivo_form.html",
        {"form": form, "modo": "crear"},
    )



@login_required
def mis_dispositivo_edit(request, pk):
    """
    Editar un dispositivo del usuario.
    Sólo permite editar si el dispositivo pertenece al usuario.
    """
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        messages.error(request, "No se encontró tu perfil de usuario en el sistema.")
        return redirect("core:profile")

    dispositivo = get_object_or_404(Dispositivo, pk=pk, usuario=usuario)

    if request.method == "POST":
        form = DispositivoUsuarioForm(request.POST, instance=dispositivo)
        if form.is_valid():
            form.save()
            messages.success(request, "Dispositivo actualizado correctamente.")
            return redirect("core:mis_dispositivos_list")
    else:
        form = DispositivoUsuarioForm(instance=dispositivo)

    return render(
        request,
        "usuarios/mis_dispositivo_form.html",
        {"form": form, "modo": "editar", "dispositivo": dispositivo},
    )


@login_required
def mis_dispositivo_delete(request, pk):
    """
    Eliminar un dispositivo del usuario.
    """
    usuario = ensure_usuario_for_request(request)
    if not usuario:
        messages.error(request, "No se encontró tu perfil de usuario en el sistema.")
        return redirect("core:profile")

    dispositivo = get_object_or_404(Dispositivo, pk=pk, usuario=usuario)

    if request.method == "POST":
        dispositivo.delete()
        messages.success(request, "Dispositivo eliminado correctamente.")
        return redirect("core:mis_dispositivos_list")

    return render(
        request,
        "usuarios/mis_dispositivo_confirm_delete.html",
        {"dispositivo": dispositivo},
    )



##ENDPOINT IoT Sencillo CAPSTONE PROYECTO TEST:
@csrf_exempt
@require_POST
def api_iot_registro_consumo(request):
    """
    Endpoint sencillo para que un dispositivo IoT (o script) envíe lecturas.

    Ejemplo de JSON esperado:
    {
      "usuario_id": "00000000-0000-0000-0000-000000000004",
      "dispositivo_id": 13,
      "fecha": "2025-11-15",
      "consumo_kwh": 2.5,
      "costo_clp": 2500
    }

    ⚠️ IMPORTANTE (para tu informe):
    Para simplificar el capstone no usamos token de API,
    pero en producción deberías proteger esto con un API key / OAuth.
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    usuario_id = payload.get("usuario_id")
    dispositivo_id = payload.get("dispositivo_id")
    fecha_str = payload.get("fecha")
    consumo_kwh = payload.get("consumo_kwh")
    costo_clp = payload.get("costo_clp", 0)

    if not usuario_id or consumo_kwh is None or not fecha_str:
        return JsonResponse(
            {
                "ok": False,
                "error": "usuario_id, consumo_kwh y fecha son obligatorios",
            },
            status=400,
        )

    # Buscar Usuario dueño del consumo
    try:
        usuario = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Usuario no encontrado"}, status=404)

    # Validar dispositivo (si viene)
    dispositivo = None
    if dispositivo_id is not None:
        try:
            dispositivo = Dispositivo.objects.get(pk=dispositivo_id, usuario=usuario)
        except Dispositivo.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": "Dispositivo no pertenece a este usuario"},
                status=404,
            )

    # Parsear fecha
    try:
        fecha = datetime.date.fromisoformat(fecha_str)
    except ValueError:
        return JsonResponse(
            {"ok": False, "error": "fecha debe tener formato YYYY-MM-DD"},
            status=400,
        )

    rc = RegistroConsumo(
        usuario=usuario,
        fecha=fecha,
        consumo_kwh=consumo_kwh,
        costo_clp=costo_clp or 0,
        dispositivo=dispositivo,
        fuente="automatica",
        creado_en=timezone.now(),
    )
    rc.save()

    return JsonResponse({"ok": True, "id": rc.id})
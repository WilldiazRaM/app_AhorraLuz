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
    # ejemplo: obtener métricas básicas y últimos registros
    registros = RegistroConsumo.objects.filter(usuario__id=request.user.id)[:10]
    context = {
        "title": "Dashboard AhorraLuz",
        "registros": registros,
    }
    return render(request, "core/dashboard.html", context)

@login_required
def profile_view(request):
    """
    Mostrar y editar datos básicos del usuario autenticado.
    Usa UserProfileForm que edita first_name, last_name, email.
    """
    user = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            logger.info("[PROFILE] Usuario %s actualizó su perfil", user.username)
            return redirect('core:profile')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
            logger.debug("[PROFILE] Errores en formulario: %s", form.errors.as_json())
    else:
        form = UserProfileForm(instance=user)

    return render(request, "core/profile.html", {
        "form": form,
        "user": user,
    })

@login_required
def consumo_new(request):
    if request.method == "POST":
        form = RegistroConsumoForm(request.POST)
        if form.is_valid():
            rc = form.save(commit=False)
            rc.usuario_id = request.user.id
            rc.save()
            return redirect('core:consumo_history')
    else:
        form = RegistroConsumoForm()
    return render(request, "core/consumo_form.html", {"form": form})

@login_required
def consumo_history(request):
    qs = RegistroConsumo.objects.filter(usuario__id=request.user.id).order_by('-fecha')[:100]
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

@login_required
def api_predict_next_24h(request):
    """
    Devuelve 24 horas de predicción horaria en kWh, timestamp local (America/Santiago).
    """
    tz = pytz.timezone("America/Santiago")
    now_utc = timezone.now()
    out = []
    for h in range(1, 25):
        ts_local = (now_utc + timedelta(hours=h)).astimezone(tz)
        row = build_row(
            signals=_default_signals(),
            calendar=_calendar_feats(ts_local),
            climate=_climate_stub(ts_local)
        )
        kwh = predict_one(row)
        out.append({
            "timestamp_local": ts_local.isoformat(),
            "kwh": round(kwh, 3)
        })
    return JsonResponse({"predicciones": out})



# === NOWCAST: helpers === PREDICTS TEST 1


def _get_or_create_nivel_alerta(codigo: str, descripcion: str) -> NivelAlerta:
    obj, _ = NivelAlerta.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion})
    return obj

def _get_or_create_tipo_notificacion(codigo: str, descripcion: str) -> TipoNotificacion:
    obj, _ = TipoNotificacion.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion})
    return obj

def _user_baseline_kwh(usuario, ref_dt):
    """Media de los últimos 7 días; si no hay datos, usa media de últimos 5 registros; si no, 1.0 kWh."""
    q = RegistroConsumo.objects.filter(usuario=usuario, fecha__gte=ref_dt - timedelta(days=7), fecha__lte=ref_dt)
    avg = q.aggregate(x=Avg("consumo_kwh"))["x"]
    if avg is None:
        q2 = RegistroConsumo.objects.filter(usuario=usuario).order_by("-fecha")[:5]
        avg = q2.aggregate(x=Avg("consumo_kwh"))["x"]
    return float(avg or 1.0)

def _classify_alert(yhat: float, baseline: float):
    """Devuelve (nivel, texto) con 4 niveles: VERDE/AMARILLO/NARANJA/ROJO comparando con baseline."""
    ratio = yhat / baseline if baseline > 0 else 1.0
    if ratio < 0.90:
        nivel = _get_or_create_nivel_alerta("VERDE", "Consumo bajo lo esperado")
        texto = f"Predicción {yhat:.2f} kWh (−{(1-ratio)*100:.0f}% vs tu promedio). ¡Buen desempeño!"
    elif ratio < 1.10:
        nivel = _get_or_create_nivel_alerta("AMARILLO", "Consumo dentro de lo esperado")
        texto = f"Predicción {yhat:.2f} kWh (≈{(ratio-1)*100:.0f}% vs promedio). Mantén hábitos actuales."
    elif ratio < 1.30:
        nivel = _get_or_create_nivel_alerta("NARANJA", "Consumo sobre lo esperado")
        texto = f"Predicción {yhat:.2f} kWh (+{(ratio-1)*100:.0f}% vs promedio). Revisa horarios y uso de equipos."
    else:
        nivel = _get_or_create_nivel_alerta("ROJO", "Riesgo de alto consumo")
        texto = f"Predicción {yhat:.2f} kWh (+{(ratio-1)*100:.0f}% vs promedio). Considera reducir cargas pico."
    return nivel, texto, ratio

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

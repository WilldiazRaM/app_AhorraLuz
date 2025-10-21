import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import user_passes_test, login_required
from django.urls import reverse
from .forms import PerfilForm, RegistroConsumoForm, AdminRegisterUserForm, AdminUpdateUserForm, UserProfileForm, ContactPublicForm
from .models import *
from django.core.paginator import Paginator
from django.db.models import Q
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



from .forms import PasswordResetRequestForm, SetNewPasswordForm
from .models import AuthIdentidad, PasswordResetToken
from django.conf import settings


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
@require_http_methods(["GET", "POST"])
def password_reset_request_view(request):
    subject = "Restablecer tu contraseña – AhorraLuz"
    context = {
        "minutes": settings.PASSWORD_RESET_MINUTES,
        "reset_link": reset_link,
        "now": timezone.now(),
    }
    html = render_to_string("emails/password_reset.html", context)
    text = strip_tags(html)

    send_mail(
        subject,
        text,  # fallback texto
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
        html_message=html,  # HTML principal
    )


    form = PasswordResetRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        # Siempre mostrarmos "enviado" para evitar enumeración de correos
        msg_ok = "Si el correo existe, te enviaremos un enlace para restablecer la contraseña."

        try:
            identidad = AuthIdentidad.objects.get(email__iexact=email)
        except AuthIdentidad.DoesNotExist:
            messages.info(request, msg_ok)
            return redirect("core:password_reset_request")

        # Generar token aleatorio y guardar solo el hash
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

        reset_link = f"{settings.SITE_URL}{reverse('core:password_reset_confirm')}?token={raw_token}"
        subject = "Restablecer tu contraseña – AhorraLuz"
        body = (
            f"Hola,\n\n"
            f"Solicitaste restablecer tu contraseña. Usa este enlace (válido por {settings.PASSWORD_RESET_MINUTES} minutos):\n\n"
            f"{reset_link}\n\n"
            f"Si no fuiste tú, ignora este mensaje.\n"
        )
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        except Exception as e:
            # No revelamos info sensible al usuario; log y mensaje genérico
            logger.exception("[RESET] Error enviando correo: %s", e)

        messages.info(request, msg_ok)
        return redirect("core:password_reset_request")

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
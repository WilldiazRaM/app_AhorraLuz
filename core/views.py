from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import user_passes_test, login_required
from django.urls import reverse
from .forms import PerfilForm, RegistroConsumoForm, AdminRegisterUserForm, AdminUpdateUserForm
from .models import *
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone



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
    try:
        perfil = request.user.perfil
    except Exception:
        perfil = None

    if request.method == "POST":
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            perfil = form.save(commit=False)
            perfil.usuario_id = request.user.id  # si tu PK es UUID
            perfil.save()
            return redirect('core:profile')
    else:
        form = PerfilForm(instance=perfil)

    return render(request, "core/profile.html", {"form": form})

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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import PerfilForm, RegistroConsumoForm
from .models import *

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

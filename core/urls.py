from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page='/'), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),
    path("consumo/new/", views.consumo_new, name="consumo_new"),
    path("consumo/history/", views.consumo_history, name="consumo_history"),
    path("mantenedor/usuarios/registrar/", views.register_user_admin, name="register_user_admin"),
]

# core/urls.py
import logging
from functools import wraps
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "core"

logger = logging.getLogger(__name__)

# Clase Login con logging (ya la tenías; la dejamos)
class DebugLoginView(auth_views.LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        logger.info("[LOGIN] form_valid username=%s ip=%s", username, self.request.META.get('REMOTE_ADDR'))
        return super().form_valid(form)

    def form_invalid(self, form):
        username = form.data.get("username", "<no-username>")
        # logs en formato JSON de errores (sin imprimir password)
        logger.warning("[LOGIN] form_invalid username=%s errors=%s ip=%s",
                       username, form.errors.as_json(), self.request.META.get('REMOTE_ADDR'))
        return super().form_invalid(form)


# Decorador para envolver views y loggear entrada/salida
def debug_view(fn):
    """
    Decorador que registra en logs la entrada a la vista, parámetros y tiempo.
    - NO imprime valores de POST (solo nombres de campos).
    - Mantiene firma original con functools.wraps.
    """
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        try:
            user = getattr(request, "user", None)
            user_repr = f"{user}" if user and user.is_authenticated else "anonymous"
        except Exception:
            user_repr = "unknown"

        # Info inicial: método, path, user, query keys y POST keys (no valores)
        query_keys = list(request.GET.keys())
        post_keys = list(request.POST.keys()) if request.method in ("POST", "PUT", "PATCH") else []
        logger.debug(
            "[VIEW ENTER] %s %s user=%s query_keys=%s post_keys=%s kwargs=%s",
            request.method, request.path, user_repr, query_keys, post_keys, kwargs
        )

        # Ejecutar la vista
        response = fn(request, *args, **kwargs)

        # Info final: status code si existe (algunos views retornan HttpResponse)
        status = getattr(response, "status_code", "n/a")
        logger.debug("[VIEW EXIT] %s %s -> status=%s user=%s",
                     request.method, request.path, status, user_repr)
        return response
    return wrapper


urlpatterns = [
    path("", debug_view(views.index), name="home"),
    path("register/", debug_view(views.register_view), name="register"),
    # usamos la clase DebugLoginView para loguear dentro del form_valid/form_invalid
    path("login/", DebugLoginView.as_view(), name="login"),
    path("logout/", debug_view(auth_views.LogoutView.as_view(next_page='/')), name="logout"),
    path("dashboard/", debug_view(views.dashboard), name="dashboard"),
    path("profile/", debug_view(views.profile_view), name="profile"),
    path("consumo/new/", debug_view(views.consumo_new), name="consumo_new"),
    path("consumo/history/", debug_view(views.consumo_history), name="consumo_history"),
    path("mantenedor/usuarios/registrar/", debug_view(views.register_user_admin), name="register_user_admin"),
    path("mantenedor/usuarios/", debug_view(views.admin_users_list), name="admin_users_list"),
    path("mantenedor/usuarios/<uuid:usuario_id>/editar/", debug_view(views.admin_user_update), name="admin_user_update"),
    path("mantenedor/usuarios/<uuid:usuario_id>/desactivar/", debug_view(views.admin_user_deactivate), name="admin_user_deactivate"),
    path("mantenedor/usuarios/<uuid:usuario_id>/eliminar/", debug_view(views.admin_user_delete), name="admin_user_delete"),
    path("mantenedor/usuarios/<uuid:usuario_id>/reset-password/", debug_view(views.admin_user_reset_password), name="admin_user_reset_password"),
    path("password/reset/", views.password_reset_request_view, name="password_reset_request"),
    path("password/reset/confirm/", views.password_reset_confirm_view, name="password_reset_confirm"),
]

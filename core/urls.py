# core/urls.py
import logging
from functools import wraps
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import ( api_predict_next_24h, ComunaListView, ComunaCreateView, ComunaUpdateView, ComunaDeleteView,
    TipoDispositivoListView, TipoDispositivoCreateView, TipoDispositivoUpdateView, TipoDispositivoDeleteView,
    DispositivoListView, DispositivoCreateView, DispositivoUpdateView, DispositivoDeleteView,
    AuditoriaEventoListView, AuditoriaEventoDetailView, )


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
    path("contacto/", debug_view(views.contact_public_view), name="contacto"),
    path("api/predict/next-24h/", debug_view(api_predict_next_24h), name="api_predict_next_24h"),
    # Comuna
    path("mantenedor/comunas/", debug_view(ComunaListView.as_view()), name="mant_comuna_list"),
    path("mantenedor/comunas/nuevo/", debug_view(ComunaCreateView.as_view()), name="mant_comuna_new"),
    path("mantenedor/comunas/<int:pk>/editar/", debug_view(ComunaUpdateView.as_view()), name="mant_comuna_edit"),
    path("mantenedor/comunas/<int:pk>/eliminar/", debug_view(ComunaDeleteView.as_view()), name="mant_comuna_delete"),

    # TipoDispositivo
    path("mantenedor/tipos-dispositivo/", debug_view(TipoDispositivoListView.as_view()), name="mant_tipodispositivo_list"),
    path("mantenedor/tipos-dispositivo/nuevo/", debug_view(TipoDispositivoCreateView.as_view()), name="mant_tipodispositivo_new"),
    path("mantenedor/tipos-dispositivo/<int:pk>/editar/", debug_view(TipoDispositivoUpdateView.as_view()), name="mant_tipodispositivo_edit"),
    path("mantenedor/tipos-dispositivo/<int:pk>/eliminar/", debug_view(TipoDispositivoDeleteView.as_view()), name="mant_tipodispositivo_delete"),

    # Dispositivo (operativo)
    path("mantenedor/dispositivos/", debug_view(DispositivoListView.as_view()), name="mant_dispositivo_list"),
    path("mantenedor/dispositivos/nuevo/", debug_view(DispositivoCreateView.as_view()), name="mant_dispositivo_new"),
    path("mantenedor/dispositivos/<int:pk>/editar/", debug_view(DispositivoUpdateView.as_view()), name="mant_dispositivo_edit"),
    path("mantenedor/dispositivos/<int:pk>/eliminar/", debug_view(DispositivoDeleteView.as_view()), name="mant_dispositivo_delete"),

    # Auditoría (solo lectura)
    path("mantenedor/auditoria/", debug_view(AuditoriaEventoListView.as_view()), name="mant_auditoria_list"),
    path("mantenedor/auditoria/<int:pk>/", debug_view(AuditoriaEventoDetailView.as_view()), name="mant_auditoria_detail"),

    # ---------- CATÁLOGOS ----------
    # TipoDispositivo
    path("mantenedor/tipos-dispositivo/", debug_view(views.TipoDispositivoList.as_view()), name="mant_tipodispositivo_list"),
    path("mantenedor/tipos-dispositivo/nuevo/", debug_view(views.TipoDispositivoCreate.as_view()), name="mant_tipodispositivo_new"),
    path("mantenedor/tipos-dispositivo/editar/", debug_view(lambda r: None), name="mant_tipodispositivo_edit_base"),  # solo para construir edit_base
    path("mantenedor/tipos-dispositivo/eliminar/", debug_view(lambda r: None), name="mant_tipodispositivo_delete_base"),
    path("mantenedor/tipos-dispositivo/<int:pk>/editar/", debug_view(views.TipoDispositivoUpdate.as_view()), name="mant_tipodispositivo_edit"),
    path("mantenedor/tipos-dispositivo/<int:pk>/eliminar/", debug_view(views.TipoDispositivoDelete.as_view()), name="mant_tipodispositivo_delete"),

    # TipoVivienda
    path("mantenedor/tipos-vivienda/", debug_view(views.TipoViviendaList.as_view()), name="mant_tipovivienda_list"),
    path("mantenedor/tipos-vivienda/nuevo/", debug_view(views.TipoViviendaCreate.as_view()), name="mant_tipovivienda_new"),
    path("mantenedor/tipos-vivienda/editar/", debug_view(lambda r: None), name="mant_tipovivienda_edit_base"),
    path("mantenedor/tipos-vivienda/eliminar/", debug_view(lambda r: None), name="mant_tipovivienda_delete_base"),
    path("mantenedor/tipos-vivienda/<int:pk>/editar/", debug_view(views.TipoViviendaUpdate.as_view()), name="mant_tipovivienda_edit"),
    path("mantenedor/tipos-vivienda/<int:pk>/eliminar/", debug_view(views.TipoViviendaDelete.as_view()), name="mant_tipovivienda_delete"),

    # TipoNotificacion
    path("mantenedor/tipos-notificacion/", debug_view(views.TipoNotificacionList.as_view()), name="mant_tiponotif_list"),
    path("mantenedor/tipos-notificacion/nuevo/", debug_view(views.TipoNotificacionCreate.as_view()), name="mant_tiponotif_new"),
    path("mantenedor/tipos-notificacion/editar/", debug_view(lambda r: None), name="mant_tiponotif_edit_base"),
    path("mantenedor/tipos-notificacion/eliminar/", debug_view(lambda r: None), name="mant_tiponotif_delete_base"),
    path("mantenedor/tipos-notificacion/<int:pk>/editar/", debug_view(views.TipoNotificacionUpdate.as_view()), name="mant_tiponotif_edit"),
    path("mantenedor/tipos-notificacion/<int:pk>/eliminar/", debug_view(views.TipoNotificacionDelete.as_view()), name="mant_tiponotif_delete"),

    # NivelAlerta
    path("mantenedor/niveles-alerta/", debug_view(views.NivelAlertaList.as_view()), name="mant_nivelalerta_list"),
    path("mantenedor/niveles-alerta/nuevo/", debug_view(views.NivelAlertaCreate.as_view()), name="mant_nivelalerta_new"),
    path("mantenedor/niveles-alerta/editar/", debug_view(lambda r: None), name="mant_nivelalerta_edit_base"),
    path("mantenedor/niveles-alerta/eliminar/", debug_view(lambda r: None), name="mant_nivelalerta_delete_base"),
    path("mantenedor/niveles-alerta/<int:pk>/editar/", debug_view(views.NivelAlertaUpdate.as_view()), name="mant_nivelalerta_edit"),
    path("mantenedor/niveles-alerta/<int:pk>/eliminar/", debug_view(views.NivelAlertaDelete.as_view()), name="mant_nivelalerta_delete"),

    # Permisos
    path("mantenedor/permisos/", debug_view(views.PermisoList.as_view()), name="mant_permiso_list"),
    path("mantenedor/permisos/nuevo/", debug_view(views.PermisoCreate.as_view()), name="mant_permiso_new"),
    path("mantenedor/permisos/editar/", debug_view(lambda r: None), name="mant_permiso_edit_base"),
    path("mantenedor/permisos/eliminar/", debug_view(lambda r: None), name="mant_permiso_delete_base"),
    path("mantenedor/permisos/<int:pk>/editar/", debug_view(views.PermisoUpdate.as_view()), name="mant_permiso_edit"),
    path("mantenedor/permisos/<int:pk>/eliminar/", debug_view(views.PermisoDelete.as_view()), name="mant_permiso_delete"),

    # Roles
    path("mantenedor/roles/", debug_view(views.RolList.as_view()), name="mant_rol_list"),
    path("mantenedor/roles/nuevo/", debug_view(views.RolCreate.as_view()), name="mant_rol_new"),
    path("mantenedor/roles/editar/", debug_view(lambda r: None), name="mant_rol_edit_base"),
    path("mantenedor/roles/eliminar/", debug_view(lambda r: None), name="mant_rol_delete_base"),
    path("mantenedor/roles/<int:pk>/editar/", debug_view(views.RolUpdate.as_view()), name="mant_rol_edit"),
    path("mantenedor/roles/<int:pk>/eliminar/", debug_view(views.RolDelete.as_view()), name="mant_rol_delete"),

    # ---------- OPERATIVO ----------
    # Dispositivos
    path("mantenedor/dispositivos/", debug_view(views.DispositivoList.as_view()), name="mant_dispositivo_list"),
    path("mantenedor/dispositivos/nuevo/", debug_view(views.DispositivoCreate.as_view()), name="mant_dispositivo_new"),
    path("mantenedor/dispositivos/editar/", debug_view(lambda r: None), name="mant_dispositivo_edit_base"),
    path("mantenedor/dispositivos/eliminar/", debug_view(lambda r: None), name="mant_dispositivo_delete_base"),
    path("mantenedor/dispositivos/<int:pk>/editar/", debug_view(views.DispositivoUpdate.as_view()), name="mant_dispositivo_edit"),
    path("mantenedor/dispositivos/<int:pk>/eliminar/", debug_view(views.DispositivoDelete.as_view()), name="mant_dispositivo_delete"),

    # Direcciones
    path("mantenedor/direcciones/", debug_view(views.DireccionList.as_view()), name="mant_direccion_list"),
    path("mantenedor/direcciones/nuevo/", debug_view(views.DireccionCreate.as_view()), name="mant_direccion_new"),
    path("mantenedor/direcciones/editar/", debug_view(lambda r: None), name="mant_direccion_edit_base"),
    path("mantenedor/direcciones/eliminar/", debug_view(lambda r: None), name="mant_direccion_delete_base"),
    path("mantenedor/direcciones/<int:pk>/editar/", debug_view(views.DireccionUpdate.as_view()), name="mant_direccion_edit"),
    path("mantenedor/direcciones/<int:pk>/eliminar/", debug_view(views.DireccionDelete.as_view()), name="mant_direccion_delete"),

    # Registros de consumo
    path("mantenedor/registros-consumo/", debug_view(views.RegistroConsumoList.as_view()), name="mant_registroconsumo_list"),
    path("mantenedor/registros-consumo/nuevo/", debug_view(views.RegistroConsumoCreate.as_view()), name="mant_registroconsumo_new"),
    path("mantenedor/registros-consumo/editar/", debug_view(lambda r: None), name="mant_registroconsumo_edit_base"),
    path("mantenedor/registros-consumo/eliminar/", debug_view(lambda r: None), name="mant_registroconsumo_delete_base"),
    path("mantenedor/registros-consumo/<int:pk>/editar/", debug_view(views.RegistroConsumoUpdate.as_view()), name="mant_registroconsumo_edit"),
    path("mantenedor/registros-consumo/<int:pk>/eliminar/", debug_view(views.RegistroConsumoDelete.as_view()), name="mant_registroconsumo_delete"),

    # Notificaciones
    path("mantenedor/notificaciones/", debug_view(views.NotificacionList.as_view()), name="mant_notificacion_list"),
    path("mantenedor/notificaciones/nuevo/", debug_view(views.NotificacionCreate.as_view()), name="mant_notificacion_new"),
    path("mantenedor/notificaciones/editar/", debug_view(lambda r: None), name="mant_notificacion_edit_base"),
    path("mantenedor/notificaciones/eliminar/", debug_view(lambda r: None), name="mant_notificacion_delete_base"),
    path("mantenedor/notificaciones/<int:pk>/editar/", debug_view(views.NotificacionUpdate.as_view()), name="mant_notificacion_edit"),
    path("mantenedor/notificaciones/<int:pk>/eliminar/", debug_view(views.NotificacionDelete.as_view()), name="mant_notificacion_delete"),

    # Predicciones
    path("mantenedor/predicciones/", debug_view(views.PrediccionConsumoList.as_view()), name="mant_prediccion_list"),
    path("mantenedor/predicciones/nuevo/", debug_view(views.PrediccionConsumoCreate.as_view()), name="mant_prediccion_new"),
    path("mantenedor/predicciones/editar/", debug_view(lambda r: None), name="mant_prediccion_edit_base"),
    path("mantenedor/predicciones/eliminar/", debug_view(lambda r: None), name="mant_prediccion_delete_base"),
    path("mantenedor/predicciones/<int:pk>/editar/", debug_view(views.PrediccionConsumoUpdate.as_view()), name="mant_prediccion_edit"),
    path("mantenedor/predicciones/<int:pk>/eliminar/", debug_view(views.PrediccionConsumoDelete.as_view()), name="mant_prediccion_delete"),
]

from django.contrib import admin

# Register your models here.
from django.contrib import admin
from . import models


@admin.register(models.Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "activo", "creado_en", "actualizado_en")
    search_fields = ("id",)
    list_filter = ("activo",)


@admin.register(models.Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rut", "nombres", "apellidos", "tipo_vivienda")
    search_fields = ("rut", "nombres", "apellidos")


@admin.register(models.AuthIdentidad)
class AuthIdentidadAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "email", "ultimo_acceso", "creado_en")
    search_fields = ("email",)
    list_filter = ("creado_en",)


@admin.register(models.Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "usuario", "tipo_dispositivo", "activo", "fecha_registro")
    search_fields = ("nombre",)
    list_filter = ("tipo_dispositivo", "activo")


@admin.register(models.Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "calle", "numero", "depto", "comuna")
    search_fields = ("calle", "numero")
    list_filter = ("comuna",)


@admin.register(models.MetricaMensual)
class MetricaMensualAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "periodo_mes", "consumo_kwh", "ahorro_clp")
    search_fields = ("usuario__id",)
    list_filter = ("periodo_mes",)


@admin.register(models.RegistroConsumo)
class RegistroConsumoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "fecha", "consumo_kwh", "costo_clp", "dispositivo")
    search_fields = ("usuario__id",)
    list_filter = ("fecha",)


@admin.register(models.PrediccionConsumo)
class PrediccionConsumoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "fecha_prediccion", "consumo_predicho_kwh", "nivel_alerta")
    search_fields = ("usuario__id",)
    list_filter = ("fecha_prediccion", "nivel_alerta")


@admin.register(models.Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "tipo", "titulo", "leida", "creada_en")
    search_fields = ("titulo", "mensaje")
    list_filter = ("tipo", "leida")


@admin.register(models.AuditoriaEvento)
class AuditoriaEventoAdmin(admin.ModelAdmin):
    list_display = ("id", "entidad", "entidad_id", "accion", "usuario_id", "ocurrido_en")
    search_fields = ("entidad", "entidad_id", "accion")
    list_filter = ("accion",)


@admin.register(models.Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(models.TipoDispositivo)
class TipoDispositivoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(models.TipoVivienda)
class TipoViviendaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(models.TipoNotificacion)
class TipoNotificacionAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "descripcion")
    search_fields = ("codigo",)


@admin.register(models.NivelAlerta)
class NivelAlertaAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "descripcion")
    search_fields = ("codigo",)


@admin.register(models.Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "descripcion")
    search_fields = ("codigo",)


@admin.register(models.Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(models.RolPermiso)
class RolPermisoAdmin(admin.ModelAdmin):
    list_display = ("rol", "permiso")
    search_fields = ("rol__nombre", "permiso__codigo")
    list_filter = ("rol",)


@admin.register(models.UsuarioRol)
class UsuarioRolAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rol") 
    search_fields = ("usuario__id", "rol__nombre")
    list_filter = ("rol",)

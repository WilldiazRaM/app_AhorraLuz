# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuditoriaEventos(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario_id = models.UUIDField(blank=True, null=True)
    entidad = models.TextField()
    entidad_id = models.TextField(blank=True, null=True)
    accion = models.TextField()
    detalle = models.JSONField(blank=True, null=True)
    ip = models.TextField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    ocurrido_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auditoria_eventos'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthIdentidades(models.Model):
    id = models.UUIDField(primary_key=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    email = models.TextField()
    contrasena_hash = models.TextField()
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_identidades'


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CatComuna(models.Model):
    nombre = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = 'cat_comuna'


class CatNivelAlerta(models.Model):
    id = models.SmallAutoField(primary_key=True)
    codigo = models.TextField(unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cat_nivel_alerta'


class CatTipoDispositivo(models.Model):
    id = models.SmallAutoField(primary_key=True)
    nombre = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = 'cat_tipo_dispositivo'


class CatTipoNotificacion(models.Model):
    id = models.SmallAutoField(primary_key=True)
    codigo = models.TextField(unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cat_tipo_notificacion'


class CatTipoVivienda(models.Model):
    id = models.SmallAutoField(primary_key=True)
    nombre = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = 'cat_tipo_vivienda'


class Direcciones(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    calle = models.CharField(max_length=120)
    numero = models.CharField(max_length=20, blank=True, null=True)
    depto = models.CharField(max_length=20, blank=True, null=True)
    comuna = models.ForeignKey(CatComuna, models.DO_NOTHING, blank=True, null=True)
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'direcciones'


class Dispositivos(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    nombre = models.CharField(max_length=100)
    tipo_dispositivo = models.ForeignKey(CatTipoDispositivo, models.DO_NOTHING, blank=True, null=True)
    potencia_promedio_w = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    horas_uso_diario = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    activo = models.BooleanField()
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'dispositivos'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class MetricasMensuales(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    periodo_mes = models.DateField()
    consumo_kwh = models.DecimalField(max_digits=14, decimal_places=4)
    ahorro_clp = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    reduccion_huella_co2_kg = models.DecimalField(max_digits=14, decimal_places=3, blank=True, null=True)
    comparacion_mes_anterior_pct = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    calculado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'metricas_mensuales'
        unique_together = (('usuario', 'periodo_mes'),)


class Notificaciones(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    tipo = models.ForeignKey(CatTipoNotificacion, models.DO_NOTHING, blank=True, null=True)
    titulo = models.CharField(max_length=140, blank=True, null=True)
    mensaje = models.TextField()
    leida = models.BooleanField()
    creada_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'notificaciones'


class Perfiles(models.Model):
    usuario = models.OneToOneField('Usuarios', models.DO_NOTHING, primary_key=True)
    rut = models.TextField(unique=True, blank=True, null=True)
    nombres = models.CharField(max_length=100, blank=True, null=True)
    apellidos = models.CharField(max_length=100, blank=True, null=True)
    tipo_vivienda = models.ForeignKey(CatTipoVivienda, models.DO_NOTHING, blank=True, null=True)
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'perfiles'


class Permisos(models.Model):
    id = models.SmallAutoField(primary_key=True)
    codigo = models.TextField(unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'permisos'


class PrediccionesConsumo(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    fecha_prediccion = models.DateField()
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    consumo_predicho_kwh = models.DecimalField(max_digits=12, decimal_places=4)
    nivel_alerta = models.ForeignKey(CatNivelAlerta, models.DO_NOTHING, blank=True, null=True)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'predicciones_consumo'


class RegistrosConsumo(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    fecha = models.DateField()
    consumo_kwh = models.DecimalField(max_digits=12, decimal_places=4)
    costo_clp = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    dispositivo = models.ForeignKey(Dispositivos, models.DO_NOTHING, blank=True, null=True)
    fuente = models.TextField()  # This field type is a guess.
    creado_en = models.DateTimeField()

    # A unique constraint could not be introspected.
    class Meta:
        managed = False
        db_table = 'registros_consumo'
        unique_together = (('usuario', 'fecha'),)


class RolPermiso(models.Model):
    rol = models.OneToOneField('Roles', models.DO_NOTHING, primary_key=True)  # The composite primary key (rol_id, permiso_id) found, that is not supported. The first column is selected.
    permiso = models.ForeignKey(Permisos, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'rol_permiso'
        unique_together = (('rol', 'permiso'),)


class Roles(models.Model):
    id = models.SmallAutoField(primary_key=True)
    nombre = models.TextField(unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'


class UsuarioRol(models.Model):
    usuario = models.OneToOneField('Usuarios', models.DO_NOTHING, primary_key=True)  # The composite primary key (usuario_id, rol_id) found, that is not supported. The first column is selected.
    rol = models.ForeignKey(Roles, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'usuario_rol'
        unique_together = (('usuario', 'rol'),)


class Usuarios(models.Model):
    id = models.UUIDField(primary_key=True)
    activo = models.BooleanField()
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'usuarios'

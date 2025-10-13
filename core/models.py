from django.db import models

# Create your models here.
from django.db import models


class AuditoriaEvento(models.Model):
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
        db_table = "auditoria_eventos"

    def __str__(self):
        return f"{self.entidad}#{self.entidad_id} - {self.accion}"


class AuthIdentidad(models.Model):
    id = models.UUIDField(primary_key=True)
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE)
    email = models.TextField()
    contrasena_hash = models.TextField()
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()

    class Meta:
        db_table = "auth_identidades"
        indexes = [
            models.Index(fields=["email"], name="ux_auth_identidades_email_ci")
        ]

    def __str__(self):
        return self.email


class Comuna(models.Model):
    nombre = models.TextField(unique=True)

    class Meta:
        db_table = "cat_comuna"

    def __str__(self):
        return self.nombre


class NivelAlerta(models.Model):
    id = models.SmallAutoField(primary_key=True)
    codigo = models.TextField(unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "cat_nivel_alerta"

    def __str__(self):
        return self.codigo


class TipoDispositivo(models.Model):
    id = models.SmallAutoField(primary_key=True)
    nombre = models.TextField(unique=True)

    class Meta:
        db_table = "cat_tipo_dispositivo"

    def __str__(self):
        return self.nombre


class TipoNotificacion(models.Model):
    id = models.SmallAutoField(primary_key=True)
    codigo = models.TextField(unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "cat_tipo_notificacion"

    def __str__(self):
        return self.codigo


class TipoVivienda(models.Model):
    id = models.SmallAutoField(primary_key=True)
    nombre = models.TextField(unique=True)

    class Meta:
        db_table = "cat_tipo_vivienda"

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    id = models.UUIDField(primary_key=True)
    activo = models.BooleanField()
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return str(self.id)


class Direccion(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE)
    calle = models.CharField(max_length=120)
    numero = models.CharField(max_length=20, blank=True, null=True)
    depto = models.CharField(max_length=20, blank=True, null=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, blank=True, null=True)
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()

    class Meta:
        db_table = "direcciones"

    def __str__(self):
        return f"{self.calle} {self.numero or ''}".strip()


class Dispositivo(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    tipo_dispositivo = models.ForeignKey(TipoDispositivo, on_delete=models.SET_NULL, blank=True, null=True)
    potencia_promedio_w = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    horas_uso_diario = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField()

    class Meta:
        db_table = "dispositivos"

    def __str__(self):
        return self.nombre


class MetricaMensual(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE)
    periodo_mes = models.DateField()
    consumo_kwh = models.DecimalField(max_digits=14, decimal_places=4)
    ahorro_clp = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    reduccion_huella_co2_kg = models.DecimalField(max_digits=14, decimal_places=3, blank=True, null=True)
    comparacion_mes_anterior_pct = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    calculado_en = models.DateTimeField()

    class Meta:
        db_table = "metricas_mensuales"
        unique_together = (("usuario", "periodo_mes"),)

    def __str__(self):
        return f"{self.usuario} - {self.periodo_mes}"


class Notificacion(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoNotificacion, on_delete=models.SET_NULL, blank=True, null=True)
    titulo = models.CharField(max_length=140, blank=True, null=True)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    creada_en = models.DateTimeField()

    class Meta:
        db_table = "notificaciones"

    def __str__(self):
        return self.titulo or f"Notificacion {self.id}"


class Perfil(models.Model):
    usuario = models.OneToOneField("Usuario", on_delete=models.CASCADE, primary_key=True)
    rut = models.TextField(unique=True, blank=True, null=True)
    nombres = models.CharField(max_length=100, blank=True, null=True)
    apellidos = models.CharField(max_length=100, blank=True, null=True)
    tipo_vivienda = models.ForeignKey(TipoVivienda, on_delete=models.SET_NULL, blank=True, null=True)
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()

    class Meta:
        db_table = "perfiles"

    def __str__(self):
        return f"{self.nombres or ''} {self.apellidos or ''}".strip() or str(self.usuario)


class Permiso(models.Model):
    id = models.SmallAutoField(primary_key=True)
    codigo = models.TextField(unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "permisos"

    def __str__(self):
        return self.codigo


class PrediccionConsumo(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE)
    fecha_prediccion = models.DateField()
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    consumo_predicho_kwh = models.DecimalField(max_digits=12, decimal_places=4)
    nivel_alerta = models.ForeignKey(NivelAlerta, on_delete=models.SET_NULL, blank=True, null=True)
    creado_en = models.DateTimeField()

    class Meta:
        db_table = "predicciones_consumo"

    def __str__(self):
        return f"{self.usuario} - {self.fecha_prediccion}"


class RegistroConsumo(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE)
    fecha = models.DateField()
    consumo_kwh = models.DecimalField(max_digits=12, decimal_places=4)
    costo_clp = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.SET_NULL, blank=True, null=True)
    fuente = models.TextField()
    creado_en = models.DateTimeField()

    class Meta:
        db_table = "registros_consumo"
        unique_together = (("usuario", "fecha"),)

    def __str__(self):
        return f"{self.usuario} - {self.fecha}"


class Rol(models.Model):
    id = models.SmallAutoField(primary_key=True)
    nombre = models.TextField(unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.nombre


class RolPermiso(models.Model):

    rol = models.OneToOneField('Rol', on_delete=models.CASCADE, primary_key=True)
    permiso = models.ForeignKey('Permiso', on_delete=models.CASCADE)

    class Meta:
        db_table = "rol_permiso"
        unique_together = (("rol", "permiso"),)
        managed = False

    def __str__(self):
        return f"{self.rol} -> {self.permiso}"


class UsuarioRol(models.Model):
    usuario = models.OneToOneField('Usuario', on_delete=models.CASCADE, primary_key=True)
    rol = models.ForeignKey('Rol', on_delete=models.CASCADE)

    class Meta:
        db_table = "usuario_rol"
        unique_together = (("usuario", "rol"),)
        managed = False

    def __str__(self):
        return f"{self.usuario} -> {self.rol}"


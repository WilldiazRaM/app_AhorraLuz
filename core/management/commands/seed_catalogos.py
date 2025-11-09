from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    Comuna, TipoDispositivo, TipoVivienda, TipoNotificacion, NivelAlerta
)

TIPOS_DISPOSITIVO = [
    "Refrigerador", "Congelador", "Lavadora", "Secadora", "Lavavajillas",
    "Horno eléctrico", "Cocina eléctrica", "Microondas", "Hervidor eléctrico",
    "Tostador", "Licuadora", "Robot de cocina",
    "Aire acondicionado", "Calefactor eléctrico", "Termoventilador",
    "Deshumidificador", "Ventilador",
    "Televisor LED/LCD", "Decodificador/Set-top box",
    "Computador de escritorio", "Notebook", "Monitor",
    "Router/Modem", "Consola de videojuegos",
    "Iluminación LED", "Iluminación fluorescente",
    "Bomba de agua", "Cargadores (celular/tablet)", "Impresora",
]

TIPOS_VIVIENDA = [
    "Casa aislada", "Casa pareada", "Departamento", "Condominio", "Otro",
]

TIPOS_NOTIFICACION = [
    ("ALERTA_ALTO_CONSUMO", "Alerta por consumo alto respecto al histórico"),
    ("RECORDATORIO_LECTURA", "Recordatorio de ingreso de lectura/consumo"),
    ("RECOMENDACION_AHORRO", "Recomendaciones inteligentes de ahorro"),
]

NIVELES_ALERTA = [
    ("BAJO", "Bajo"), ("MEDIO", "Medio"), ("ALTO", "Alto"), ("CRITICO", "Crítico"),
]

# Gran Santiago (comunas urbanas principales de la Región Metropolitana)
COMUNAS_GRAN_SANTIAGO = [
    "Santiago", "Las Condes", "Providencia", "Vitacura", "Ñuñoa", "La Reina", "Macul", "Peñalolén",
    "Lo Barnechea", "Huechuraba", "Recoleta", "Independencia", "Conchalí", "Renca", "Cerro Navia",
    "Lo Prado", "Quinta Normal", "Estación Central", "Pudahuel", "Maipú", "Cerrillos", "Pedro Aguirre Cerda",
    "Lo Espejo", "San Miguel", "San Joaquín", "La Cisterna", "San Ramón", "La Granja",
    "El Bosque", "La Florida", "Puente Alto", "Pirque", "San José de Maipo",
    "Quilicura", "Colina", "Lampa", "Til Til",
]

class Command(BaseCommand):
    help = "Carga catálogos básicos y comunas de Gran Santiago"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Borrar y recargar")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            self.stdout.write("Limpiando catálogos...")
            TipoDispositivo.objects.all().delete()
            TipoVivienda.objects.all().delete()
            TipoNotificacion.objects.all().delete()
            NivelAlerta.objects.all().delete()
            # (No borro comunas por si ya hay FK; si necesitas, agrega confirmación)

        # Tipos de dispositivo
        for nombre in TIPOS_DISPOSITIVO:
            TipoDispositivo.objects.get_or_create(nombre=nombre)

        # Tipos de vivienda
        for nombre in TIPOS_VIVIENDA:
            TipoVivienda.objects.get_or_create(nombre=nombre)

        # Tipos de notificación
        for codigo, descripcion in TIPOS_NOTIFICACION:
            TipoNotificacion.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion})

        # Niveles de alerta
        for codigo, descripcion in NIVELES_ALERTA:
            NivelAlerta.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion})

        # Comunas (Gran Santiago)
        for nombre in COMUNAS_GRAN_SANTIAGO:
            Comuna.objects.get_or_create(nombre=nombre)

        self.stdout.write(self.style.SUCCESS("Catálogos cargados correctamente."))

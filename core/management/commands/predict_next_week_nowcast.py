# Aplicacion/core/management/commands/predict_next_week_nowcast.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import numpy as np
from zoneinfo import ZoneInfo  # alternativa moderna a pytz

from core.utils.ml_nowcast import build_row, predict_one
from core.models import PrediccionConsumo, NivelAlerta

TZ = ZoneInfo("America/Santiago")

def _signals():
    return {
        "Global_reactive_power": 0.3,
        "Voltage": 230.0,
        "Global_intensity": 12.0,
        "Sub_metering_1": 0.1,
        "Sub_metering_2": 0.1,
        "Sub_metering_3": 0.3,
        "other_kwh_h": 0.2
    }

def _calendar(dt_local):
    dow = dt_local.weekday()
    return {
        "Month": dt_local.month,
        "DayOfWeek": dow,
        "Hour": dt_local.hour,
        "Is_Weekday": int(dow < 5),
    }

def _climate(_dt_local):
    return {"Temp_C": 14.0}

class Command(BaseCommand):
    help = "Genera predicciones diarias (próximos 7 días) y las guarda en predicciones_consumo"

    def add_arguments(self, parser):
        parser.add_argument("--usuario-id", required=True, help="UUID del usuario (tabla usuarios)")

    def handle(self, *args, **opts):
        usuario_id = opts["usuario_id"]
        now_utc = timezone.now()
        start_local = now_utc.astimezone(TZ).date() + timedelta(days=1)

        registros = []  # (day, kwh)
        for d in range(7):
            day = start_local + timedelta(days=d)
            kwh_day = 0.0
            for h in range(24):
                dt_local = timezone.datetime(day.year, day.month, day.day, h, 0, 0, tzinfo=TZ)
                row = build_row(_signals(), _calendar(dt_local), _climate(dt_local))
                kwh_day += predict_one(row)
            registros.append((day, round(kwh_day, 3)))

        vals = [kwh for (_day, kwh) in registros]
        p33, p66 = np.percentile(vals, [33, 66])

        # Asegúrate de tener nivel_alerta con códigos LOW/MEDIUM/HIGH
        low  = NivelAlerta.objects.filter(codigo__iexact="LOW").first()
        med  = NivelAlerta.objects.filter(codigo__iexact="MEDIUM").first()
        high = NivelAlerta.objects.filter(codigo__iexact="HIGH").first()

        def pick_level(kwh):
            if kwh < p33: return low
            if kwh < p66: return med
            return high

        for day, kwh in registros:
            PrediccionConsumo.objects.get_or_create(
                usuario_id=usuario_id,
                fecha_prediccion=now_utc.date(),
                periodo_inicio=day,   # tus campos son DateField en el modelo
                periodo_fin=day,
                defaults={
                    "consumo_predicho_kwh": kwh,
                    "nivel_alerta": pick_level(kwh),
                    "creado_en": timezone.now(),
                }
            )

        self.stdout.write(self.style.SUCCESS("Predicciones semanales guardadas."))
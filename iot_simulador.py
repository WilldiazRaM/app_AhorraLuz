#!/usr/bin/env python
"""
Simulador sencillo de dispositivo IoT para AhorraLuz.

- Resuelve el usuario energético (UUID) a partir del email (AuthIdentidad).
- Busca un dispositivo asociado a ese usuario.
- Genera una lectura simulada y la envía al endpoint /api/iot/consumos/.
"""

import os
import sys
import random
import datetime

import django
import requests

# Ajusta si tu settings tiene otro nombre / modulo
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ahorraluz.settings")
django.setup()

from core.models import AuthIdentidad, Dispositivo, RegistroConsumo  # noqa: E402


def main():
    # ----------- 1) Config vía variables de entorno -----------
    email = (os.getenv("AHORRALUZ_IOT_EMAIL") or "").strip().lower()
    base_url = (os.getenv("AHORRALUZ_IOT_BASE_URL") or "").rstrip("/")

    # Opcionales para elegir dispositivo concreto
    device_name = (os.getenv("AHORRALUZ_IOT_DEVICE_NAME", "") or "").strip()
    device_id_env = os.getenv("AHORRALUZ_IOT_DEVICE_ID")

    if not email:
        print("❌ Debes definir AHORRALUZ_IOT_EMAIL.")
        sys.exit(1)

    print(f"🔧 Email IoT configurado: {email}")
    print(f"🔧 BASE_URL: {base_url}")

    # ----------- 2) Resolver usuario energético (UUID) -----------
    identidad = (
        AuthIdentidad.objects
        .select_related("usuario")
        .filter(email__iexact=email)
        .first()
    )

    if not identidad or not identidad.usuario_id:
        print(f"❌ No se encontró AuthIdentidad para el email {email}.")
        print("   Primero entra a la app AhorraLuz con ese correo para que se cree el usuario interno.")
        sys.exit(1)

    usuario = identidad.usuario
    print(f"✅ Usuario energético encontrado: UUID={usuario.id}")

    # ----------- 3) Resolver dispositivo a usar -----------
    dispositivos_qs = Dispositivo.objects.filter(usuario=usuario, activo=True).order_by("id")

    dispositivo = None
    if device_id_env:
        try:
            dispositivo = dispositivos_qs.get(pk=int(device_id_env))
        except Dispositivo.DoesNotExist:
            print(f"⚠️ No se encontró dispositivo id={device_id_env} para este usuario; se buscará otro.")

    if not dispositivo and device_name:
        dispositivo = dispositivos_qs.filter(nombre__iexact=device_name).first()

    if not dispositivo:
        dispositivo = dispositivos_qs.first()

    if not dispositivo:
        print("⚠️ El usuario no tiene dispositivos activos.")
        print("   Se enviará la lectura SIN dispositivo_id (campo null).")
        dispositivo_id = None
    else:
        dispositivo_id = dispositivo.id
        print(f"✅ Usando dispositivo id={dispositivo_id}, nombre={dispositivo.nombre!r}")

    # ----------- 4) Elegir fecha segura (no romper UNIQUE (usuario, fecha)) -----------
    ultimo = (
        RegistroConsumo.objects
        .filter(usuario=usuario)
        .order_by("-fecha")
        .first()
    )
    if ultimo:
        fecha = ultimo.fecha + datetime.timedelta(days=1)
        print(f"📅 Última fecha de consumo: {ultimo.fecha} -> nueva fecha simulada: {fecha}")
    else:
        fecha = datetime.date.today()
        print(f"📅 No hay registros previos, usando fecha de hoy: {fecha}")

    # ----------- 5) Datos simulados de consumo -----------
    consumo_kwh = round(random.uniform(1.5, 6.0), 3)

    # Tarifa configurable por entorno, default 200 CLP/kWh
    tarifa = float(os.getenv("AHORRALUZ_IOT_TARIFA_CLP_KWH", "200"))
    costo_clp = int(consumo_kwh * tarifa)

    payload = {
        "usuario_id": str(usuario.id),
        "dispositivo_id": dispositivo_id,
        "fecha": fecha.isoformat(),         # "YYYY-MM-DD"
        "consumo_kwh": consumo_kwh,
        "costo_clp": costo_clp,
    }

    # ----------- 6) Llamar al endpoint IoT -----------
    url = f"{base_url}/api/iot/consumos/"
    print(f"\n➡️ Enviando POST a {url}")
    print(f"   JSON payload: {payload}")

    try:
        resp = requests.post(url, json=payload, timeout=5)
    except requests.RequestException as exc:
        print(f"❌ Error al llamar a la API: {exc}")
        sys.exit(1)

    print(f"\n⬅️ Status code: {resp.status_code}")
    print(f"   Respuesta: {resp.text}")

    if resp.ok:
        print("\n✅ Lectura registrada correctamente.")
        print("   Puedes verla entrando con ese usuario a /consumo/history/ y en el Dashboard.")
    else:
        print("\n⚠️ La API respondió con error, revisa logs en Django/Render.")


if __name__ == "__main__":
    main()

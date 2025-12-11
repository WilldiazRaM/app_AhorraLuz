# ⚡ AhorraLuz — Plataforma Web de Monitoreo y Predicción de Consumo Energético  
**Proyecto CAPSTONE – Ingeniería en Informática, DUOC UC (2025)**  
Desarrollado con **Django + PostgreSQL + ML + IoT Simulation**

---

## 🧭 Descripción General

**AhorraLuz** es una plataforma web diseñada para que los hogares puedan:

- Registrar su consumo eléctrico mensual o automático (IoT).
- Visualizar KPIs energéticos y métricas de ahorro.
- Recibir alertas y notificaciones cuando se detectan patrones de alto consumo.
- Obtener **predicciones de consumo** basadas en modelos de minería de datos.
- Administrar dispositivos eléctricos conectados.

Es un proyecto desarrollado como **Trabajo de Título (CAPSTONE 2025)** aplicando conocimientos de:

- Programación Web (Django)
- Bases de Datos relacionales (PostgreSQL)
- Seguridad informática
- Arquitectura de software
- Minería de datos y Machine Learning
- Gestión de proyectos TI

La aplicación está **desplegada en Render** y es totalmente funcional.

---

## 🌐 Demo en Producción

🔗 **https://app-ahorraluz.onrender.com**

> Incluye login, dashboard, historial de consumo, predicción de consumo y módulo administrativo (RBAC).

---

## 🚀 Características Principales

### ✔ Gestión completa de usuarios
- Registro e inicio de sesión mediante backend propio `AuthIdentidad` (bcrypt).
- Asociación automática con entidad interna `Usuario` (UUID).
- Perfil editable: nombre, comuna, dirección, tipo de vivienda.

### ✔ Registro de consumo eléctrico
- Ingreso manual de boletas mediante formulario validado.
- Ingreso automático vía **IoT** mediante endpoint público `/api/iot/consumos/`.

### ✔ Predicción energética (ML)
- Predicción de consumo diario/mensual usando modelos basados en patrones históricos.
- Métricas del modelo: MAE, RMSE, MAPE.

### ✔ Dashboard energético
Incluye:
- Últimos registros de consumo
- Métricas globales
- Comparación de precisión del modelo
- KPIs energéticos y económicos

### ✔ Sistema de alertas automáticas
- Alertas cuando se detecta consumo inusual.
- Notificaciones internas con categorías.

### ✔ Módulo administrativo (Backoffice)
Con control de acceso (RBAC):
- CRUD de usuarios, dispositivos, tipos, comunas, viviendas
- Auditoría completa del sistema

### ✔ Seguridad avanzada (Middleware)
Incluye middleware propio:
- Manejo global de excepciones
- CSP, HSTS, Permissions Policy
- X-Content-Type-Options, Referrer-Policy

---

## 🔌 Integración IoT – Simulador incluido

```bash
python iot_simulador.py
```

El script envía lecturas automáticas al backend Django usando datos del usuario y dispositivo configurados.

---

## 🛠️ Tecnologías Utilizadas

| Capa | Tecnología |
|------|------------|
| Backend | Django 5, Python 3 |
| Base de datos | PostgreSQL |
| Machine Learning | NumPy, Pandas, SciKit-Learn |
| Seguridad | bcrypt, middleware CSP/HSTS |
| Frontend | Bootstrap 5 |
| Despliegue | Render.com |

---

## 📊 Modelo de Datos (resumen)

Modelos principales:
- Usuario / AuthIdentidad / Perfil
- Dispositivo / TipoDispositivo
- RegistroConsumo
- PrediccionConsumo
- Notificacion
- AuditoriaEvento
- Catálogos: Comuna, TipoVivienda, NivelAlerta, TipoNotificacion

---

## 📂 Estructura del Proyecto

```plaintext
Aplicacion/
├── ahorraluz/
├── core/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── middleware.py
│   └── utils/
├── templates/
├── static/
├── iot_simulador.py
├── manage.py
├── render.yaml
└── requirements.txt
```

---

## 🧩 Instalación Local

```bash
git clone https://github.com/WilldiazRaM/AhorraLuz.git
cd Aplicacion
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## 👥 Equipo CAPSTONE

- **William Díaz Santander** – Backend, Arquitectura, BD, ML, Seguridad  
- **Álvaro Campos** – Frontend  
- **Alexander Palma** – Jefe de Proyecto  

Patrocinado por **DUOC UC – Ingeniería en Informática 2025**

---

## 📜 Licencia

Proyecto académico — libre para revisión como portafolio.

---

## ⭐ Contribuye

Si te gustó este proyecto, ¡deja una ⭐ en GitHub!

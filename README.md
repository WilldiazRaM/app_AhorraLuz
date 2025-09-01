# ⚡ App Web de Ahorro Energético para Hogares

##  Descripción General
La **App Web de Ahorro Energético para Hogares** es un proyecto académico desarrollado con **Django (Python)** y **PostgreSQL**, cuyo objetivo principal es ayudar a los usuarios a **registrar, monitorear y optimizar el consumo energético de sus hogares**.  

La aplicación ofrece estadísticas claras, predicciones de consumo, y recomendaciones personalizadas para fomentar el ahorro energético, en un contexto de **alzas tarifarias de electricidad en Chile**.

---

##  Objetivos Principales
1. Fomentar el ahorro energético en los hogares mediante recomendaciones basadas en el comportamiento del usuario.  
2. Proporcionar indicadores claros y medibles de consumo y ahorro.  
3. Incorporar técnicas de **minería de datos** para predecir patrones de alto consumo y alertar al usuario de forma preventiva.  

---
---

## 🌐 Demo en Producción

La aplicación se encuentra desplegada en Render y puede ser accedida desde el siguiente enlace:  

🔗 [App AhorraLuz – Producción](https://app-ahorraluz.onrender.com/)

> ⚠️ Nota: Esta es una versión inicial de la aplicación, pueden existir limitaciones de rendimiento o disponibilidad debido al plan gratuito de Render.

---




##  Funcionalidades (MVP v1.0)

- **Autenticación y autorización de usuarios** (usuarios y administradores).  
- **Gestión de perfil de usuario** con datos del hogar y dispositivos.  
- **Registro manual de consumo eléctrico** (kWh y costos).  
- **Dashboard principal** con KPIs:  
  - Consumo promedio mensual (kWh).  
  - Ahorro acumulado ($).  
  - Reducción estimada de huella de carbono (kg CO₂eq).  
- **Visualización del historial de consumo** (gráficos y tablas por día, semana, mes y año).  
- **Predicción de consumo energético** mediante minería de datos.  
- **Alertas y notificaciones** (ej: alto consumo, logros de ahorro).  
- **Cálculo de ahorro económico y reducción de huella de carbono** en métricas comprensibles.  
- **Administración de usuarios (Backoffice)** y gestión de roles (RBAC).  

---

## 🛡️ Requisitos No Funcionales (principales)

- Seguridad contra ataques comunes (SQL Injection, XSS, CSRF).  
- Cifrado de contraseñas y gestión segura de cookies/sesiones.  
- Validación y sanitización de entradas.  
- Base de datos normalizada (mínimo 3NF) con índices y mantenimiento automático.  
- Escalabilidad para integración futura con **ETL / BI**.  
- Métricas de rendimiento y alertas automáticas.  
- Interfaz web responsiva e intuitiva.  

---

## 🛠️ Tecnologías

- **Backend:** Python 3 + Django  
- **Base de datos:** PostgreSQL  
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap  
- **Minería de datos:** Scikit-learn, Pandas, NumPy  
- **BI / Reportes:** Power BI (integración futura)  
- **Control de versiones:** Git + GitHub
- **Proximamente integracion de Github Action:** para automatizar Pruebas Integracion y Unitarias

---

## 📂 Estructura del Repositorio (inicial)
```
ahorraluz/
├── ahorraluz/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── migrations/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── homepage/
├── venv/
├── __pycache__/
├── .env
├── .gitignore
├── manage.py
├── render.yaml
└── requirements.txt
```



---

## 📅 Cronograma de Entregables

- **Fase 1 (Agosto – Septiembre 2025):** Acta de Constitución, Requerimientos, Mockups.  
- **Fase 2 (Octubre – Noviembre 2025):** Desarrollo de la aplicación y modelo arquitectónico.  
- **Fase 3 (Diciembre 2025):** Presentación final ante comisión evaluadora.  

---

## 👥 Equipo de Proyecto CAPSTONE

- **Patrocinador Principal:** Fabián Enrique Saldano Pérez – Profesor DUOC UC  
- **Jefe de Proyecto:** Alexander Yerco Eduardo Palma Maldonado  
- **Gerente de Proyecto:** William Díaz Santander  

**Integrantes del Equipo de Desarrollo:**  
- Álvaro Campos – Desarrollo Frontend e Integración  
- Alexander Palma – Jefe de Proyecto / Coordinación  
- William Díaz – Backend y Gestión de Base de Datos  

---

## 🚀 Instalación y Uso (próximamente)

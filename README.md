# 🦷 DentalForce - Sistema de Gestión Odontológica

[![Django](https://img.shields.io/badge/Django-4.2.6-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

DentalForce es un sistema integral de gestión diseñado específicamente para clínicas dentales. Desarrollado con Django y PostgreSQL, ofrece una plataforma robusta y segura para administrar todos los aspectos operativos de tu clínica dental.

---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Módulos del Sistema](#-módulos-del-sistema)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Uso del Sistema](#-uso-del-sistema)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Testing](#-testing)
- [Seguridad](#-seguridad)
- [Mantenimiento](#-mantenimiento)
- [Solución de Problemas](#-solución-de-problemas)
- [Contribución](#-contribución)
- [Licencia](#-licencia)
- [Contacto](#-contacto)

---

## ✨ Características Principales

### 🏥 Gestión Clínica
- **Gestión de Citas**: Sistema de calendario intuitivo para programación de consultas
- **Historias Clínicas Electrónicas**: Acceso rápido al historial médico completo de pacientes
- **Tratamientos y Procedimientos**: Registro detallado de tratamientos odontológicos
- **Facturación Electrónica**: Generación automática de facturas y control financiero
- **Sistema de Comisiones**: Gestión de comisiones por dentista y especialidad (porcentaje o valor fijo)
- **Gestión de Dentistas**: CRUD completo con horarios, excepciones y múltiples sucursales

### 📦 Gestión de Inventario (INV)
- **Categorías y Subcategorías**: Organización jerárquica de productos
- **Marcas y Unidades de Medida**: Control detallado de proveedores y presentaciones
- **Control de Existencias**: Monitoreo en tiempo real de inventario
- **Alertas de Stock**: Notificaciones de productos con bajo inventario

### 🛒 Gestión de Compras (CMP)
- **Proveedores**: Administración completa de proveedores
- **Órdenes de Compra**: Creación y seguimiento de compras
- **Sistema de Descuentos Dual**: 
  - ✅ Descuento por **valor fijo** (monto directo)
  - ✅ Descuento por **porcentaje** (% sobre subtotal)
- **Actualización Automática de Inventario**: Sincronización en tiempo real
- **Precisión Decimal**: Cálculos con 2 decimales para exactitud contable

### 🔒 Seguridad
- **Autenticación de Usuarios**: Sistema de login seguro
- **Control de Permisos**: Roles y permisos granulares
- **Variables de Entorno**: Credenciales protegidas en archivos `.env`
- **Auditoría de Acciones**: Registro de todas las operaciones

### 📊 Reportes y Análisis
- **Dashboard Administrativo**: Vista general del estado de la clínica
- **Reportes de Inventario**: Análisis de stock y movimientos
- **Reportes Financieros**: Análisis de compras y ventas
- **Exportación de Datos**: Generación de reportes en múltiples formatos

---

## 🧩 Módulos del Sistema

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| **bases** | Autenticación, home, permisos base | ✅ Activo |
| **inv** | Inventario (categorías, productos, stock) | ✅ Activo |
| **cmp** | Compras (proveedores, órdenes, descuentos) | ✅ Activo |
| **fac** | Facturación y ventas | 🚧 Planificado |
| **pac** | Gestión de pacientes | 🚧 Planificado |
| **cit** | Sistema de citas | 🚧 Planificado |

---

## 🔧 Requisitos Previos

### Software Necesario
- **Python**: 3.12 o superior
- **PostgreSQL**: 12 o superior
- **pip**: Gestor de paquetes de Python
- **virtualenv** o **venv**: Para entornos virtuales (recomendado)

### Conocimientos Recomendados
- Python básico
- Django framework
- SQL y bases de datos relacionales
- HTML/CSS/JavaScript (para personalización de UI)

---

## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Xaler01/DentalForce.git
cd SisOdonOrbeDent
```

### 2. Crear y Activar Entorno Virtual
```bash
# Crear entorno virtual
python3 -m venv env

# Activar en macOS/Linux
source env/bin/activate

# Activar en Windows
env\Scripts\activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

**Dependencias Principales:**
- Django 4.2.6
- psycopg2-binary 2.9.9
- python-dotenv 1.0.0
- Pillow 10.1.0
- django-crispy-forms 2.1

### 4. Configurar Base de Datos PostgreSQL

**Crear Base de Datos:**
```sql
CREATE DATABASE orbedentbd1;
CREATE USER orbedent_user WITH PASSWORD 'tu_password_seguro';
ALTER ROLE orbedent_user SET client_encoding TO 'utf8';
ALTER ROLE orbedent_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE orbedent_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE orbedentbd1 TO orbedent_user;
```

### 5. Configurar Variables de Entorno

**Crear archivo `.env` en la raíz del proyecto:**
```env
# SEGURIDAD
SECRET_KEY=tu-secret-key-generada-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# BASE DE DATOS
DB_ENGINE=django.db.backends.postgresql_psycopg2
DB_NAME=orbedentbd1
DB_USER=orbedent_user
DB_PASSWORD=tu_password_seguro
DB_HOST=localhost
DB_PORT=5432

# JIRA Y CONFLUENCE (para agentes post-commit)
JIRA_URL=https://sistemaodontologico.atlassian.net
JIRA_EMAIL=tu-email@example.com
JIRA_API_TOKEN=tu-token-api-aqui
CONFLUENCE_URL=https://sistemaodontologico.atlassian.net/wiki
```

**Generar SECRET_KEY:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

> **Nota:** Las variables de Jira/Confluence son opcionales. Los agentes post-commit las usan para actualizar automáticamente las tareas en Jira y sincronizar con Confluence después de cada commit.

### 6. Aplicar Migraciones
```bash
python manage.py migrate
```

### 7. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 8. Cargar Datos Iniciales (Opcional)
```bash
# Si tienes fixtures
python manage.py loaddata fixtures/initial_data.json
```

### 9. Ejecutar Servidor de Desarrollo
```bash
python manage.py runserver
```

**Acceder a:**
- Frontend: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

---

## 💼 Uso del Sistema

### Acceso Inicial
1. Navega a http://127.0.0.1:8000/
2. Inicia sesión con el superusuario creado
3. Accede al panel administrativo

### Configuración de Inventario
1. **Crear Categorías**: Admin → INV → Categorías
2. **Crear Subcategorías**: Asignar a categorías existentes
3. **Agregar Marcas**: Registrar marcas de productos
4. **Definir Unidades**: Crear unidades de medida (caja, unidad, etc.)
5. **Registrar Productos**: Crear productos con todos los atributos

### Gestión de Compras
1. **Registrar Proveedores**: Admin → CMP → Proveedores
2. **Crear Orden de Compra**:
   - Seleccionar proveedor
   - Agregar productos al detalle
   - Elegir tipo de descuento (Valor o Porcentaje)
   - El inventario se actualiza automáticamente
3. **Consultar Compras**: Listado completo de órdenes

### Sistema de Descuentos
#### Descuento por Valor
- Selecciona "Valor" en el tipo de descuento
- Ingresa el monto fijo a descontar (ej: $50.00)
- Total = Subtotal - Descuento

#### Descuento por Porcentaje
- Selecciona "Porcentaje" en el tipo de descuento
- Ingresa el porcentaje (ej: 10 para 10%)
- Descuento = Subtotal × (Porcentaje / 100)
- Total = Subtotal - Descuento calculado

**Nota:** Todos los cálculos se redondean a 2 decimales para exactitud contable.

---

## 📁 Estructura del Proyecto

```
SisOdonOrbeDent/
├── bases/                  # Módulo base (autenticación, home)
│   ├── templates/
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── cmp/                    # Módulo de compras
│   ├── templates/
│   │   └── cmp/
│   │       ├── compras.html         # Form de compras con descuentos
│   │       ├── compras_list.html
│   │       └── proveedor_list.html
│   ├── models.py           # Proveedor, ComprasEnc, ComprasDet
│   ├── views.py            # Lógica de compras y descuentos
│   ├── forms.py
│   ├── tests.py            # 23 tests unitarios
│   └── urls.py
├── inv/                    # Módulo de inventario
│   ├── templates/
│   ├── models.py           # Categoria, SubCategoria, Marca, UnidadMedida, Producto
│   ├── views.py
│   ├── tests.py            # 10 tests unitarios
│   └── urls.py
├── dentalforce/              # Configuración del proyecto
│   ├── settings.py         # Configuración con variables de entorno
│   ├── urls.py
│   └── wsgi.py
├── static/                 # Archivos estáticos
│   └── base/
│       ├── css/
│       ├── js/
│       └── vendor/         # Bootstrap, jQuery, DataTables
├── templates/              # Templates globales
│   └── base/
│       └── base.html       # Template principal
├── env/                    # Entorno virtual (no en Git)
├── .env                    # Variables de entorno (no en Git)
├── .env.example            # Template de variables
├── .gitignore
├── manage.py
├── requirements.txt
├── db.sqlite3              # BD de desarrollo (usar PostgreSQL en producción)
└── README.md
```

---

## 🧪 Testing

### Ejecutar Todos los Tests
```bash
python manage.py test
```

**Resultado Esperado:**
```
Ran 33 tests in 0.159s
OK
```

### Tests por Módulo
```bash
# Tests de Compras (23 tests)
python manage.py test cmp

# Tests de Inventario (10 tests)
python manage.py test inv

# Tests específicos de descuentos (8 tests)
python manage.py test cmp.tests.ComprasDetDescuentosTest
```

### Cobertura de Tests
| Módulo | Tests | Cobertura |
|--------|-------|-----------|
| CMP - Descuentos | 8 | Valor, Porcentaje, Redondeo, Cambios |
| CMP - Modelos | 15 | Proveedor, ComprasEnc, ComprasDet |
| INV - Modelos | 10 | Categoria, Producto, Marca, etc. |
| **TOTAL** | **33** | **100% modelos críticos** |

### Agregar Nuevos Tests
Ejemplo de test para compras:
```python
from django.test import TestCase
from cmp.models import ComprasDet

class MiNuevoTest(TestCase):
    def test_mi_funcionalidad(self):
        # Tu código de prueba aquí
        self.assertEqual(resultado, esperado)
```

---

## 🔒 Seguridad

### ⚠️ IMPORTANTE: Antes de Producción

**Archivo `.env` para Producción:**
```env
SECRET_KEY=<generar-nueva-clave-fuerte>
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

DB_NAME=orbedentbd1_prod
DB_USER=orbedent_app
DB_PASSWORD=<password-fuerte-16+caracteres>
DB_HOST=<host-produccion>
DB_PORT=5432
```

### Verificación de Seguridad
```bash
# Verificar configuración de producción
python manage.py check --deploy
```

### Configuraciones Adicionales para Producción
En `settings.py`, agregar al final:
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

### Mejores Prácticas
- ✅ **NUNCA** commitear el archivo `.env`
- ✅ Usar contraseñas fuertes (16+ caracteres)
- ✅ Rotar credenciales cada 90 días
- ✅ Mantener dependencias actualizadas
- ✅ Hacer backups regulares de la base de datos
- ✅ Revisar logs de seguridad semanalmente

---

## 🔧 Mantenimiento

### Actualizar Dependencias
```bash
# Listar paquetes desactualizados
pip list --outdated

# Actualizar un paquete específico
pip install --upgrade django

# Actualizar requirements.txt
pip freeze > requirements.txt
```

### Crear Migraciones
```bash
# Después de modificar models.py
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver migraciones pendientes
python manage.py showmigrations
```

### Backups de Base de Datos
```bash
# Crear backup
pg_dump -U orbedent_user orbedentbd1 > backup_$(date +%Y%m%d).sql

# Restaurar backup
psql -U orbedent_user orbedentbd1 < backup_20251110.sql
```

### Recolectar Archivos Estáticos (Producción)
```bash
python manage.py collectstatic --noinput
```

### Limpiar Sesiones Expiradas
```bash
python manage.py clearsessions
```

---

## 🐛 Solución de Problemas

### Error: "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Error: "relation does not exist"
```bash
# Aplicar migraciones
python manage.py migrate
```

### Error: "FATAL: password authentication failed"
- Verificar credenciales en `.env`
- Verificar que el usuario de PostgreSQL existe
- Revisar `pg_hba.conf` en PostgreSQL

### Error: "django.db.utils.OperationalError: FATAL: database does not exist"
```bash
# Crear base de datos
psql -U postgres
CREATE DATABASE orbedentbd1;
\q
```

### Error 404 al eliminar detalle de compra
- Verificar que la URL esté configurada en `cmp/urls.py`
- URL esperada: `/cmp/compras/delete/<pk_compra>/<pk_detalle>`

### Descuentos no se calculan correctamente
- Verificar campo `tipo_descuento` en ComprasDet ('V' o 'P')
- Revisar JavaScript en `compras.html` para cálculos dinámicos
- Verificar método `save()` en modelo ComprasDet

### Tests Fallan
```bash
# Ver detalles de error
python manage.py test --verbosity=2

# Test específico
python manage.py test cmp.tests.ComprasDetDescuentosTest.test_descuento_por_porcentaje
```

---

## 🤝 Contribución

### Cómo Contribuir
1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/NuevaFuncionalidad`)
3. **Commit** tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/NuevaFuncionalidad`)
5. **Abre** un Pull Request

### Estándares de Código
- Seguir [PEP 8](https://www.python.org/dev/peps/pep-0008/) para Python
- Agregar docstrings a funciones y clases
- Escribir tests para nuevas funcionalidades
- Mantener cobertura de tests > 80%

### Reportar Bugs
Usa el [issue tracker](https://github.com/Xaler01/DentalForce/issues) e incluye:
- Descripción detallada del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Screenshots (si aplica)
- Versión de Python y Django

---

## 📝 Notas de Desarrollo

### Funcionalidades Recientes (Noviembre 2025)
- ✅ Sistema dual de descuentos (valor/porcentaje) en compras
- ✅ Precisión de 2 decimales en cálculos financieros
- ✅ Migración de credenciales a variables de entorno
- ✅ 33 tests unitarios (100% pasando)
- ✅ Auditoría de seguridad completa
- ✅ Documentación exhaustiva

### Próximas Funcionalidades Planificadas
- 🚧 Módulo de Pacientes
- 🚧 Sistema de Citas
- 🚧 Módulo de Facturación
- 🚧 Reportes avanzados con gráficos
- 🚧 API REST para integraciones
- 🚧 Aplicación móvil

### Recordatorios para Retomar el Proyecto
1. **Activar entorno virtual**: `source env/bin/activate`
2. **Verificar dependencias**: `pip list`
3. **Ejecutar tests**: `python manage.py test`
4. **Iniciar servidor**: `python manage.py runserver`
5. **Revisar migraciones pendientes**: `python manage.py showmigrations`
6. **Actualizar dependencias**: Verificar `pip list --outdated`

### Base de Datos de Desarrollo
- **BD Actual**: orbedentbd1
- **Usuario**: urbinaf (solo desarrollo)
- **Puerto**: 5432
- **Datos de prueba**: Crear con admin o fixtures

---

## 📄 Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

```
MIT License

Copyright (c) 2025 DentalForce

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 📞 Contacto

### Desarrollador
- **Email**: [xaler01@proton.me](mailto:xaler01@proton.me)
- **GitHub**: [@Xaler01](https://github.com/Xaler01)
- **Repositorio**: [DentalForce](https://github.com/Xaler01/DentalForce)

### Soporte
Para preguntas, sugerencias o reportar problemas:
1. Abre un [Issue](https://github.com/Xaler01/DentalForce/issues)
2. Envía un email a [xaler01@proton.me](mailto:xaler01@proton.me)
3. Revisa la [documentación](README.md)

---

## 🙏 Agradecimientos

- **Django Software Foundation** - Por el excelente framework
- **Bootstrap Team** - Por el framework CSS
- **SB Admin 2** - Por el template administrativo
- **Comunidad Open Source** - Por las bibliotecas y herramientas

---

## 📊 Estado del Proyecto

**Versión Actual**: 1.0.0  
**Última Actualización**: Noviembre 10, 2025  
**Estado**: ✅ En Desarrollo Activo  
**Tests**: 33/33 Pasando (100%)  
**Cobertura de Tests**: ~85%  
**Rama Actual**: `developcmp`

---

**⭐ Si este proyecto te resulta útil, considera darle una estrella en GitHub!**
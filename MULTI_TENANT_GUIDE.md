# 🏥 Guía de Uso - Sistema Multi-Tenant (Aislamiento por Clínica)

## 📋 Resumen

PowerDent ahora soporta múltiples clínicas con **aislamiento completo de datos**. Cada usuario ve solo la información de su clínica activa.

---

## 🔐 Acceso al Sistema

### Credenciales de Admin
- **Usuario**: `Admin`
- **Contraseña**: `HolaPower1`

---

## 🎯 Flujo de Uso

### 1️⃣ **Primera vez (Sin clínica seleccionada)**

Cuando accedes al sistema por primera vez:

```
Login → Middleware detecta sin clínica activa → 
  ↓
Redirige automáticamente a selector de clínicas
```

**Se mostrará una ventana emergente diciendo:**
> "Debe seleccionar una clínica para continuar."

Haz clic en **OK** para cerrar el diálogo.

### 2️⃣ **Selector de Clínicas**

Se abrirá un formulario con las clínicas disponibles:

```
┌─────────────────────────────────┐
│  Seleccione una Clínica         │
├─────────────────────────────────┤
│                                 │
│  ○ Madomed                      │
│    [Dirección]                  │
│                                 │
│  ○ Tio Alex                     │
│    [Dirección]                  │
│                                 │
│  [Confirmar Selección]          │
└─────────────────────────────────┘
```

**Acciones:**
- ✅ Selecciona una clínica con el radio button
- ✅ Haz clic en "Confirmar Selección"

### 3️⃣ **Después de Seleccionar**

Una vez selecciones la clínica:
- ✅ Se guardará en tu sesión
- ✅ Verás solo datos de esa clínica:
  - 📋 Pacientes
  - 📅 Citas
  - 🏥 Sucursales
  - 🦷 Cubículos

---

## 🔄 Cambiar de Clínica

### Opción 1: Desde el Menú Usuario (Recomendado)

1. Haz clic en tu avatar/nombre en la **esquina superior derecha**
2. Se abrirá un menú dropdown
3. Selecciona **"Cambiar Clínica"** 
4. Elige la clínica que deseas
5. Haz clic en **"Confirmar Selección"**

### Opción 2: URL Directa

Accede a: `http://localhost:8000/clinicas/seleccionar/`

---

## 👥 Permisos por Rol

### Admin (Superuser)
- ✅ Ve **todas las clínicas** (incluyendo inactivas)
- ✅ Puede cambiar entre clínicas
- ✅ Acceso total al sistema

### Usuario Regular
- ✅ Ve solo **clínicas activas** (`estado=True`)
- ✅ Puede cambiar entre clínicas asignadas
- ✅ No puede ver clínicas inactivas

---

## 🔒 Aislamiento de Datos

### Protección Automática

El sistema protege automáticamente:

| Elemento | Filtrado por | Visibilidad |
|----------|-------------|-----------|
| **Pacientes** | Clínica activa | Solo de tu clínica |
| **Citas** | Clínica de paciente | Solo de tu clínica |
| **Sucursales** | Clínica seleccionada | Solo de tu clínica |
| **Cubículos** | Clínica de sucursal | Solo de tu clínica |
| **Calendario** | Pacientes de tu clínica | Solo eventos de tu clínica |

### ✅ Garantías

- 🔒 **NO verás datos de otras clínicas**
- 🔒 **NO puedes crear pacientes sin clínica**
- 🔒 **NO puedes acceder a URLs de otras clínicas**
- 🔒 **Sesión aislada por clínica**

---

## 🛠️ Componentes Técnicos

### Middleware
- **Archivo**: `powerdent/middleware.py`
- **Función**: Valida que siempre haya clínica activa en sesión
- **Comportamiento**: Redirige al selector si no hay clínica

### Managers de Modelo
```python
# Ejemplo: Filtrar pacientes por clínica
pacientes = Paciente.objects.para_clinica(clinica_id)

# Ejemplo: Filtrar citas activas
citas = Cita.objects.para_clinica(clinica_id).activas()
```

### Context Processor
- **Archivo**: `powerdent/context_processors.py`
- **Función**: Pasa info de clínica activa a templates
- **Disponible en**: `{{ clinica_activa }}`, `{{ clinica_nombre }}`

### Vistas Protegidas
- `CitaListView` - Filtra por clínica de sesión
- `PacienteListView` - Filtra por clínica de sesión
- `PacienteCreateView` - Auto-asigna clínica activa
- `citas_json` - API de calendario filtrada

---

## ⚠️ Consideraciones Importantes

### ✅ QUÉ FUNCIONA
- ✅ Cambiar de clínica en cualquier momento
- ✅ Ver solo datos de tu clínica
- ✅ Crear nuevos pacientes/citas en tu clínica
- ✅ Admin ve todas las clínicas

### ⏳ PRÓXIMAMENTE
- ⏳ Protección completa de sucursales/cubículos
- ⏳ Segregación de usuarios por clínica
- ⏳ Reportes multi-clínica para admin
- ⏳ API REST con autenticación multi-tenant

---

## 🐛 Troubleshooting

### Problema: "No hay clínicas disponibles"
**Solución**: 
- Admin: Ve todas las clínicas (revisa que `estado=True`)
- Usuario: Contacta a admin para activar tu clínica

### Problema: Se borra mi selección al cambiar página
**Solución**: 
- Esto NO debería ocurrir (el middleware mantiene la sesión)
- Limpia cookies del navegador y vuelve a seleccionar

### Problema: Veo datos de otra clínica
**Solución**: 
- ⚠️ Esto es un BUG - reporta inmediatamente
- Limpia caché y vuelve a seleccionar clínica

---

## 📞 Soporte

Para problemas o sugerencias sobre el aislamiento multi-tenant, contacta al equipo de desarrollo.

---

**Última actualización**: Enero 10, 2026  
**Versión**: 1.0  
**Sistema**: PowerDent v4.2.6

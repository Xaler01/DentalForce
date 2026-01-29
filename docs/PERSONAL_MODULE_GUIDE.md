# Módulo de Personal - Guía de Uso

## 📍 Ubicación en el Menú
**Menú Lateral → Administración → Personal**

El módulo Personal incluye las siguientes opciones:
- **Lista de Personal**: Gestión de empleados administrativos
- **Horas Extra**: Registro y seguimiento de horas extra
- **Aprobar Horas**: Aprobación masiva de registros pendientes
- **Nómina Mensual**: Reporte detallado de nómina con horas extra

---

## 🎯 Funcionalidades Implementadas

### 1. Lista de Personal
**URL**: `/personal/`

**Descripción**: Visualiza todo el personal administrativo (auxiliares y otros empleados).

**Filtros disponibles**:
- Por Clínica
- Por Sucursal

**Información mostrada**:
- Nombre completo
- Usuario
- Clínica y Sucursal asignada
- Cargo (Auxiliar/Administrativo)
- Salario mensual
- Tarifa por hora calculada automáticamente

**Cálculo de tarifa/hora**:
```
Tarifa/Hora = Salario Mensual / 240 horas
```
Basado en: 30 días × 8 horas = 240 horas mensuales

---

### 2. Registro de Horas Extra
**URL**: `/personal/horas-extra/`

**Descripción**: Visualiza todos los registros de horas extra con estadísticas en tiempo real.

**Estadísticas mostradas**:
- Total pendientes de aprobación (badge amarillo)
- Total aprobados (badge verde)
- Total rechazados (badge rojo)

**Filtros disponibles**:
- Por Estado (Pendiente/Aprobado/Rechazado)
- Por Clínica
- Por Sucursal
- Por Mes
- Por Año

**Información de cada registro**:
- Fecha
- Personal
- Clínica y Sucursal
- Horas normales trabajadas
- Horas al 25% (lunes a viernes 19:00-24:00)
- Horas al 50% (sábados y feriados)
- Horas al 100% (domingos)
- Valor total calculado
- Estado con badge de color

**Cálculos automáticos**:
- Horas 25%: Tarifa base × 1.25
- Horas 50%: Tarifa base × 1.50
- Horas 100%: Tarifa base × 2.00

---

### 3. Aprobación Masiva
**URL**: `/personal/horas-extra/aprobar-masiva/`

**Descripción**: Permite aprobar o rechazar múltiples registros de horas extra a la vez.

**Características**:
- Checkbox "Seleccionar todos"
- Filtros por Clínica, Sucursal, Mes y Año
- Radio buttons para Aprobar/Rechazar
- Campo de observaciones compartido para todos los registros seleccionados
- Solo muestra registros en estado PENDIENTE

**Proceso**:
1. Aplicar filtros si es necesario
2. Seleccionar registros con checkboxes
3. Elegir acción (Aprobar/Rechazar)
4. Agregar observaciones (opcional)
5. Clic en "Procesar Seleccionados"

**Resultado**:
- Se actualiza el estado de todos los registros seleccionados
- Se registra quién aprobó/rechazó y la fecha
- Se agregan observaciones si fueron ingresadas

---

### 4. Reporte de Nómina Mensual
**URL**: `/personal/nomina/reporte/`

**Descripción**: Genera un reporte completo de nómina con cálculos de horas extra aprobadas.

**Filtros disponibles**:
- Mes (selector con nombres de meses)
- Año (campo numérico)
- Clínica
- Sucursal

**Tarjetas de resumen** (parte superior):
1. **Total Salarios Base**: Suma de todos los salarios mensuales
2. **Total Horas Extra**: Suma del valor de todas las horas extra aprobadas
3. **Total Horas Trabajadas**: Total de horas extra trabajadas en el mes
4. **Total a Pagar**: Salarios + Horas Extra

**Tabla detallada**:
Por cada empleado muestra:
- Nombre
- Clínica y Sucursal
- Salario base
- Horas normales trabajadas
- Horas al 25%
- Horas al 50%
- Horas al 100%
- Valor total de horas extra
- **Total a pagar** (salario + horas extra)

**Totales generales** (pie de tabla):
- Suma de todos los conceptos
- Fondo oscuro para destacar

**Funciones adicionales**:
- Botón "Imprimir" (elimina filtros en impresión)
- Diseño responsive para pantalla e impresión
- Solo incluye horas extra con estado APROBADO

---

## 📊 Cumplimiento Normativo Ecuador

### Salario Básico Unificado (SBU) 2026
**$482.00** mensuales

### Cálculo de Horas Mensuales
```
30 días × 8 horas/día = 240 horas/mes
```

### Factores de Horas Extra (Código de Trabajo Ecuador)

| Tipo | Cuándo | Factor | Cálculo |
|------|--------|--------|---------|
| **Horas Normales** | Horas regulares adicionales | 1.00 | Tarifa base |
| **Horas 25%** | Lunes-Viernes 19:00-24:00 | 1.25 | Tarifa × 1.25 |
| **Horas 50%** | Sábados y feriados | 1.50 | Tarifa × 1.50 |
| **Horas 100%** | Domingos | 2.00 | Tarifa × 2.00 |

### Ejemplo de Cálculo
```
Personal: Juan Pérez
Salario mensual: $482.00
Tarifa/hora: $482 / 240 = $2.01

Horas extra del mes:
- 5 horas normales    = 5 × $2.01 × 1.00 = $10.05
- 4 horas al 25%      = 4 × $2.01 × 1.25 = $10.05
- 6 horas al 50%      = 6 × $2.01 × 1.50 = $18.09
- 2 horas al 100%     = 2 × $2.01 × 2.00 = $8.04

Total horas extra: $46.23
Total a pagar: $482.00 + $46.23 = $528.23
```

---

## 🔄 Flujo de Trabajo Recomendado

### Mensual (día 1-26)
1. **Empleados** registran horas extra en `/personal/horas-extra/nuevo/`
2. Sistema calcula valores automáticamente
3. Registros quedan en estado PENDIENTE

### Fin de Mes (día 27-30)
4. **Administrador** ingresa a `/personal/horas-extra/aprobar-masiva/`
5. Revisa registros del mes actual
6. Aprueba o rechaza masivamente con observaciones
7. Genera reporte de nómina en `/personal/nomina/reporte/`
8. Exporta o imprime para contabilidad

---

## 🎨 Códigos de Color

### Estados de Horas Extra
- 🟡 **Amarillo (Warning)**: Pendiente de aprobación
- 🟢 **Verde (Success)**: Aprobado
- 🔴 **Rojo (Danger)**: Rechazado

### Cargos de Personal
- 🔵 **Azul (Info)**: Auxiliar dental
- ⚫ **Gris (Secondary)**: Administrativo

---

## 📱 Características Técnicas

### Seguridad
- LoginRequiredMixin en todas las vistas
- Registro de auditoría (quién aprobó/rechazó y cuándo)
- Relación con usuario en modificaciones

### Performance
- `select_related()` para reducir consultas a BD
- Filtros optimizados con índices
- Paginación automática si hay muchos registros

### UX/UI
- Bootstrap 4 para diseño responsive
- FontAwesome 5 para iconos
- Filtros persistentes en URL (compartibles)
- Botones de acción con tooltips
- Tablas ordenables y scrolleables

---

## 🚀 Próximas Mejoras Sugeridas

1. **Alertas automáticas** (día 27-30) para recordar aprobar horas extra
2. **Dashboard** de Personal con gráficos de horas extra por mes
3. **Exportación a Excel** de reportes de nómina
4. **Notificaciones** cuando se aprueba/rechaza un registro
5. **Historial** de cambios en aprobaciones
6. **Límites** de horas extra configurables por cargo

---

**Última actualización**: 29/01/2026  
**Versión del módulo**: 2.0  
**Desarrollador**: PowerDent Team

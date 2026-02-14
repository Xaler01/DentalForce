# Instrucciones para GitHub Copilot Agent - DentalForce

## Agente de Seguridad Pre-Commit

### Objetivo
Revisar todos los archivos que se van a incluir en un commit para garantizar que no se suban credenciales, información sensible o archivos de configuración privada a repositorios públicos.

### Alcance de Revisión

Este agente debe revisar TODOS los archivos staged antes de realizar un commit y verificar que NO contengan:

#### 1. Credenciales de Servicios Externos
- **Jira**: API tokens, emails, URLs de proyectos con tokens embebidos
- **Bases de Datos**: Strings de conexión, usuarios, contraseñas, hosts, puertos
- **Servicios de Pago**: 
  - PayPal: Client ID, Secret, tokens de sandbox/producción
  - Criptomonedas: Claves privadas, seeds, API keys de exchanges
- **Servicios Cloud**: AWS keys, Azure credentials, Google Cloud tokens
- **APIs de terceros**: Cualquier API key, secret o token de autenticación

#### 2. Información Personal Identificable (PII)
- Emails personales o corporativos (excepto emails de ejemplo/demo)
- Números de teléfono reales
- Direcciones físicas
- Números de identificación (cédulas, pasaportes, etc.)
- Información médica de pacientes reales

#### 3. Configuraciones Privadas
- Archivos `settings_local.py`, `local_settings.py`
- Variables de entorno con valores reales (`.env` con credenciales)
- Certificados SSL/TLS privados
- Claves SSH privadas
- Tokens de sesión o JWT con información real

#### 4. Archivos de Copilot Props
- Prompts personalizados que contengan información del proyecto
- Instrucciones con datos sensibles del negocio
- Configuraciones de agentes con credenciales

### Estructura de Carpetas Seguras

Los siguientes archivos/carpetas están en `.gitignore` y deben permanecer locales:

```
.copilot-workspace/  # Salidas de GitHub Copilot: prompts, documentación generada, análisis
.env                 # Variables de entorno
settings_local.py    # Configuraciones locales de Django
db.sqlite3          # Base de datos de desarrollo
media/              # Archivos multimedia (pueden contener datos de pacientes)
*.csv               # Archivos CSV que pueden contener datos sensibles
```

**Nota:** Anteriormente esta carpeta se llamaba `.jira-docs/`. Se renombró a `.copilot-workspace/` para reflejar su propósito más amplio como repositorio de salidas de agentes GitHub Copilot.

#### Contenido de `.copilot-workspace/`

Esta carpeta contiene archivos generados por agentes GitHub Copilot y documentación auxiliar:

**Documentación de uso único (se genera por sesión):**
- `prompts/` - Prompts personalizados para agentes
- `RESUMEN_SESION_*.md` - Resúmenes de sesiones de trabajo
- `ACTUALIZACIÓN_*.md` - Cambios y actualizaciones por fecha
- `PLAN_*.md` - Planes de implementación para características específicas
- `GUION_PRUEBAS_*.md` - Guiones de prueba generados

**Documentación relevante para nuevo personal:**
- `DocCompleta/` - Carpeta con documentación consolidada del proyecto
  - Guías de arquitectura, módulos, APIs
  - Especificaciones técnicas mantenidas
  - Referencias de seguridad y mejores prácticas
   - `agentes/` - Subcarpeta con instrucciones de agentes
- `scripts/` - Scripts auxiliares de configuración y migración
- `QUICKSTART.md` - Guía rápida de inicio

**Archivos de configuración y sincronización:**
- (Anteriormente `.jira-docs/`) Configuraciones locales
- Archivos de agentes: `DocCompleta/agentes/AGENTE_*.md` (instrucciones específicas)
- Historiales de tickets y cambios

### Proceso de Revisión

1. **Verificar carpeta `.copilot-workspace/`**
   - Confirmar que archivos no suban a `.copilot-workspace/` (la carpeta está en `.gitignore`)
   - Esta carpeta es local y contiene salidas de agentes Copilot

2. **Listar archivos staged**
   ```bash
   git diff --cached --name-only
   ```

3. **Para cada archivo, buscar patrones sensibles:**
   - Tokens API: `API_TOKEN`, `API_KEY`, `SECRET`, `TOKEN`
   - Emails: Patrones de email que no sean ejemplos
   - URLs con credenciales: `https://usuario:password@...`
   - Passwords: `PASSWORD`, `PASSWD`, `PWD`
   - Database strings: `postgresql://`, `mysql://`, `mongodb://`
   - IP addresses privadas: `192.168.x.x`, `10.x.x.x`

4. **Verificar extensiones de archivos sensibles:**
   - `.env` (solo si tiene valores reales)
   - `.pem`, `.key`, `.p12`, `.pfx` (certificados)
   - `.csv` con datos de producción
   - Backups de BD: `.sql`, `.dump`

5. **Revisar contenido de archivos Python:**
   ```python
   # PATRONES PROHIBIDOS:
   JIRA_API_TOKEN = "ATATT3x..."  # ❌ Token real
   DATABASE_PASSWORD = "<REPLACE_WITH_ENV_VAR>"  # ❌ Password real (ejemplo, usar variable de entorno)
   PAYPAL_SECRET = "xxxxx"  # ❌ Credencial de pago
   
   # PATRONES PERMITIDOS:
   JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN')  # ✅ Desde variable de entorno
   DATABASE_PASSWORD = os.getenv('DB_PASSWORD')  # ✅ Desde variable de entorno
   ```

### Acciones del Agente

#### Si NO se encuentran problemas:
```
✅ Revisión de seguridad completada
📋 Archivos revisados: X
🔒 No se encontraron credenciales o información sensible
➡️  Procediendo con el siguiente agente de commits...
```

#### Si SE encuentran problemas:
```
⚠️  ALERTA DE SEGURIDAD - Commit bloqueado

📛 Se encontraron los siguientes problemas:

Archivo: scripts/config.py
  Línea 10: JIRA_API_TOKEN contiene un token real
  Línea 15: DATABASE_URL contiene credenciales

Archivo: utils/payment.py
  Línea 5: PAYPAL_SECRET_KEY expuesta

🛠️  ACCIONES REQUERIDAS:

1. Mover 'scripts/config.py' a carpeta segura según tipo:
   - Archivos de configuración de agentes → .copilot-workspace/
   - Configuraciones DB → Usar settings_local.py
   - Credenciales de pago → Variables de entorno

2. Reemplazar valores hardcodeados por:
   import os
   JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN')

3. Agregar archivos sensibles a .gitignore

4. Limpiar el historial si ya se subieron:
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch ruta/archivo' HEAD

❌ Commit CANCELADO por seguridad
```

### Integración con Siguiente Agente

Una vez completada la revisión exitosamente, el agente debe:

1. **Crear un resumen de archivos seguros:**
   ```json
   {
     "status": "approved",
     "files_reviewed": 15,
     "files_safe": 15,
     "timestamp": "2025-11-15T10:30:00Z",
     "next_agent": "commit-agent"
   }
   ```

2. **Pasar el control al agente de commits con:**
   - Lista de archivos aprobados
   - Sugerencias de mensaje de commit basadas en los cambios
   - Confirmación de que se puede proceder
   - Linkeo automático con GitHub Issues (#123) si se menciona en el commit

### Reglas del Agente de Commits (Horario Ecuador) - ACTUALIZADO 2026-02-12

El agente de commits **debe bloquear** cualquier commit o push a ramas de desarrollo en el siguiente horario:

- **Zona horaria**: Ecuador (UTC-5)
- **Días de Semana**: Lunes a Viernes
- **Horario restringido**: 08:30 a 20:00 (ACTUALIZADO: antes era 08:30-18:30)

**Importante**: Este proyecto usa **GitHub Projects** (herramienta nativa de GitHub) para gestión de tareas, NO Jira.

**Reglas obligatorias NUEVAS**:

1. **Commits BLOQUEADOS en:**
   - Lunes a Viernes, 08:30 - 20:00 (Hora Ecuador UTC-5)
   - Ramas afectadas: `develop`, `release/*`, `staging/*`, `hotfix/*`
   - Excepto: Si es un día feriado (aplica TODO EL DÍA - commits permitidos)

2. **Commits PERMITIDOS en:**
   - ✅ Antes de 08:30 AM (Hora Ecuador)
   - ✅ Después de 20:00 (Hora Ecuador)
   - ✅ Sábados (24 horas completas)
   - ✅ Domingos (24 horas completas)
   - ✅ Días feriados en Ecuador (TODO EL DÍA)
   - ✅ Rama `main` siempre (con revisión)
   - ✅ Rama `feature/*` local (sin restricciones)

3. **Días Feriados 2026 (Commits permitidos TODO EL DÍA):**
   - Lunes 17 febrero - Carnaval
   - Martes 18 febrero - Carnaval
   - Viernes 10 de abril - Viernes Santo
   - Viernes 1 de mayo - Día del Trabajo
   - Jueves 28 de mayo - Corpus Christi
   - Lunes 10 de agosto - García Moreno
   - Lunes 2 de noviembre - Día de Difuntos
   - Martes 3 de noviembre - Independencia de Cuenca
   - Viernes 25 de diciembre - Navidad

4. **Validación requerida:**
   - El agente debe validar la hora actual de Ecuador **ANTES** de permitir commit/push
   - Si está bloqueado, mostrar: ✅ próximo horario permitido
   - Registrar en logs todos los bloqueos e intentos
   - Mostrar mensaje claro del motivo del bloqueo

**Ejemplo de Mensaje de Bloqueo:**
```
❌ COMMIT BLOQUEADO
   Rama: develop
   Motivo: Horario restringido TRABAJO (08:30 - 20:00 Ecuador UTC-5)
   Hora Actual Ecuador: 2026-02-12 14:30
   Próximo slot permitido: 2026-02-12 20:00 (en 5.5 horas)
   
   ℹ️  Commits permitidos:
      ✅ Fuera de horario: antes de 08:30 o después de 20:00
      ✅ Fines de semana: Sábados y Domingos
      ✅ Días feriados: Aplica TODO EL DÍA
      
   💡 Tip: Puedes hacer commit en 5.5 horas o esperar al fin de semana
```

**Ejemplo de Mensaje de Aprobación (Feriado):**
```
✅ COMMIT PERMITIDO
   Rama: develop
   Motivo: Día festivo - Carnaval 🎉
   Fecha: 2026-02-17
   
   Procede con el commit normalmente
```

### Configuración de Categorías de Archivos

```yaml
carpetas_seguras:
  copilot_workspace:
    destino: .copilot-workspace/
    patrones: ["*agente*", "*sesion*", "*resumen*", "*.prompt*"]
    
  database:
    destino: settings_local.py
    patrones: ["DATABASE_*", "DB_*", "postgresql://", "mysql://"]
    
  pagos:
    destino: .env (como variables)
    patrones: ["PAYPAL_*", "STRIPE_*", "CRYPTO_*", "*_SECRET*", "*_KEY*"]
    
  servidores:
    destino: .env (como variables)
    patrones: ["SSH_*", "SERVER_*", "HOST=", "PORT="]
    
  personal:
    destino: Excluir del repo
    patrones: ["*.csv", "pacientes_*", "*.xlsx con datos reales"]
```

### Ejemplo de Uso

```bash
# El usuario ejecuta:
git add .

# El agente de seguridad automáticamente:
# 1. Revisa todos los archivos en staging
# 2. Busca patrones sensibles
# 3. Si encuentra problemas:
#    - Bloquea el commit
#    - Muestra lista de problemas
#    - Sugiere soluciones
# 4. Si todo está bien:
#    - Aprueba los archivos
#    - Pasa control al agente de commits
```

### Excepciones Permitidas

Archivos que pueden contener "credenciales" de ejemplo:
- `README.md` con ejemplos claramente marcados como EJEMPLO
- Archivos de test con datos de fixture
- Documentación con placeholders: `YOUR_API_KEY_HERE`

---

## Coordinacion explicita y ciclo de vida (Agente META)

### Objetivo
Garantizar coordinacion total entre Backend, Frontend, DevOps y PM con un solo agente orquestador, documentando cada fase y reportando avances.

### Comando de inicio (formato sugerido)
"Agente inicia el ciclo de vida del Proyecto <NOMBRE_PROYECTO> y mantenme informado de los cambios hasta version estable"

### Reglas de ejecucion
1. El agente trabaja en modo documentacion y planeacion primero, sin ejecutar comandos destructivos.
2. Cada fase debe dejar un registro claro de acciones y decisiones en la documentacion existente.
3. Ningun cambio se considera completo sin: plan, ejecucion y validacion documentada.
4. Reportar siempre: que cambio, por que, impacto, y proximo paso.

### Fases y acciones obligatorias

**Fase 0 - Preparacion**
- Confirmar objetivos y alcance.
- Definir entregables por modulo.
- Validar herramientas y entorno (solo checklist, sin ejecucion automatica).
- Resultado: plan de trabajo y riesgos.

**Fase 1 - Contratos y tipos compartidos**
- Definir DTOs y contratos API antes de implementar.
- Centralizar tipos compartidos (backend/frontend).
- Documentar cambios de contratos y su impacto.
- Resultado: contratos estables y versionados.

**Fase 2 - Implementacion coordinada**
- Backend y frontend avanzan con el mismo contrato.
- Validaciones en runtime (Zod) y compile-time (TypeScript).
- Documentar endpoints, errores y paginacion.
- Resultado: features funcionales y sincronizadas.

**Fase 3 - QA automatizado**
- Plan de pruebas unitarias, integracion y E2E.
- Validar que los cambios pasen QA antes de continuar.
- Documentar resultados de pruebas.
- Resultado: build validado.

**Fase 4 - Despliegue controlado**
- Definir pipeline CI/CD y checklist de release.
- Despliegue staging -> validacion -> produccion.
- Documentar version final y notas de release.
- Resultado: version estable.

### Registro de cambios (formato requerido)
- Fecha y fase
- Tarea realizada
- Archivos afectados
- Impacto (backend/frontend/devops/pm)
- Estado de pruebas
- Proximo paso

### Mantenimiento de `.copilot-workspace/`

La carpeta `.copilot-workspace/` debe:
- Permanecer en `.gitignore` (nunca subirla al repositorio)
- Limpiarse regularmente (archivar sesiones antiguas)
- Contener solo archivos actuales o de referencia
- Mantener `DocCompleta/` con documentación de proyecto relevante

**Limpieza recomendada:**
```bash
# Mover archivos de un solo uso a historial
mv .copilot-workspace/RESUMEN_SESION_*.md .copilot-workspace/historial/
mv .copilot-workspace/PLAN_*.md .copilot-workspace/historial/

# Mantener solo DocCompleta/ con docs vivas
# Y scripts/ con configuraciones reutilizables
```

### Mantenimiento General

Este archivo debe actualizarse cuando:
- Se agreguen nuevos servicios externos al proyecto
- Se identifiquen nuevos patrones de seguridad
- Se reorganice la estructura de carpetas seguras
- Se implementen nuevas integraciones que requieran credenciales
- Se cambie el nombre o propósito de `.copilot-workspace/`

---

**Última actualización**: 2026-02-12  
**Versión**: 2.0 (ACTUALIZADO: Reglas de commits con feriados, horario extendido a 20:00, recuperación de usuario/contraseña, onboarding)  
**Responsable**: Equipo de Desarrollo OdontoHub  

**Documentación Relacionada:**
- Agente de Seguridad: `.copilot-workspace/DocCompleta/agentes/AGENTE_SEGURIDAD_PRE_COMMIT.md`
- Agente de Commits: `.copilot-workspace/DocCompleta/agentes/AGENTE_COMMITS.md`
- Agente de GitHub Projects: `.copilot-workspace/DocCompleta/agentes/AGENTE_GITHUB_PROJECTS.md`
- Agente de QA: `.copilot-workspace/DocCompleta/agentes/AGENTE_QA_FUNCIONAL.md`
- Agente Meta: `.copilot-workspace/DocCompleta/71_AGENTE_META_MANTENIMIENTO_AGENTES.md`
- Especificaciones funcionales: `.copilot-workspace/DocCompleta/ESPECIFICACIONES_ODONTOHUB_v2.md`
- Stack tecnológico: `.copilot-workspace/DocCompleta/54_TECNOLOGIAS_STACK_ODONTOHUB.md`
- Reporte de validación: Ver `/home/devuser/REPORTE_VALIDACION_STACK_ODONTOHUB.md` en VM

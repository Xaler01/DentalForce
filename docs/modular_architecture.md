# Evolución modular y escalable (base monolito modular → servicios)

## Objetivo
Preparar el sistema para ~1000 clínicas concurrentes, con aislamiento de datos, catálogos compartidos con overrides y capacidad de escalar por dominio sin rehacer todo.

## Estrategia en fases
1) **Monolito modular (ahora)**: separar por bounded context claro dentro del repo Django (apps/librerías internas), contratos explícitos entre módulos y uso de utilidades de tenant-aware (ej. `enfermedades_para_clinica`).
2) **Modular + eventos internos**: introducir un bus interno (Django signals → transición a mensajes) para reducir acoplamiento directo entre dominios.
3) **Servicios ligeros**: extraer catálogos/archivos/pagos en servicios pequeños con APIs internas o RPC, manteniendo core clínico en Django.
4) **Servicios plenos**: mover dominios que más escalen (agenda/citas y facturación) a servicios independientes con cache y colas.

## Bounded contexts propuestos (Django apps o libs internas)
- **Identidad y Acceso**: usuarios, roles, permisos; aware de clínica actual.
- **Tenant/Clínicas**: clínica, sucursales, configuración; dueño del `clinica_id` y políticas.
- **Catálogos Clínicos**: enfermedades, alergias, procedimientos, medicamentos (catálogo global + overrides `ClinicaX`), plantillas de tratamientos.
- **Pacientes**: ficha, antecedentes, adjuntos, alertas; siempre filtrado por clínica.
- **Agenda/Citas**: disponibilidad, cubículos, excepciones, reservas, cola; dueño de su propio modelo de capacidad.
- **Facturación/Pagos**: órdenes, facturas, métodos de pago; expone totales a otros.
- **Inventario/Compras**: ítems, stock, movimientos.
- **Notificaciones/Alertas**: email/SMS/push; suscribe eventos.

## Contratos y patrones clave
- **Tenant boundary**: todos los modelos operativos con `clinica_id`; utilidades de filtrado; admin/queries nunca sin filtro.
- **Overrides de catálogo**: patrón `Clinica<Entidad>` (ya aplicado a Enfermedad) para visibilidad/alias por clínica; replicar en otros catálogos.
- **Anti-corrupción**: cada contexto expone DTOs/serializers; no acceder modelos cruzados desde vistas de otro dominio.
- **Eventos internos**: definir eventos semilla (PacienteCreado, CitaAgendada, PagoRegistrado); publicar vía signal/bus para desacoplar acciones secundarias.
- **Versionado de contratos**: serializers esquemados (pydantic/dataclasses) aunque sea intra-proceso; facilita extraer servicios.

## Datos y escalabilidad
- **PostgreSQL**: mantener single DB con partición lógica por `clinica_id`; considerar RLS si se requiere control extra.
- **Índices**: `clinica_id` + campos frecuentes en cada tabla crítica (citas, pacientes, pagos) y covering indexes para listados.
- **Cache**: Redis para catálogos y disponibilidad de agenda por clínica; invalidar por `clinica_id`.
- **Colas**: RabbitMQ/Redis streams para trabajos pesados (confirmaciones, generación de PDFs, facturación asíncrona, cálculos de alertas).
- **Mediciones**: métricas por clínica (latencias, errores, throughput) y feature flags.

## Operación y despliegue
- **Blueprint**: contenedores separados por procesos (web, worker, beat); horizontal scale por proceso.
- **Límites**: gunicorn/uvicorn con workers auto-ajustados; PG pool sizing; circuit breakers a servicios externos.
- **Observabilidad**: logs estructurados con `clinica_id`, tracing (OTel), dashboards por dominio.

## Plan táctico inmediato
- Formalizar módulos internos (apps) según bounded contexts arriba.
- Replicar override de catálogos a alergias/procedimientos/medicamentos.
- Introducir capa de servicios internos (clases) para no acceder modelos externos directamente.
- Definir eventos internos semilla y un dispatcher sencillo (futuro bus).
- Añadir caching por clínica para catálogos de solo lectura.

## Futuro (cuando crezca la carga)
- Extraer Catálogos y Notificaciones como microservicios primero; luego Agenda y Facturación.
- API Gateway interno con auth de servicio y rate limits.
- Particionar tablas calientes (citas, logs de pagos) por rango o hash en PG si el volumen lo exige.

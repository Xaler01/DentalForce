# Multi-tenant: catálogo de enfermedades con overrides por clínica

## Propósito
Permitir que cada clínica controle la visibilidad y el nombre mostrado de las enfermedades del catálogo global sin afectar a las demás clínicas.

## Modelo clave
- `enfermedades.ClinicaEnfermedad`: une `Clinica` con `Enfermedad` y agrega:
  - `habilitada` (bool): deshabilita el uso para esa clínica.
  - `ocultar` (bool): la oculta en listados, aunque siga habilitada.
  - `nombre_personalizado` (str): alias específico de la clínica.
  - `notas` (text): comentarios internos.

## Reglas de resolución
- Si no existe registro (clinica, enfermedad), se considera habilitada y visible.
- Si `habilitada=False` o `ocultar=True`, se excluye de los listados de esa clínica.
- El nombre mostrado usa `nombre_personalizado` si está presente.

## APIs de soporte
- `enfermedades.utils.enfermedades_para_clinica(clinica)`: devuelve queryset filtrado para listados.
- `enfermedades.utils.nombre_enfermedad_para_clinica(enfermedad, clinica)`: resuelve el nombre a mostrar.

## Uso recomendado en vistas/formularios
- Para dropdowns/listados: usar `enfermedades_para_clinica(request.user.clinica_actual)`.
- Para mostrar nombres: usar `nombre_enfermedad_para_clinica(enf, clinica)` en plantillas/serializadores.

## Admin
- Admin registrado: permite habilitar, ocultar o renombrar por clínica sin afectar el catálogo global.

## Pruebas
- `enfermedades/tests/test_overrides.py` cubre:
  - Respeto a overrides por clínica.
  - Nombres personalizados.
  - Aislamiento: cambios en una clínica no afectan a otra.

## Próximos pasos sugeridos
- Replicar patrón para otros catálogos globales (ej. alergias, medicamentos, procedimientos).
- Añadir capa de caché por clínica si el volumen de catálogos crece (memcached/Redis con keys por clinica_id).
- Exponer un flag de "bloqueo duro" para forzar fallos si una clínica intenta usar una enfermedad deshabilitada.

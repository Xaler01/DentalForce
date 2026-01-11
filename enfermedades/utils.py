"""
Utilidades para el sistema de enfermedades y alertas
SOOD-78: CalculadorAlerta - Lógica de cálculo automático de alertas
SOOD-79: GestorAlertas - Gestión de creación y actualización de alertas
"""
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db.models import Q

from .models import Enfermedad, EnfermedadPaciente, AlertaPaciente, ClinicaEnfermedad


class CalculadorAlerta:
    """
    Calculador de alertas para pacientes
    SOOD-78: Implementa la lógica de negocio para determinar nivel de alerta
    """
    
    # Umbrales configurables
    UMBRAL_VIP_FACTURACION = Decimal('3000.00')  # Monto mínimo para VIP automático
    UMBRAL_MULTIPLES_CONDICIONES = 3  # Número de enfermedades para alerta múltiple
    
    def __init__(self, paciente):
        """
        Inicializa el calculador para un paciente específico
        
        Args:
            paciente: Instancia de Paciente
        """
        self.paciente = paciente
        self._enfermedades_activas = None
        self._enfermedades_criticas = None
        self._enfermedades_alto_riesgo = None
        
    def calcular_nivel_alerta(self) -> str:
        """
        Calcula el nivel de alerta general del paciente
        
        Returns:
            str: 'ROJO', 'AMARILLO' o 'VERDE'
        """
        # ROJO: Máxima prioridad
        if self._tiene_alerta_roja():
            return 'ROJO'
        
        # AMARILLO: Precauciones necesarias
        if self._tiene_alerta_amarilla():
            return 'AMARILLO'
        
        # VERDE: Sin riesgos identificados
        return 'VERDE'
    
    def obtener_factores_alerta(self) -> Dict[str, List[str]]:
        """
        Obtiene todos los factores que contribuyen a las alertas
        
        Returns:
            Dict con factores categorizados por nivel
        """
        factores = {
            'ROJO': [],
            'AMARILLO': [],
            'INFO': []
        }
        
        # Factores ROJO
        if self._tiene_enfermedades_criticas():
            criticas = self.get_enfermedades_criticas()
            for enf in criticas:
                factores['ROJO'].append(
                    f"Enfermedad crítica: {enf.nombre} ({enf.codigo_cie10 or 'Sin CIE-10'})"
                )
        
        if self.paciente.es_vip:
            categoria = self.paciente.get_categoria_vip_display() or "Sin categoría"
            factores['ROJO'].append(f"Cliente VIP: {categoria}")
        
        if self._es_vip_por_facturacion():
            total = self.paciente.get_total_facturado()
            factores['ROJO'].append(f"VIP por facturación: ${total:,.2f}")
        
        # Factores AMARILLO
        if self._tiene_enfermedades_alto_riesgo():
            alto_riesgo = self.get_enfermedades_alto_riesgo()
            for enf in alto_riesgo:
                factores['AMARILLO'].append(
                    f"Enfermedad de alto riesgo: {enf.nombre}"
                )
        
        if self._tiene_multiples_condiciones():
            count = self.get_enfermedades_activas().count()
            factores['AMARILLO'].append(
                f"Múltiples condiciones médicas: {count} enfermedades"
            )
        
        if self._requiere_interconsulta():
            interconsulta = self.get_enfermedades_requieren_interconsulta()
            factores['AMARILLO'].append(
                f"Requiere interconsulta: {interconsulta.count()} condición(es)"
            )
        
        # INFO
        if self.get_enfermedades_activas().exists():
            factores['INFO'].append(
                f"Total de enfermedades registradas: {self.get_enfermedades_activas().count()}"
            )
        
        return factores
    
    def generar_descripcion_alerta(self, nivel: str) -> str:
        """
        Genera una descripción detallada de la alerta
        
        Args:
            nivel: Nivel de alerta ('ROJO', 'AMARILLO', 'VERDE')
            
        Returns:
            str: Descripción formateada
        """
        factores = self.obtener_factores_alerta()
        
        if nivel == 'VERDE':
            return "Paciente sin factores de riesgo identificados. Atención estándar."
        
        descripcion_partes = []
        
        if factores['ROJO']:
            descripcion_partes.append("⚠️ FACTORES CRÍTICOS:")
            for factor in factores['ROJO']:
                descripcion_partes.append(f"  • {factor}")
        
        if factores['AMARILLO']:
            descripcion_partes.append("\n⚠ PRECAUCIONES:")
            for factor in factores['AMARILLO']:
                descripcion_partes.append(f"  • {factor}")
        
        if factores['INFO']:
            descripcion_partes.append("\nℹ️ INFORMACIÓN ADICIONAL:")
            for factor in factores['INFO']:
                descripcion_partes.append(f"  • {factor}")
        
        return "\n".join(descripcion_partes)
    
    def determinar_tipo_alerta_principal(self) -> Optional[str]:
        """
        Determina el tipo principal de alerta según los factores presentes
        
        Returns:
            str: Tipo de alerta o None si no hay alertas
        """
        if self._tiene_enfermedades_criticas():
            return 'ENFERMEDAD_CRITICA'
        
        if self.paciente.es_vip:
            return 'VIP_MANUAL'
        
        if self._es_vip_por_facturacion():
            return 'VIP_FACTURACION'
        
        if self._requiere_interconsulta():
            return 'REQUIERE_INTERCONSULTA'
        
        if self._tiene_multiples_condiciones():
            return 'MULTIPLES_CONDICIONES'
        
        if self._tiene_enfermedades_alto_riesgo():
            return 'ENFERMEDAD_ALTA'
        
        return None
    
    def generar_titulo_alerta(self, nivel: str, tipo: str) -> str:
        """
        Genera un título descriptivo para la alerta
        
        Args:
            nivel: Nivel de alerta
            tipo: Tipo de alerta
            
        Returns:
            str: Título formateado
        """
        templates = {
            'ENFERMEDAD_CRITICA': f"⚠️ CRÍTICO: {self.paciente.get_nombre_completo()} - Enfermedad Crítica",
            'ENFERMEDAD_ALTA': f"⚠ PRECAUCIÓN: {self.paciente.get_nombre_completo()} - Alto Riesgo",
            'VIP_MANUAL': f"⭐ VIP: {self.paciente.get_nombre_completo()} - {self.paciente.get_categoria_vip_display()}",
            'VIP_FACTURACION': f"💰 VIP: {self.paciente.get_nombre_completo()} - Cliente Frecuente",
            'MULTIPLES_CONDICIONES': f"📋 PRECAUCIÓN: {self.paciente.get_nombre_completo()} - Múltiples Condiciones",
            'REQUIERE_INTERCONSULTA': f"👨‍⚕️ INTERCONSULTA: {self.paciente.get_nombre_completo()}",
            'SISTEMA': f"ℹ️ INFO: {self.paciente.get_nombre_completo()}",
        }
        
        return templates.get(tipo, f"Alerta {nivel}: {self.paciente.get_nombre_completo()}")
    
    # Métodos privados de verificación
    
    def _tiene_alerta_roja(self) -> bool:
        """Verifica si el paciente requiere alerta ROJA"""
        return (
            self._tiene_enfermedades_criticas() or
            self.paciente.es_vip or
            self._es_vip_por_facturacion()
        )
    
    def _tiene_alerta_amarilla(self) -> bool:
        """Verifica si el paciente requiere alerta AMARILLA"""
        return (
            self._tiene_enfermedades_alto_riesgo() or
            self._tiene_multiples_condiciones() or
            self._requiere_interconsulta()
        )
    
    def _tiene_enfermedades_criticas(self) -> bool:
        """Verifica si tiene enfermedades críticas"""
        return self.get_enfermedades_criticas().exists()
    
    def _tiene_enfermedades_alto_riesgo(self) -> bool:
        """Verifica si tiene enfermedades de alto/medio riesgo"""
        return self.get_enfermedades_alto_riesgo().exists()
    
    def _tiene_multiples_condiciones(self) -> bool:
        """Verifica si tiene múltiples enfermedades activas"""
        return self.get_enfermedades_activas().count() >= self.UMBRAL_MULTIPLES_CONDICIONES
    
    def _requiere_interconsulta(self) -> bool:
        """Verifica si alguna enfermedad requiere interconsulta"""
        return self.get_enfermedades_requieren_interconsulta().exists()
    
    def _es_vip_por_facturacion(self) -> bool:
        """Verifica si es VIP por monto facturado"""
        return self.paciente.es_vip_por_facturacion(self.UMBRAL_VIP_FACTURACION)
    
    # Métodos de acceso a datos (con caché)
    
    def get_enfermedades_activas(self):
        """Retorna enfermedades activas del paciente (con caché)"""
        if self._enfermedades_activas is None:
            self._enfermedades_activas = self.paciente.enfermedades.filter(
                pacientes_afectados__estado=True,
                pacientes_afectados__estado_actual='ACTIVA'
            )
        return self._enfermedades_activas
    
    def get_enfermedades_criticas(self):
        """Retorna enfermedades críticas (con caché)"""
        if self._enfermedades_criticas is None:
            self._enfermedades_criticas = self.get_enfermedades_activas().filter(
                Q(nivel_riesgo='CRITICO') | Q(genera_alerta_roja=True)
            )
        return self._enfermedades_criticas
    
    def get_enfermedades_alto_riesgo(self):
        """Retorna enfermedades de alto/medio riesgo (con caché)"""
        if self._enfermedades_alto_riesgo is None:
            self._enfermedades_alto_riesgo = self.get_enfermedades_activas().filter(
                nivel_riesgo__in=['ALTO', 'MEDIO']
            ).exclude(
                nivel_riesgo='CRITICO'
            )
        return self._enfermedades_alto_riesgo
    
    def get_enfermedades_requieren_interconsulta(self):
        """Retorna enfermedades que requieren interconsulta médica"""
        return self.get_enfermedades_activas().filter(requiere_interconsulta=True)
    
    def get_resumen_estadistico(self) -> Dict[str, int]:
        """
        Genera un resumen estadístico de las condiciones del paciente
        
        Returns:
            Dict con contadores de diferentes categorías
        """
        return {
            'total_enfermedades': self.get_enfermedades_activas().count(),
            'criticas': self.get_enfermedades_criticas().count(),
            'alto_riesgo': self.get_enfermedades_alto_riesgo().count(),
            'requieren_interconsulta': self.get_enfermedades_requieren_interconsulta().count(),
            'es_vip': 1 if (self.paciente.es_vip or self._es_vip_por_facturacion()) else 0,
        }


def enfermedades_para_clinica(clinica):
    """
    Retorna queryset de Enfermedades visibles para una clínica específica.

    Reglas:
    - Solo enfermedades con `estado=True` global
    - Si existe ClinicaEnfermedad con `habilitada=False` u `ocultar=True`, se excluye
    - Si no existe configuración para (clinica, enfermedad), se considera habilitada
    """
    qs = Enfermedad.objects.filter(estado=True)
    # Excluir explícitamente deshabilitadas para la clínica
    qs = qs.exclude(
        configuraciones__clinica=clinica,
        configuraciones__habilitada=False
    )
    # Excluir marcadas como ocultas para la clínica
    qs = qs.exclude(
        configuraciones__clinica=clinica,
        configuraciones__ocultar=True
    )
    return qs


def nombre_enfermedad_para_clinica(enfermedad, clinica):
    """
    Obtiene el nombre a mostrar de una enfermedad para una clínica,
    considerando nombre personalizado si existe.
    """
    try:
        cfg = ClinicaEnfermedad.objects.get(clinica=clinica, enfermedad=enfermedad)
        return cfg.nombre_personalizado or enfermedad.nombre
    except ClinicaEnfermedad.DoesNotExist:
        return enfermedad.nombre


class GestorAlertas:
    """
    Gestor de alertas de pacientes
    SOOD-79: Maneja creación, actualización y eliminación de alertas
    """
    
    def __init__(self, paciente, usuario=None):
        """
        Inicializa el gestor para un paciente
        
        Args:
            paciente: Instancia de Paciente
            usuario: Usuario que ejecuta la acción (para auditoría)
        """
        self.paciente = paciente
        self.usuario = usuario
        self.calculador = CalculadorAlerta(paciente)
    
    def actualizar_alertas(self, desactivar_antiguas=True) -> Tuple[AlertaPaciente, bool]:
        """
        Actualiza las alertas del paciente según su estado actual
        
        Args:
            desactivar_antiguas: Si debe desactivar alertas antiguas
            
        Returns:
            Tuple (alerta_creada_o_actualizada, fue_creada)
        """
        nivel = self.calculador.calcular_nivel_alerta()
        tipo = self.calculador.determinar_tipo_alerta_principal()
        
        # Si no hay factores de alerta, desactivar todas y retornar
        if nivel == 'VERDE' and not tipo:
            if desactivar_antiguas:
                self.desactivar_alertas_activas(
                    razon="Paciente sin factores de riesgo actuales"
                )
            return None, False
        
        # Buscar alerta activa existente del mismo tipo
        alerta_existente = AlertaPaciente.objects.filter(
            paciente=self.paciente,
            tipo=tipo,
            es_activa=True
        ).first()
        
        # Si existe y el nivel no cambió, solo actualizar timestamp
        if alerta_existente and alerta_existente.nivel == nivel:
            alerta_existente.fm = timezone.now()
            if self.usuario:
                alerta_existente.um = self.usuario.id
            alerta_existente.save(update_fields=['fm', 'um'])
            return alerta_existente, False
        
        # Desactivar alertas antiguas si se solicita
        if desactivar_antiguas:
            self.desactivar_alertas_activas(
                razon=f"Nueva alerta generada: {tipo}",
                excluir_id=alerta_existente.id if alerta_existente else None
            )
        
        # Crear nueva alerta o actualizar nivel
        if alerta_existente:
            alerta_existente.nivel = nivel
            alerta_existente.descripcion = self.calculador.generar_descripcion_alerta(nivel)
            alerta_existente.fm = timezone.now()
            if self.usuario:
                alerta_existente.um = self.usuario.id
            alerta_existente.save()
            fue_creada = False
            alerta = alerta_existente
        else:
            alerta = self.crear_alerta(nivel, tipo)
            fue_creada = True
        
        # Asociar enfermedades relacionadas
        self._asociar_enfermedades_alerta(alerta, tipo)
        
        return alerta, fue_creada
    
    def crear_alerta(self, nivel: str, tipo: str, **kwargs) -> AlertaPaciente:
        """
        Crea una nueva alerta para el paciente
        
        Args:
            nivel: Nivel de la alerta
            tipo: Tipo de la alerta
            **kwargs: Campos adicionales opcionales
            
        Returns:
            AlertaPaciente creada
        """
        defaults = {
            'paciente': self.paciente,
            'nivel': nivel,
            'tipo': tipo,
            'titulo': self.calculador.generar_titulo_alerta(nivel, tipo),
            'descripcion': self.calculador.generar_descripcion_alerta(nivel),
            'requiere_accion': nivel in ['ROJO', 'AMARILLO'],
            'es_activa': True,
        }
        
        # Auditoría
        if self.usuario:
            defaults['uc'] = self.usuario
            defaults['um'] = self.usuario.id
        
        # Sobrescribir con kwargs
        defaults.update(kwargs)
        
        alerta = AlertaPaciente.objects.create(**defaults)
        return alerta
    
    def desactivar_alertas_activas(self, razon: str = None, excluir_id: int = None):
        """
        Desactiva todas las alertas activas del paciente
        
        Args:
            razon: Razón de la desactivación
            excluir_id: ID de alerta a no desactivar
        """
        queryset = AlertaPaciente.objects.filter(
            paciente=self.paciente,
            es_activa=True
        )
        
        if excluir_id:
            queryset = queryset.exclude(id=excluir_id)
        
        for alerta in queryset:
            alerta.desactivar(razon)
    
    def _asociar_enfermedades_alerta(self, alerta: AlertaPaciente, tipo: str):
        """
        Asocia enfermedades relevantes a la alerta
        
        Args:
            alerta: Alerta a la que asociar enfermedades
            tipo: Tipo de alerta
        """
        enfermedades = []
        
        if tipo == 'ENFERMEDAD_CRITICA':
            enfermedades = list(self.calculador.get_enfermedades_criticas())
        elif tipo == 'ENFERMEDAD_ALTA':
            enfermedades = list(self.calculador.get_enfermedades_alto_riesgo())
        elif tipo == 'MULTIPLES_CONDICIONES':
            enfermedades = list(self.calculador.get_enfermedades_activas())
        elif tipo == 'REQUIERE_INTERCONSULTA':
            enfermedades = list(self.calculador.get_enfermedades_requieren_interconsulta())
        
        if enfermedades:
            alerta.enfermedades_relacionadas.set(enfermedades)
    
    def generar_reporte_alertas(self) -> Dict:
        """
        Genera un reporte completo del estado de alertas del paciente
        
        Returns:
            Dict con información detallada
        """
        nivel = self.calculador.calcular_nivel_alerta()
        factores = self.calculador.obtener_factores_alerta()
        estadisticas = self.calculador.get_resumen_estadistico()
        
        alertas_activas = AlertaPaciente.objects.filter(
            paciente=self.paciente,
            es_activa=True
        ).order_by('-fc')
        
        return {
            'paciente': {
                'id': self.paciente.id,
                'nombre': self.paciente.get_nombre_completo(),
                'cedula': self.paciente.cedula,
            },
            'nivel_actual': nivel,
            'factores': factores,
            'estadisticas': estadisticas,
            'alertas_activas': [
                {
                    'id': a.id,
                    'nivel': a.nivel,
                    'tipo': a.tipo,
                    'titulo': a.titulo,
                    'fecha_creacion': a.fc.isoformat() if a.fc else None,
                    'requiere_accion': a.requiere_accion,
                    'vista': a.vista_por is not None,
                }
                for a in alertas_activas
            ],
            'recomendaciones': self._generar_recomendaciones(nivel, factores),
        }
    
    def _generar_recomendaciones(self, nivel: str, factores: Dict) -> List[str]:
        """
        Genera recomendaciones basadas en el nivel y factores
        
        Args:
            nivel: Nivel de alerta
            factores: Factores de alerta
            
        Returns:
            Lista de recomendaciones
        """
        recomendaciones = []
        
        if nivel == 'ROJO':
            recomendaciones.append("⚠️ Atención prioritaria requerida")
            recomendaciones.append("Revisar protocolo de atención VIP/Crítico")
            if any('Enfermedad crítica' in f for f in factores.get('ROJO', [])):
                recomendaciones.append("Verificar contraindicaciones antes de cualquier procedimiento")
                recomendaciones.append("Considerar interconsulta médica obligatoria")
        
        if nivel == 'AMARILLO':
            recomendaciones.append("⚠ Aplicar precauciones estándar")
            if any('interconsulta' in f.lower() for f in factores.get('AMARILLO', [])):
                recomendaciones.append("Solicitar autorización médica para procedimientos invasivos")
        
        if nivel == 'VERDE':
            recomendaciones.append("✓ Atención estándar - Sin precauciones especiales")
        
        return recomendaciones

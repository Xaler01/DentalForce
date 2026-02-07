from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from clinicas.models import Clinica


class RolUsuario(models.TextChoices):
    """Enumeración de roles disponibles en el sistema"""
    SUPER_ADMIN = 'super_admin', 'Super Administrador'
    ADMIN_CLINICA = 'admin_clinica', 'Administrador de Clínica'
    DENTISTA = 'dentista', 'Dentista'
    AUXILIAR = 'auxiliar', 'Auxiliar Odontológico'
    RECEPCIONISTA = 'recepcionista', 'Recepcionista'
    ADMINISTRATIVO = 'administrativo', 'Personal Administrativo'
    # Roles legacy (mantener compatibilidad)
    ODONTOLOGO = 'odontologo', 'Odontólogo'  # Sinónimo de DENTISTA
    ASISTENTE = 'asistente', 'Asistente Odontológico'  # Sinónimo de AUXILIAR


class PermisoPersonalizado(models.Model):
    """
    Permiso granular que puede asignarse a roles o usuarios.
    
    Permite control fino sobre las capacidades que tiene cada usuario o rol.
    Pueden ser permisos del sistema (clinica=None) o personalizados por clínica.
    """
    
    CATEGORIAS = [
        ('recepcion', 'Recepción'),
        ('asistencia', 'Asistencia Odontológica'),
        ('odontologia', 'Odontología'),
        ('admin', 'Administración'),
        ('reportes', 'Reportes'),
        ('inventario', 'Inventario'),
        ('facturacion', 'Facturación'),
    ]
    
    codigo = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Código del Permiso',
        help_text='Código único (ej: recepcion.crear_cita, odontologia.editar_diagnostico)'
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Permiso')
    descripcion = models.TextField(verbose_name='Descripción', blank=True)
    
    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIAS,
        verbose_name='Categoría'
    )
    
    # null = Permiso global del sistema, FK = Personalizado para clínica específica
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='permisos_personalizados',
        verbose_name='Clínica',
        help_text='Vacío = Permiso global. Seleccionar = Permiso personalizado para esta clínica'
    )
    
    activo = models.BooleanField(default=True, verbose_name='¿Activo?')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Permiso Personalizado'
        verbose_name_plural = 'Permisos Personalizados'
        ordering = ['categoria', 'codigo']
        db_table = 'usuarios_permiso_personalizado'
        indexes = [
            models.Index(fields=['codigo', 'activo']),
            models.Index(fields=['clinica', 'activo']),
            models.Index(fields=['categoria']),
        ]
    
    def __str__(self):
        clinica_str = f" ({self.clinica.nombre})" if self.clinica else " (Sistema)"
        return f"{self.codigo} - {self.nombre}{clinica_str}"
    
    @property
    def es_global(self):
        """¿Es permiso global del sistema?"""
        return self.clinica is None


class RolUsuarioDentalForce(models.Model):
    """
    Rol con conjunto predefinido de permisos.
    
    Puede ser un rol del sistema (clinica=None) o personalizado por clínica.
    Permite agrupar permisos relacionados para facilitar la asignación.
    """
    
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Rol')
    descripcion = models.TextField(
        verbose_name='Descripción',
        blank=True,
        help_text='Descripción de las responsabilidades de este rol'
    )
    
    # null = Rol global del sistema, FK = Personalizado para clínica específica
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='roles_personalizados',
        verbose_name='Clínica',
        help_text='Vacío = Rol global. Seleccionar = Rol personalizado para esta clínica'
    )
    
    permisos = models.ManyToManyField(
        PermisoPersonalizado,
        related_name='roles',
        verbose_name='Permisos asignados a este rol',
        blank=True
    )
    
    activo = models.BooleanField(default=True, verbose_name='¿Activo?')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Rol DentalForce'
        verbose_name_plural = 'Roles DentalForce'
        unique_together = [['clinica', 'nombre']]
        ordering = ['nombre']
        db_table = 'usuarios_rol_dentalforce'
        indexes = [
            models.Index(fields=['nombre', 'activo']),
            models.Index(fields=['clinica']),
        ]
    
    def __str__(self):
        clinica_str = f" ({self.clinica.nombre})" if self.clinica else " (Sistema)"
        return f"{self.nombre}{clinica_str}"
    
    @property
    def es_global(self):
        """¿Es rol global del sistema?"""
        return self.clinica is None


class UsuarioClinica(models.Model):
    """
    Vinculación de usuarios con clínicas, roles y permisos.
    
    Ahora soporta:
    - Campo 'rol' (legacy): mantener compatibilidad
    - ManyToMany 'roles_personalizados': nuevos roles granulares
    - ManyToMany 'permisos_adicionales': permisos personalizados adicionales
    
    El usuario tiene acceso a:
    1. Permisos de todos los roles_personalizados asignados
    2. Permisos adicionales personalizados
    3. Los permisos del rol legacy (si aplica)
    """
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='clinica_asignacion'
    )
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE,
        related_name='usuarios'
    )
    sucursal = models.ForeignKey(
        'clinicas.Sucursal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_asignados',
        verbose_name='Sucursal Asignada',
        help_text='Sucursal principal donde trabaja el usuario (opcional). Admin de Clínica no tiene sucursal asignada.'
    )
    
    # LEGACY: Campo rol antiguo (mantener para compatibilidad)
    rol = models.CharField(
        max_length=20,
        choices=RolUsuario.choices,
        default=RolUsuario.ADMINISTRATIVO,
        verbose_name='Rol del usuario (Legacy)',
        help_text='Campo antiguo. Usar "roles_personalizados" para nueva funcionalidad.'
    )
    
    # NUEVO: Múltiples roles con permisos granulares
    roles_personalizados = models.ManyToManyField(
        RolUsuarioDentalForce,
        blank=True,
        related_name='usuarios_asignados',
        verbose_name='Roles Personalizados',
        help_text='Nuevos roles con permisos granulares. Puede asignar múltiples roles.'
    )
    
    # NUEVO: Permisos adicionales personalizados
    permisos_adicionales = models.ManyToManyField(
        PermisoPersonalizado,
        blank=True,
        related_name='usuarios_con_permiso_adicional',
        verbose_name='Permisos Adicionales',
        help_text='Permisos adicionales específicos. Se suman a los permisos de los roles.'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='¿Usuario activo?'
    )
    contrasena_temporal = models.BooleanField(
        default=False,
        verbose_name='¿Contraseña temporal?',
        help_text='Marca si el usuario tiene una contraseña temporal y debe cambiarla en primer acceso'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de última modificación'
    )

    class Meta:
        verbose_name = 'Usuario-Clínica'
        verbose_name_plural = 'Usuarios-Clínicas'
        unique_together = ('usuario', 'clinica')
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['clinica', 'rol']),
            models.Index(fields=['usuario', 'activo']),
        ]

    def __str__(self):
        """Representación en texto del objeto"""
        return f"{self.usuario.get_full_name() or self.usuario.email} - {self.clinica.nombre} ({self.get_rol_display()})"

    def tiene_permiso(self, codigo_permiso):
        """
        Verifica si el usuario tiene un permiso específico.
        
        Busca el permiso en:
        1. Permisos de todos los roles_personalizados asignados
        2. Permisos adicionales personalizados
        3. Permisos implícitos del rol legacy (si corresponde)
        
        Args:
            codigo_permiso (str): Código del permiso (ej: 'recepcion.crear_cita')
        
        Returns:
            bool: True si tiene el permiso, False en caso contrario
        """
        if not self.activo:
            return False
        
        # 1. Permisos de los roles personalizados
        permisos_de_roles = PermisoPersonalizado.objects.filter(
            roles__usuarios_asignados=self,
            codigo=codigo_permiso,
            activo=True
        ).exists()
        
        # 2. Permisos adicionales directos
        permisos_adicionales = self.permisos_adicionales.filter(
            codigo=codigo_permiso,
            activo=True
        ).exists()
        
        # 3. Permisos implícitos del rol legacy (si es necesario)
        # Por ahora, solo permisos explícitos
        
        return permisos_de_roles or permisos_adicionales
    
    def get_permisos(self):
        """
        Retorna QuerySet de todos los permisos disponibles para este usuario.
        
        Returns:
            QuerySet: Todos los PermisoPersonalizado disponibles (sin duplicados)
        """
        if not self.activo:
            return PermisoPersonalizado.objects.none()
        
        # Permisos de roles
        permisos_rol = PermisoPersonalizado.objects.filter(
            roles__usuarios_asignados=self,
            activo=True
        )
        
        # Permisos adicionales
        permisos_adic = self.permisos_adicionales.filter(activo=True)
        
        # Combinar y eliminar duplicados
        return permisos_rol.union(permisos_adic)
    
    def get_codigos_permisos(self):
        """Retorna lista de códigos de permisos disponibles"""
        return list(self.get_permisos().values_list('codigo', flat=True))
    
    @property
    def nombres_roles_personalizados(self):
        """Retorna lista de nombres de roles personalizados"""
        return list(self.roles_personalizados.values_list('nombre', flat=True))

    @property
    def es_admin(self):
        """¿El usuario es administrador de su clínica?"""
        return self.rol == RolUsuario.ADMIN_CLINICA

    @property
    def es_odontologo(self):
        """¿El usuario es odontólogo?"""
        return self.rol == RolUsuario.ODONTOLOGO

    @property
    def es_administrativo(self):
        """¿El usuario es personal administrativo?"""
        return self.rol == RolUsuario.ADMINISTRATIVO

    @property
    def es_asistente(self):
        """¿El usuario es asistente?"""
        return self.rol == RolUsuario.ASISTENTE

    @property
    def nombre_completo(self):
        """Obtener nombre completo del usuario"""
        nombre = self.usuario.get_full_name()
        return nombre if nombre else self.usuario.email

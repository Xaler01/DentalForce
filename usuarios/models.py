from django.db import models
from django.contrib.auth.models import User
from clinicas.models import Clinica


class RolUsuario(models.TextChoices):
    """Enumeración de roles disponibles en el sistema"""
    SUPER_ADMIN = 'super_admin', 'Super Administrador'
    ADMIN_CLINICA = 'admin_clinica', 'Administrador de Clínica'
    ADMINISTRATIVO = 'administrativo', 'Personal Administrativo'
    ODONTOLOGO = 'odontologo', 'Odontólogo'
    ASISTENTE = 'asistente', 'Asistente Odontológico'


class UsuarioClinica(models.Model):
    """
    Vinculación de usuarios con clínicas y sus roles.
    
    Garantiza que cada usuario (excepto super admin) está asignado a exactamente
    una clínica con un rol específico.
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
    rol = models.CharField(
        max_length=20,
        choices=RolUsuario.choices,
        default=RolUsuario.ADMINISTRATIVO,
        verbose_name='Rol del usuario'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='¿Usuario activo?'
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

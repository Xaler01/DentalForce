from django.db import models
from django.contrib.auth.models import User
from bases.models import ClaseModelo


class CategoriaEnfermedad(ClaseModelo):
    """
    Categorías para clasificar enfermedades (Ej: Cardiovascular, Endocrinológica, etc.)
    SOOD-71: Modelo base para organización jerárquica de enfermedades
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre de la categoría (Ej: Cardiovascular, Respiratoria)"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción detallada de la categoría"
    )
    icono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Clase de icono FontAwesome (Ej: fa-heart, fa-lungs)"
    )
    color = models.CharField(
        max_length=20,
        default='#6c757d',
        help_text="Color hexadecimal para identificación visual"
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de presentación (menor = primero)"
    )

    class Meta:
        verbose_name = "Categoría de Enfermedad"
        verbose_name_plural = "Categorías de Enfermedades"
        ordering = ['orden', 'nombre']
        db_table = 'enf_categoria'

    def __str__(self):
        return self.nombre

    def cantidad_enfermedades(self):
        """Retorna la cantidad de enfermedades activas en esta categoría"""
        return self.enfermedades.filter(estado=True).count()
    cantidad_enfermedades.short_description = "Enfermedades"

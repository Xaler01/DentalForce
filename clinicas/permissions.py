"""
Mixins para control granular de permisos multi-tenant.
Proporciona controles de acceso a nivel de clínica y objeto.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages


class ClinicaRequiredMixin(UserPassesTestMixin):
    """
    Mixin que verifica que el usuario tenga una clínica seleccionada.
    Si no, redirige al selector de clínicas.
    """
    def test_func(self):
        return 'clinica_id' in self.request.session

    def handle_no_permission(self):
        messages.warning(self.request, 'Debe seleccionar una clínica para continuar.')
        return redirect('clinicas:seleccionar')


class ClinicaOwnershipMixin(ClinicaRequiredMixin):
    """
    Mixin que verifica que el objeto pertenezca a la clínica activa.
    Evita que un usuario vea datos de otra clínica.
    
    Requiere que el modelo tenga:
    - Un campo FK a Clinica, O
    - Una relación a través de otra entidad (Sucursal, Dentista, etc.)
    
    Configurar en la vista:
        - clinica_field: nombre del campo FK a Clinica
        - related_clinica_fields: ruta de relaciones si no es FK directo
    """
    clinica_field = 'clinica'  # Por defecto
    related_clinica_fields = None  # Ej: 'sucursal__clinica' para Cubículo
    
    def get_object_clinica_id(self, obj):
        """
        Extrae el clinica_id del objeto usando el campo configurado.
        """
        if self.related_clinica_fields:
            # Navegar a través de relaciones: 'sucursal__clinica'
            parts = self.related_clinica_fields.split('__')
            current = obj
            for part in parts:
                current = getattr(current, part, None)
                if current is None:
                    return None
            return current.id if hasattr(current, 'id') else None
        else:
            # Campo directo
            attr = getattr(obj, self.clinica_field, None)
            return attr.id if attr else None
    
    def test_func(self):
        # Primero verificar que haya clínica activa
        if not super().test_func():
            return False
        
        # Obtener el objeto
        obj = self.get_object()
        clinica_id_objeto = self.get_object_clinica_id(obj)
        clinica_id_activa = self.request.session.get('clinica_id')
        
        # Admins puede ver todo
        if self.request.user.is_superuser:
            return True
        
        # Verificar que el objeto pertenezca a la clínica activa
        return clinica_id_objeto == clinica_id_activa
    
    def handle_no_permission(self):
        """
        Si falla el test, el usuario no tiene permiso para ver este objeto.
        """
        messages.error(
            self.request,
            'No tiene permiso para acceder a este recurso o pertenece a otra clínica.'
        )
        raise PermissionDenied('Acceso denegado: el recurso pertenece a otra clínica.')


class ClinicaFilterMixin:
    """
    Mixin que filtra automáticamente querysets por la clínica activa.
    Útil para ListViews que deben mostrar solo datos de la clínica seleccionada.
    
    Configurar en la vista:
        - clinica_filter_field: nombre del campo FK a Clinica
        - related_clinica_filter_fields: ruta de relaciones si no es FK directo
    """
    clinica_filter_field = 'clinica'
    related_clinica_filter_fields = None  # Ej: 'sucursal__clinica'
    
    def get_queryset(self):
        """
        Filtra el queryset por la clínica activa.
        """
        queryset = super().get_queryset()
        clinica_id = self.request.session.get('clinica_id')
        
        # Admins puede ver todo
        if self.request.user.is_superuser:
            return queryset
        
        # Filtrar por clínica si está configurada
        if clinica_id:
            if self.related_clinica_filter_fields:
                # Usar filtro con relaciones: 'sucursal__clinica'
                filter_key = f"{self.related_clinica_filter_fields}__id"
                return queryset.filter(**{filter_key: clinica_id})
            else:
                # Filtro directo
                filter_key = f"{self.clinica_filter_field}__id"
                return queryset.filter(**{filter_key: clinica_id})
        
        # Si no hay clínica activa, retornar queryset vacío
        return queryset.none()


class PermissionCheckMixin(UserPassesTestMixin):
    """
    Mixin para verificar permisos específicos del usuario.
    Funciona en conjunto con los mixins anteriores.
    
    Configurar en la vista:
        - permission_required: permiso requerido (ej: 'clinicas.view_clinica')
    """
    permission_required = None
    
    def test_func(self):
        """Verifica que el usuario tenga el permiso requerido"""
        if not self.permission_required:
            return True
        
        return self.request.user.has_perm(self.permission_required)
    
    def handle_no_permission(self):
        """Si no tiene permiso, mostrar mensaje de error"""
        messages.error(
            self.request,
            f'No tiene permisos para realizar esta acción.'
        )
        raise PermissionDenied('Permisos insuficientes.')


class MultiTenantAccessMixin(
    ClinicaOwnershipMixin,
    PermissionCheckMixin
):
    """
    Mixin completo que combina:
    1. Verificación de clínica seleccionada
    2. Verificación de propiedad del objeto (pertenece a la clínica activa)
    3. Verificación de permisos específicos
    
    Uso en vistas DetailView:
        class ClinicaDetailView(MultiTenantAccessMixin, DetailView):
            model = Clinica
            permission_required = 'clinicas.view_clinica'
    """
    pass


class MultiTenantListMixin(
    PermissionCheckMixin,
    ClinicaRequiredMixin,
    ClinicaFilterMixin
):
    """
    Mixin completo para ListViews que filtra por clínica y verifica permisos.
    Verifica AMBAS condiciones: permiso Y clínica seleccionada.
    
    Uso en vistas ListView:
        class ClinicaListView(MultiTenantListMixin, ListView):
            model = Clinica
            permission_required = 'clinicas.view_clinica'
            clinica_filter_field = 'id'  # Filtrar por clinica directamente
    """
    def test_func(self):
        """Combina las pruebas de ambos mixins"""
        # Primero verifica permisos
        if not PermissionCheckMixin.test_func(self):
            return False
        # Luego verifica clínica
        return ClinicaRequiredMixin.test_func(self)
    
    def handle_no_permission(self):
        """Manejo personalizado: primero permisos, luego clínica"""
        # Si no tiene permiso, lanza excepción
        if not PermissionCheckMixin.test_func(self):
            return PermissionCheckMixin.handle_no_permission(self)
        # Si no tiene clínica, redirige
        return ClinicaRequiredMixin.handle_no_permission(self)

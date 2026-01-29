from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Prefetch

from .models import Clinica, Sucursal, Especialidad, Cubiculo
from .forms import ClinicaForm, SucursalForm, EspecialidadForm, CubiculoForm
from .permissions import (
    ClinicaRequiredMixin,
    ClinicaOwnershipMixin,
    MultiTenantAccessMixin,
    MultiTenantListMixin,
    PermissionCheckMixin
)


# ============================================================================
# SELECTOR DE CLÍNICA
# ============================================================================

class ClinicaSelectView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Selector de clínica independiente del módulo de citas."""
    template_name = 'clinicas/clinica_select.html'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.warning(self.request, 'Solo el administrador general puede cambiar de clínica.')
        return redirect('bases:home')

    def get(self, request):
        # Solo el admin general (superuser) puede acceder
        clinicas = list(Clinica.objects.all().order_by('nombre'))

        context = {
            'clinicas': clinicas,
            'clinica_actual_id': request.session.get('clinica_id'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        clinica_id = request.POST.get('clinica_id')
        if not clinica_id:
            messages.error(request, 'Debe seleccionar una clínica.')
            return redirect('clinicas:seleccionar')

        try:
            clinica = Clinica.objects.get(pk=clinica_id)
        except Clinica.DoesNotExist:
            messages.error(request, 'La clínica seleccionada no existe o está inactiva.')
            return redirect('clinicas:seleccionar')

        request.session['clinica_id'] = clinica.id
        messages.success(request, f'Clínica "{clinica.nombre}" seleccionada.')
        next_url = request.GET.get('next', reverse('bases:home'))
        return redirect(next_url)


# ============================================================================
# VISTAS CRUD DE CLÍNICAS
# ============================================================================

class ClinicaListView(MultiTenantListMixin, ListView):
    """Lista todas las clínicas (solo super-admin)"""
    model = Clinica
    template_name = 'clinicas/clinica_list.html'
    context_object_name = 'clinicas'
    paginate_by = 25
    permission_required = 'clinicas.view_clinica'
    
    def get_queryset(self):
        """Los superusers ven todas, usuarios normales solo su clínica activa"""
        if self.request.user.is_superuser:
            return Clinica.objects.all().prefetch_related('sucursales')
        
        clinica_id = self.request.session.get('clinica_id')
        if clinica_id:
            return Clinica.objects.filter(id=clinica_id).prefetch_related('sucursales')
        
        return Clinica.objects.none()


class ClinicaDetailView(MultiTenantAccessMixin, DetailView):
    """Detalle de una clínica"""
    model = Clinica
    template_name = 'clinicas/clinica_detail.html'
    context_object_name = 'clinica'
    permission_required = 'clinicas.view_clinica'
    clinica_field = 'id'  # Comparar directamente
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clinica = self.object
        context['sucursales'] = clinica.sucursales.all()
        return context


class ClinicaCreateView(PermissionCheckMixin, LoginRequiredMixin, CreateView):
    """Crear nueva clínica (solo super-admin)"""
    model = Clinica
    form_class = ClinicaForm
    template_name = 'clinicas/clinica_form.html'
    permission_required = 'clinicas.add_clinica'
    success_url = reverse_lazy('clinicas:list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Clínica "{self.object.nombre}" creada exitosamente.')
        return response


class ClinicaUpdateView(MultiTenantAccessMixin, UpdateView):
    """Editar clínica"""
    model = Clinica
    form_class = ClinicaForm
    template_name = 'clinicas/clinica_form.html'
    permission_required = 'clinicas.change_clinica'
    clinica_field = 'id'
    success_url = reverse_lazy('clinicas:list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Clínica "{self.object.nombre}" actualizada.')
        return response


class ClinicaDeleteView(MultiTenantAccessMixin, DeleteView):
    """Eliminar clínica"""
    model = Clinica
    template_name = 'clinicas/clinica_confirm_delete.html'
    permission_required = 'clinicas.delete_clinica'
    clinica_field = 'id'
    success_url = reverse_lazy('clinicas:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Clínica eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# VISTAS CRUD DE SUCURSALES
# ============================================================================

class SucursalListView(MultiTenantListMixin, ListView):
    """Lista todas las sucursales de la clínica activa"""
    model = Sucursal
    template_name = 'clinicas/sucursal_list.html'
    context_object_name = 'sucursales'
    paginate_by = 25
    permission_required = 'clinicas.view_sucursal'
    clinica_filter_field = 'clinica'
    
    def get_queryset(self):
        """Override para incluir select_related en clinica"""
        qs = super().get_queryset()
        return qs.select_related('clinica')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener clínica del queryset ya cargado para evitar query adicional
        if self.object_list:
            # Si hay sucursales, la clínica ya está cargada vía select_related
            context['clinica'] = self.object_list.first().clinica
        else:
            # Si no hay sucursales, obten la clínica activa
            clinica_id = self.request.session.get('clinica_id')
            context['clinica'] = Clinica.objects.get(id=clinica_id)
        return context


class SucursalDetailView(MultiTenantAccessMixin, DetailView):
    """Detalle de una sucursal"""
    model = Sucursal
    template_name = 'clinicas/sucursal_detail.html'
    context_object_name = 'sucursal'
    permission_required = 'clinicas.view_sucursal'
    clinica_field = 'clinica'
    related_clinica_fields = 'clinica'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sucursal = self.object
        context['cubiculos'] = sucursal.cubiculos.all()
        return context


class SucursalCreateView(MultiTenantListMixin, CreateView):
    """Crear nueva sucursal"""
    model = Sucursal
    form_class = SucursalForm
    template_name = 'clinicas/sucursal_form.html'
    permission_required = 'clinicas.add_sucursal'
    success_url = reverse_lazy('clinicas:sucursal_list')
    
    def get_initial(self):
        """Pre-llenar la clínica activa"""
        initial = super().get_initial()
        clinica_id = self.request.session.get('clinica_id')
        if clinica_id:
            initial['clinica'] = Clinica.objects.get(id=clinica_id)
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pasar el usuario al formulario para filtrar la clínica
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Sucursal "{self.object.nombre}" creada.')
        return response


class SucursalUpdateView(MultiTenantAccessMixin, UpdateView):
    """Editar sucursal"""
    model = Sucursal
    form_class = SucursalForm
    template_name = 'clinicas/sucursal_form.html'
    permission_required = 'clinicas.change_sucursal'
    clinica_field = 'clinica'
    related_clinica_fields = 'clinica'
    success_url = reverse_lazy('clinicas:sucursal_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pasar el usuario al formulario para filtrar la clínica
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Sucursal "{self.object.nombre}" actualizada.')
        return response


class SucursalDeleteView(MultiTenantAccessMixin, DeleteView):
    """Eliminar sucursal"""
    model = Sucursal
    template_name = 'clinicas/sucursal_confirm_delete.html'
    permission_required = 'clinicas.delete_sucursal'
    clinica_field = 'clinica'
    related_clinica_fields = 'clinica'
    success_url = reverse_lazy('clinicas:sucursal_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Sucursal eliminada.')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# VISTAS CRUD DE ESPECIALIDADES
# ============================================================================

class EspecialidadListView(PermissionCheckMixin, ListView):
    """Lista todas las especialidades"""
    model = Especialidad
    template_name = 'clinicas/especialidad_list.html'
    context_object_name = 'especialidades'
    paginate_by = 25
    permission_required = 'clinicas.view_especialidad'
    
    def get_queryset(self):
        """Las especialidades son globales, pero filtramos por búsqueda"""
        queryset = Especialidad.objects.all()
        
        # Búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        return queryset.order_by('nombre')


class EspecialidadDetailView(PermissionCheckMixin, DetailView):
    """Detalle de una especialidad"""
    model = Especialidad
    template_name = 'clinicas/especialidad_detail.html'
    context_object_name = 'especialidad'
    permission_required = 'clinicas.view_especialidad'


class EspecialidadCreateView(PermissionCheckMixin, LoginRequiredMixin, CreateView):
    """Crear nueva especialidad"""
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'clinicas/especialidad_form.html'
    permission_required = 'clinicas.add_especialidad'
    success_url = reverse_lazy('clinicas:especialidad_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Especialidad "{self.object.nombre}" creada.')
        return response


class EspecialidadUpdateView(PermissionCheckMixin, UpdateView):
    """Editar especialidad"""
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'clinicas/especialidad_form.html'
    permission_required = 'clinicas.change_especialidad'
    success_url = reverse_lazy('clinicas:especialidad_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Especialidad "{self.object.nombre}" actualizada.')
        return response


class EspecialidadDeleteView(PermissionCheckMixin, DeleteView):
    """Eliminar especialidad"""
    model = Especialidad
    template_name = 'clinicas/especialidad_confirm_delete.html'
    permission_required = 'clinicas.delete_especialidad'
    success_url = reverse_lazy('clinicas:especialidad_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtrar conteos por clínica activa
        clinica_id = self.request.session.get('clinica_id')
        
        if clinica_id and not self.request.user.is_superuser:
            # Importar modelo Dentista (evitar imports circulares)
            from cit.models import Dentista, Cita
            
            # Contar solo dentistas de la clínica activa
            context['dentistas_count'] = self.object.dentistas.filter(
                sucursal_principal__clinica_id=clinica_id
            ).count()
            
            # Contar solo citas de la clínica activa
            context['citas_count'] = Cita.objects.filter(
                especialidad=self.object,
                dentista__sucursal_principal__clinica_id=clinica_id
            ).count()
        else:
            # Superusers ven totales globales
            from cit.models import Cita
            context['dentistas_count'] = self.object.dentistas.count()
            context['citas_count'] = Cita.objects.filter(especialidad=self.object).count()
        
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Especialidad eliminada.')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# VISTAS CRUD DE CUBÍCULOS
# ============================================================================

class CubiculoListView(MultiTenantListMixin, ListView):
    """Lista todos los cubículos de la clínica activa"""
    model = Cubiculo
    template_name = 'clinicas/cubiculo_list.html'
    context_object_name = 'cubiculos'
    paginate_by = 25
    permission_required = 'clinicas.view_cubiculo'
    clinica_filter_field = 'sucursal__clinica'
    related_clinica_filter_fields = 'sucursal__clinica'


class CubiculoDetailView(MultiTenantAccessMixin, DetailView):
    """Detalle de un cubículo"""
    model = Cubiculo
    template_name = 'clinicas/cubiculo_detail.html'
    context_object_name = 'cubiculo'
    permission_required = 'clinicas.view_cubiculo'
    related_clinica_fields = 'sucursal__clinica'
    
    def get_queryset(self):
        """Optimizar con select_related para sucursal y clínica"""
        return super().get_queryset().select_related('sucursal', 'sucursal__clinica')


class CubiculoCreateView(MultiTenantListMixin, CreateView):
    """Crear nuevo cubículo"""
    model = Cubiculo
    form_class = CubiculoForm
    template_name = 'clinicas/cubiculo_form.html'
    permission_required = 'clinicas.add_cubiculo'
    success_url = reverse_lazy('clinicas:cubiculo_list')
    
    def get_form_kwargs(self):
        """Filtrar sucursales por la clínica activa"""
        kwargs = super().get_form_kwargs()
        clinica_id = self.request.session.get('clinica_id')
        form = kwargs.get('form') or self.form_class
        # El form limitará las sucursales en el formulario
        return kwargs
    
    def form_valid(self, form):
        # Asignar el usuario actual como creador
        form.instance.uc_id = self.request.user.id
        response = super().form_valid(form)
        messages.success(self.request, f'Cubículo "{self.object.nombre}" creado.')
        return response


class CubiculoUpdateView(MultiTenantAccessMixin, UpdateView):
    """Editar cubículo"""
    model = Cubiculo
    form_class = CubiculoForm
    template_name = 'clinicas/cubiculo_form.html'
    permission_required = 'clinicas.change_cubiculo'
    related_clinica_fields = 'sucursal__clinica'
    success_url = reverse_lazy('clinicas:cubiculo_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Cubículo "{self.object.nombre}" actualizado.')
        return response


class CubiculoDeleteView(MultiTenantAccessMixin, DeleteView):
    """Eliminar cubículo"""
    model = Cubiculo
    template_name = 'clinicas/cubiculo_confirm_delete.html'
    permission_required = 'clinicas.delete_cubiculo'
    related_clinica_fields = 'sucursal__clinica'
    success_url = reverse_lazy('clinicas:cubiculo_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cubículo eliminado.')
        return super().delete(request, *args, **kwargs)

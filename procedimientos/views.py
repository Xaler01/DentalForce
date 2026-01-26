"""
Views para gestión de catálogo de procedimientos odontológicos y precios por clínica.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count, Prefetch
from .models import ProcedimientoOdontologico, ClinicaProcedimiento
from .forms import ProcedimientoOdontologicoForm, ClinicaProcedimientoForm


# ==================== VISTAS DE PROCEDIMIENTOS ====================

class ProcedimientoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de procedimientos odontológicos"""
    model = ProcedimientoOdontologico
    template_name = 'procedimientos/procedimiento_list.html'
    context_object_name = 'procedimientos'
    paginate_by = 20
    permission_required = 'procedimientos.view_procedimientoodontologico'
    
    def get_queryset(self):
        queryset = ProcedimientoOdontologico.objects.all().order_by('categoria', 'nombre')
        
        # Búsqueda
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(codigo__icontains=search) |
                Q(codigo_cdt__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        # Filtro por categoría
        categoria = self.request.GET.get('categoria', '').strip()
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        # Filtro por estado
        estado = self.request.GET.get('estado', '').strip()
        if estado == 'activo':
            queryset = queryset.filter(estado=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(estado=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = ProcedimientoOdontologico.CATEGORIA_CHOICES
        context['search'] = self.request.GET.get('search', '')
        context['categoria_filter'] = self.request.GET.get('categoria', '')
        context['estado_filter'] = self.request.GET.get('estado', '')
        return context


class ProcedimientoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crear nuevo procedimiento"""
    model = ProcedimientoOdontologico
    form_class = ProcedimientoOdontologicoForm
    template_name = 'procedimientos/procedimiento_form.html'
    success_url = reverse_lazy('procedimientos:procedimiento-list')
    permission_required = 'procedimientos.add_procedimientoodontologico'
    
    def form_valid(self, form):
        form.instance.uc = self.request.user
        messages.success(
            self.request,
            f'✅ Procedimiento "{form.instance.nombre}" creado exitosamente.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Error al crear el procedimiento. Revise los campos marcados.'
        )
        return super().form_invalid(form)


class ProcedimientoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Actualizar procedimiento existente"""
    model = ProcedimientoOdontologico
    form_class = ProcedimientoOdontologicoForm
    template_name = 'procedimientos/procedimiento_form.html'
    success_url = reverse_lazy('procedimientos:procedimiento-list')
    permission_required = 'procedimientos.change_procedimientoodontologico'
    
    def form_valid(self, form):
        form.instance.um = self.request.user
        messages.success(
            self.request,
            f'✅ Procedimiento "{form.instance.nombre}" actualizado exitosamente.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Error al actualizar el procedimiento. Revise los campos marcados.'
        )
        return super().form_invalid(form)


class ProcedimientoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Eliminar procedimiento (soft delete)"""
    model = ProcedimientoOdontologico
    template_name = 'procedimientos/procedimiento_confirm_delete.html'
    success_url = reverse_lazy('procedimientos:procedimiento-list')
    permission_required = 'procedimientos.delete_procedimientoodontologico'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Verificar si tiene precios asociados
        if self.object.precios_por_clinica.exists():
            messages.warning(
                request,
                f'⚠️ El procedimiento "{self.object.nombre}" tiene precios asignados. '
                f'Se desactivará en lugar de eliminarse.'
            )
            self.object.estado = False
            self.object.save()
        else:
            messages.success(
                request,
                f'✅ Procedimiento "{self.object.nombre}" eliminado exitosamente.'
            )
            self.object.delete()
        
        return redirect(self.success_url)


# ==================== VISTAS DE PRECIOS POR CLÍNICA ====================

class ClinicaProcedimientoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de precios de procedimientos por clínica"""
    model = ClinicaProcedimiento
    template_name = 'procedimientos/precio_list.html'
    context_object_name = 'precios'
    paginate_by = 20
    permission_required = 'procedimientos.view_clinicaprocedimiento'
    
    def get_queryset(self):
        queryset = ClinicaProcedimiento.objects.select_related(
            'clinica', 'procedimiento'
        ).order_by('clinica__nombre', 'procedimiento__categoria', 'procedimiento__nombre')
        
        # Filtrar por clínica del usuario si no es admin
        if not self.request.user.is_staff:
            from usuarios.models import UsuarioClinica
            try:
                usuario_clinica = UsuarioClinica.objects.get(
                    usuario=self.request.user,
                    activo=True
                )
                queryset = queryset.filter(clinica=usuario_clinica.clinica)
            except UsuarioClinica.DoesNotExist:
                queryset = queryset.none()
        
        # Búsqueda
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(procedimiento__nombre__icontains=search) |
                Q(procedimiento__codigo__icontains=search) |
                Q(clinica__nombre__icontains=search)
            )
        
        # Filtro por clínica
        clinica_id = self.request.GET.get('clinica', '').strip()
        if clinica_id:
            queryset = queryset.filter(clinica_id=clinica_id)
        
        # Filtro por categoría
        categoria = self.request.GET.get('categoria', '').strip()
        if categoria:
            queryset = queryset.filter(procedimiento__categoria=categoria)
        
        # Filtro por estado
        estado = self.request.GET.get('estado', '').strip()
        if estado == 'activo':
            queryset = queryset.filter(activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(activo=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = ProcedimientoOdontologico.CATEGORIA_CHOICES
        
        # Clínicas disponibles
        from clinicas.models import Clinica
        if self.request.user.is_staff:
            context['clinicas'] = Clinica.objects.filter(estado=True)
        else:
            from usuarios.models import UsuarioClinica
            try:
                usuario_clinica = UsuarioClinica.objects.get(
                    usuario=self.request.user,
                    activo=True
                )
                context['clinicas'] = Clinica.objects.filter(
                    id=usuario_clinica.clinica_id,
                    estado=True
                )
            except UsuarioClinica.DoesNotExist:
                context['clinicas'] = Clinica.objects.none()
        
        context['search'] = self.request.GET.get('search', '')
        context['clinica_filter'] = self.request.GET.get('clinica', '')
        context['categoria_filter'] = self.request.GET.get('categoria', '')
        context['estado_filter'] = self.request.GET.get('estado', '')
        return context


class ClinicaProcedimientoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crear nuevo precio para procedimiento"""
    model = ClinicaProcedimiento
    form_class = ClinicaProcedimientoForm
    template_name = 'procedimientos/precio_form.html'
    success_url = reverse_lazy('procedimientos:precio-list')
    permission_required = 'procedimientos.add_clinicaprocedimiento'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.uc = self.request.user
        messages.success(
            self.request,
            f'✅ Precio para "{form.instance.procedimiento.nombre}" '
            f'en {form.instance.clinica.nombre} creado exitosamente.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Error al crear el precio. Revise los campos marcados.'
        )
        return super().form_invalid(form)


class ClinicaProcedimientoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Actualizar precio de procedimiento"""
    model = ClinicaProcedimiento
    form_class = ClinicaProcedimientoForm
    template_name = 'procedimientos/precio_form.html'
    success_url = reverse_lazy('procedimientos:precio-list')
    permission_required = 'procedimientos.change_clinicaprocedimiento'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.um = self.request.user
        messages.success(
            self.request,
            f'✅ Precio para "{form.instance.procedimiento.nombre}" actualizado exitosamente.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Error al actualizar el precio. Revise los campos marcados.'
        )
        return super().form_invalid(form)


class ClinicaProcedimientoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Eliminar precio de procedimiento"""
    model = ClinicaProcedimiento
    template_name = 'procedimientos/precio_confirm_delete.html'
    success_url = reverse_lazy('procedimientos:precio-list')
    permission_required = 'procedimientos.delete_clinicaprocedimiento'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(
            request,
            f'✅ Precio para "{self.object.procedimiento.nombre}" '
            f'en {self.object.clinica.nombre} eliminado exitosamente.'
        )
        return super().delete(request, *args, **kwargs)

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseForbidden
from usuarios.models import UsuarioClinica, RolUsuario
from usuarios.forms import UsuarioForm
from core.services.tenants import get_clinica_from_request


class UsuarioEsAdminMixin(UserPassesTestMixin):
    """
    Mixin que verifica que el usuario sea admin de clínica o super admin.
    """
    def test_func(self):
        # Super admin: acceso completo
        if self.request.user.is_superuser:
            return True
        
        # Admin de clínica: acceso solo a su clínica
        try:
            user_clinica = self.request.user.clinica_asignacion
            return user_clinica.rol == RolUsuario.ADMIN_CLINICA and user_clinica.activo
        except:
            return False


class UsuarioListView(LoginRequiredMixin, UsuarioEsAdminMixin, ListView):
    """
    Vista para listar usuarios de la clínica.
    Solo accesible por admin de clínica o super admin.
    """
    model = UsuarioClinica
    template_name = 'usuarios/usuarioclinica_list.html'
    context_object_name = 'usuarios'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtrar usuarios según rol del usuario actual"""
        # Super admin: ver todos
        if self.request.user.is_superuser:
            return UsuarioClinica.objects.select_related('usuario', 'clinica').order_by('-fecha_creacion')
        
        # Admin de clínica: solo ver usuarios de su clínica
        try:
            user_clinica = self.request.user.clinica_asignacion
            clinica = user_clinica.clinica
            return UsuarioClinica.objects.filter(
                clinica=clinica
            ).select_related('usuario', 'clinica').order_by('-fecha_creacion')
        except:
            return UsuarioClinica.objects.none()
    
    def get_context_data(self, **kwargs):
        """Agregar datos al contexto"""
        context = super().get_context_data(**kwargs)
        
        # Si no es super admin, mostrar solo su clínica
        if not self.request.user.is_superuser:
            try:
                user_clinica = self.request.user.clinica_asignacion
                context['clinica_actual'] = user_clinica.clinica
            except:
                pass
        
        return context


class UsuarioCreateView(LoginRequiredMixin, UsuarioEsAdminMixin, CreateView):
    """
    Vista para crear un nuevo usuario y asignarlo a una clínica.
    """
    model = User
    form_class = UsuarioForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuarios:lista')
    
    def form_valid(self, form):
        """Procesar formulario válido"""
        response = super().form_valid(form)
        
        # Mostrar credenciales si es creación
        if hasattr(form, 'password_temporal'):
            messages.success(
                self.request,
                f'✅ Usuario creado exitosamente.\n'
                f'Email: {form.cleaned_data["email"]}\n'
                f'Contraseña temporal: {form.password_temporal}\n'
                f'Clínica: {form.cleaned_data["clinica"].nombre}\n'
                f'Rol: {form.cleaned_data["rol"]}'
            )
        else:
            messages.success(
                self.request,
                f'✅ Usuario actualizado exitosamente.'
            )
        
        return response
    
    def get_form_kwargs(self):
        """Pasar contexto al formulario"""
        kwargs = super().get_form_kwargs()
        
        # Si no es super admin, restringir a su clínica
        if not self.request.user.is_superuser:
            try:
                user_clinica = self.request.user.clinica_asignacion
                kwargs['initial'] = {'clinica': user_clinica.clinica}
            except:
                pass
        
        return kwargs


class UsuarioUpdateView(LoginRequiredMixin, UsuarioEsAdminMixin, UpdateView):
    """
    Vista para editar un usuario existente.
    """
    model = User
    form_class = UsuarioForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuarios:lista')
    
    def get_object(self, queryset=None):
        """Obtener usuario con validación de acceso"""
        usuario = super().get_object(queryset)
        
        # Validar acceso: solo admin de la clínica del usuario o super admin
        if not self.request.user.is_superuser:
            try:
                user_clinica_actual = self.request.user.clinica_asignacion
                user_clinica_target = usuario.clinica_asignacion
                
                if user_clinica_actual.clinica != user_clinica_target.clinica:
                    raise Http404("No tienes permiso para editar este usuario.")
            except:
                raise Http404("No tienes permiso para editar este usuario.")
        
        return usuario
    
    def form_valid(self, form):
        """Procesar formulario válido"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'✅ Usuario actualizado exitosamente.'
        )
        return response


class UsuarioDeleteView(LoginRequiredMixin, UsuarioEsAdminMixin, DeleteView):
    """
    Vista para soft-delete de un usuario (marcar como inactivo).
    """
    model = UsuarioClinica
    template_name = 'usuarios/usuarioclinica_confirm_delete.html'
    success_url = reverse_lazy('usuarios:lista')
    
    def get_object(self, queryset=None):
        """Obtener UsuarioClinica con validación"""
        usuario_clinica = super().get_object(queryset)
        
        # Validar acceso
        if not self.request.user.is_superuser:
            try:
                user_clinica_actual = self.request.user.clinica_asignacion
                if user_clinica_actual.clinica != usuario_clinica.clinica:
                    raise Http404("No tienes permiso para eliminar este usuario.")
            except:
                raise Http404("No tienes permiso para eliminar este usuario.")
        
        return usuario_clinica
    
    def delete(self, request, *args, **kwargs):
        """Soft delete: marcar como inactivo"""
        self.object = self.get_object()
        self.object.activo = False
        self.object.save()
        
        messages.success(
            request,
            f'✅ Usuario marcado como inactivo.'
        )
        
        return redirect(self.success_url)


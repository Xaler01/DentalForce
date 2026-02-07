from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q
from usuarios.models import UsuarioClinica, RolUsuario, RolUsuarioDentalForce, PermisoPersonalizado
from usuarios.forms import UsuarioForm, PerfilUsuarioForm
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


class PerfilUsuarioView(LoginRequiredMixin, UpdateView):
    """
    Vista para que cualquier usuario pueda editar su propio perfil.
    No requiere permisos de admin.
    """
    model = User
    form_class = PerfilUsuarioForm
    template_name = 'usuarios/perfil_form.html'
    success_url = reverse_lazy('usuarios:mi_perfil')
    
    def get_object(self, queryset=None):
        """Siempre devuelve el usuario actual"""
        return self.request.user
    
    def form_valid(self, form):
        """Procesar formulario válido"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'✅ Tu perfil ha sido actualizado exitosamente.'
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


# ================================
# GESTIÓN DE ROLES Y PERMISOS
# ================================

class RolListView(LoginRequiredMixin, UsuarioEsAdminMixin, ListView):
    """
    Lista todos los roles disponibles para la clínica del usuario.
    Solo accesible para Admin de Clínica.
    """
    model = RolUsuarioDentalForce
    template_name = 'usuarios/rol_list.html'
    context_object_name = 'roles'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Solo mostrar:
        1. Roles globales del sistema
        2. Roles personalizados de su clínica (si es admin)
        """
        clinica = self.request.user.clinica_asignacion.clinica
        return RolUsuarioDentalForce.objects.filter(
            Q(clinica=None) | Q(clinica=clinica),
            activo=True
        ).order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clinica = self.request.user.clinica_asignacion.clinica
        context['clinica'] = clinica
        return context


class RolDetailView(LoginRequiredMixin, UsuarioEsAdminMixin, DetailView):
    """Vista detallada de un rol con sus permisos"""
    model = RolUsuarioDentalForce
    template_name = 'usuarios/rol_detail.html'
    context_object_name = 'rol'
    
    def get_queryset(self):
        clinica = self.request.user.clinica_asignacion.clinica
        return RolUsuarioDentalForce.objects.filter(
            Q(clinica=None) | Q(clinica=clinica)
        )


class PermisoListView(LoginRequiredMixin, UsuarioEsAdminMixin, ListView):
    """
    Lista todos los permisos disponibles para asignar a roles/usuarios.
    Agrupados por categoría.
    """
    model = PermisoPersonalizado
    template_name = 'usuarios/permiso_list.html'
    context_object_name = 'permisos'
    
    def get_queryset(self):
        clinica = self.request.user.clinica_asignacion.clinica
        return PermisoPersonalizado.objects.filter(
            Q(clinica=None) | Q(clinica=clinica),
            activo=True
        ).order_by('categoria', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agrupar permisos por categoría
        clinica = self.request.user.clinica_asignacion.clinica
        permisos = PermisoPersonalizado.objects.filter(
            Q(clinica=None) | Q(clinica=clinica),
            activo=True
        )
        
        permisos_por_categoria = {}
        for permiso in permisos:
            cat = permiso.get_categoria_display()
            if cat not in permisos_por_categoria:
                permisos_por_categoria[cat] = []
            permisos_por_categoria[cat].append(permiso)
        
        context['permisos_por_categoria'] = permisos_por_categoria
        context['clinica'] = clinica
        
        return context


class UsuarioRolesUpdateView(LoginRequiredMixin, UsuarioEsAdminMixin, UpdateView):
    """
    Permite asignar roles y permisos a un usuario.
    Solo accesible para Admin de Clínica (de su propia clínica).
    """
    model = UsuarioClinica
    template_name = 'usuarios/usuario_roles_form.html'
    fields = ['roles_personalizados', 'permisos_adicionales']
    success_url = reverse_lazy('usuarios:lista')
    
    def get_queryset(self):
        """Solo puede editar usuarios de su propia clínica"""
        clinica = self.request.user.clinica_asignacion.clinica
        return UsuarioClinica.objects.filter(clinica=clinica)
    
    def get_form(self):
        """Filtrar roles y permisos disponibles"""
        form = super().get_form()
        clinica = self.request.user.clinica_asignacion.clinica
        
        # Solo mostrar roles y permisos de su clínica o globales
        form.fields['roles_personalizados'].queryset = RolUsuarioDentalForce.objects.filter(
            Q(clinica=None) | Q(clinica=clinica),
            activo=True
        )
        
        form.fields['permisos_adicionales'].queryset = PermisoPersonalizado.objects.filter(
            Q(clinica=None) | Q(clinica=clinica),
            activo=True
        )
        
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_clinica = self.object
        
        # Mostrar información del usuario
        context['usuario_editado'] = usuario_clinica.usuario
        context['roles_actuales'] = usuario_clinica.roles_personalizados.all()
        context['permisos_actuales'] = usuario_clinica.permisos_adicionales.all()
        context['permisos_totales'] = usuario_clinica.get_permisos()
        
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        usuario = self.object.usuario
        messages.success(
            self.request,
            f'✅ Roles y permisos de {usuario.get_full_name() or usuario.username} actualizados.'
        )
        return response


class CambiarContrasenaObligatorioView(LoginRequiredMixin, UpdateView):
    """
    Vista para cambiar contraseña obligatoria en primer login.
    Se muestra si el usuario tiene contrasena_temporal=True.
    """
    model = User
    fields = []
    template_name = 'usuarios/cambiar_contrasena_obligatorio.html'
    success_url = reverse_lazy('bases:home')
    
    def get_object(self, queryset=None):
        """Siempre devuelve el usuario actual"""
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            user_clinica = self.request.user.clinica_asignacion
            context['contrasena_temporal'] = user_clinica.contrasena_temporal
        except:
            context['contrasena_temporal'] = False
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesar cambio de contraseña"""
        password_nueva = request.POST.get('password_nueva', '').strip()
        password_confirmar = request.POST.get('password_confirmar', '').strip()
        
        # Validar que no estén vacías
        if not password_nueva or not password_confirmar:
            messages.error(request, '❌ La contraseña no puede estar vacía.')
            return self.get(request, *args, **kwargs)
        
        # Validar que coincidan
        if password_nueva != password_confirmar:
            messages.error(request, '❌ Las contraseñas no coinciden.')
            return self.get(request, *args, **kwargs)
        
        # Validar longitud mínima
        if len(password_nueva) < 8:
            messages.error(request, '❌ La contraseña debe tener al menos 8 caracteres.')
            return self.get(request, *args, **kwargs)
        
        # Cambiar contraseña
        user = self.request.user
        user.set_password(password_nueva)
        user.save()
        
        # Marcar contraseña como no-temporal
        try:
            user_clinica = user.clinica_asignacion
            user_clinica.contrasena_temporal = False
            user_clinica.save()
        except:
            pass
        
        # Mensaje de éxito
        messages.success(request, '✅ Contraseña cambió correctamente. Ahora puedes acceder al sistema.')
        
        # Redirigir a home
        return redirect(self.success_url)


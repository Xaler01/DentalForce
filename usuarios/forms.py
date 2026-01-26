import secrets
import re
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from usuarios.models import UsuarioClinica, RolUsuario
from clinicas.models import Clinica


class UsuarioForm(forms.ModelForm):
    """
    Formulario para crear/editar usuarios con asignación a clínica y rol.
    
    Maneja tanto la creación del User como la del UsuarioClinica.
    """
    
    clinica = forms.ModelChoiceField(
        queryset=Clinica.objects.filter(estado=True),
        required=True,
        label='Clínica',
        help_text='Selecciona la clínica a la que pertenece este usuario'
    )
    
    rol = forms.ChoiceField(
        choices=RolUsuario.choices,
        required=True,
        label='Rol',
        help_text='Selecciona el rol del usuario en la clínica'
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
    
    def __init__(self, *args, **kwargs):
        """Inicializar formulario y configurar widgets"""
        self.user = kwargs.pop('instance', None)  # Usuario existente (si es edición)
        super().__init__(*args, **kwargs)
        
        # Configurar widgets
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['clinica'].widget.attrs.update({'class': 'form-control'})
        self.fields['rol'].widget.attrs.update({'class': 'form-control'})
        
        # Si es edición, cargar datos de UsuarioClinica
        if self.user and hasattr(self.user, 'clinica_asignacion'):
            user_clinica = self.user.clinica_asignacion
            self.fields['clinica'].initial = user_clinica.clinica
            self.fields['rol'].initial = user_clinica.rol
    
    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        
        # Si es edición, permitir el email del usuario actual
        if self.user:
            if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
                raise ValidationError('Este email ya está registrado en el sistema.')
        else:
            # Si es creación, no permitir email duplicado
            if User.objects.filter(email=email).exists():
                raise ValidationError('Este email ya está registrado en el sistema.')
        
        return email
    
    def clean_first_name(self):
        """Validar que nombre no sea vacío"""
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name or len(first_name) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        return first_name
    
    def clean_rol(self):
        """Validar que no se cree super admin desde formulario"""
        rol = self.cleaned_data.get('rol')
        if rol == RolUsuario.SUPER_ADMIN:
            raise ValidationError(
                'No puedes crear usuarios con rol Super Admin desde este formulario. '
                'Contacta al equipo de administración.'
            )
        return rol
    
    def save(self, commit=True):
        """Guardar usuario y crear/actualizar UsuarioClinica"""
        # Si es creación, generar username desde email y contraseña temporal
        if not self.user:
            # Generar username único derivado del email
            base_username = self.cleaned_data['email'].split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data.get('last_name', ''),
                is_staff=False,
                is_superuser=False
            )
            
            # Generar contraseña temporal
            password_temporal = secrets.token_urlsafe(12)
            user.set_password(password_temporal)
            if commit:
                user.save()
            
            # Guardar en sesión para mostrar credenciales después
            self.password_temporal = password_temporal
        else:
            # Edición de usuario existente
            user = self.user
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data.get('last_name', '')
            if commit:
                user.save()
        
        # Crear o actualizar UsuarioClinica
        if commit:
            clinica = self.cleaned_data['clinica']
            rol = self.cleaned_data['rol']
            
            usuario_clinica, created = UsuarioClinica.objects.update_or_create(
                usuario=user,
                defaults={
                    'clinica': clinica,
                    'rol': rol,
                    'activo': True
                }
            )
            
            self.usuario_clinica = usuario_clinica
        
        return user


class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario para que un usuario edite su propio perfil.
    Solo permite editar campos básicos: nombre, apellido y email.
    """
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-user',
            'placeholder': 'Ingresa tu nombre'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Apellido',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-user',
            'placeholder': 'Ingresa tu apellido'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-user',
            'placeholder': 'tu_email@ejemplo.com'
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

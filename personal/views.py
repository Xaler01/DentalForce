from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q, Count
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView
from django.views import View

from clinicas.models import Clinica, Sucursal
from core.services.tenants import get_clinica_from_request
from usuarios.views import UsuarioEsAdminMixin
from .models import Personal, RegistroHorasPersonal
from .forms import PersonalForm, RegistroHorasPersonalForm


class PersonalListView(LoginRequiredMixin, UsuarioEsAdminMixin, ListView):
	model = Personal
	template_name = 'personal/personal_list.html'
	context_object_name = 'personal_list'

	def get_queryset(self):
		queryset = Personal.objects.select_related(
			'sucursal_principal', 'sucursal_principal__clinica', 'usuario'
		).filter(estado=True)
		
		# Restringir por clínica activa si no es superadmin
		clinica_activa = get_clinica_from_request(self.request)
		if not self.request.user.is_superuser and clinica_activa:
			queryset = queryset.filter(sucursal_principal__clinica=clinica_activa)
		
		# Filtro por clínica (solo si superadmin)
		clinica_id = self.request.GET.get('clinica')
		if self.request.user.is_superuser and clinica_id:
			queryset = queryset.filter(sucursal_principal__clinica_id=clinica_id)
		
		# Filtro por sucursal
		sucursal_id = self.request.GET.get('sucursal')
		if sucursal_id:
			queryset = queryset.filter(sucursal_principal_id=sucursal_id)
		
		return queryset.order_by('usuario__first_name', 'usuario__last_name')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		clinica_activa = get_clinica_from_request(self.request)
		if self.request.user.is_superuser:
			context['clinicas'] = Clinica.objects.filter(estado=True)
			context['sucursales'] = Sucursal.objects.filter(estado=True).select_related('clinica')
		else:
			context['clinicas'] = Clinica.objects.filter(id=clinica_activa.id) if clinica_activa else Clinica.objects.none()
			context['sucursales'] = Sucursal.objects.filter(clinica=clinica_activa, estado=True) if clinica_activa else Sucursal.objects.none()
		return context


class PersonalCreateView(LoginRequiredMixin, UsuarioEsAdminMixin, CreateView):
	model = Personal
	form_class = PersonalForm
	template_name = 'personal/personal_form.html'
	success_url = '/personal/'

	def form_valid(self, form):
		form.instance.uc = self.request.user
		response = super().form_valid(form)
		messages.success(self.request, '✅ Personal creado correctamente')
		return response

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['request'] = self.request
		return kwargs


class PersonalUpdateView(LoginRequiredMixin, UsuarioEsAdminMixin, UpdateView):
	model = Personal
	form_class = PersonalForm
	template_name = 'personal/personal_form.html'
	success_url = '/personal/'

	def form_valid(self, form):
		form.instance.um = self.request.user.id
		response = super().form_valid(form)
		messages.success(self.request, '✅ Personal actualizado correctamente')
		return response

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['request'] = self.request
		return kwargs


class PersonalHorasExtraCreateView(LoginRequiredMixin, CreateView):
	model = RegistroHorasPersonal
	form_class = RegistroHorasPersonalForm
	template_name = 'personal/horas_extra_form.html'
	success_url = '/personal/horas-extra/'

	def form_valid(self, form):
		try:
			personal = self.request.user.personal_profile
		except Personal.DoesNotExist:
			messages.error(self.request, '❌ No tiene perfil de Personal asociado')
			return redirect('personal:personal-list')

		form.instance.personal = personal
		form.instance.uc = self.request.user
		response = super().form_valid(form)
		messages.success(self.request, '✅ Horas extra registradas correctamente')
		return response


class PersonalHorasExtraListView(LoginRequiredMixin, ListView):
	model = RegistroHorasPersonal
	template_name = 'personal/horas_extra_list.html'
	context_object_name = 'horas_list'

	def get_queryset(self):
		queryset = RegistroHorasPersonal.objects.select_related(
			'personal', 'personal__usuario', 'personal__sucursal_principal', 'personal__sucursal_principal__clinica'
		)

		# Si no es admin, solo puede ver sus propios registros
		if not self._es_admin():
			queryset = queryset.filter(personal__usuario=self.request.user)
		else:
			clinica_activa = get_clinica_from_request(self.request)
			if clinica_activa and not self.request.user.is_superuser:
				queryset = queryset.filter(personal__sucursal_principal__clinica=clinica_activa)
		
		# Filtro por estado
		estado = self.request.GET.get('estado')
		if estado:
			queryset = queryset.filter(estado=estado)
		
		# Filtro por clínica
		clinica_id = self.request.GET.get('clinica')
		if self.request.user.is_superuser and clinica_id:
			queryset = queryset.filter(personal__sucursal_principal__clinica_id=clinica_id)
		
		# Filtro por sucursal
		sucursal_id = self.request.GET.get('sucursal')
		if sucursal_id:
			queryset = queryset.filter(personal__sucursal_principal_id=sucursal_id)
		
		# Filtro por mes/año
		mes = self.request.GET.get('mes')
		anio = self.request.GET.get('anio')
		if mes and anio:
			queryset = queryset.filter(fecha__month=mes, fecha__year=anio)
		
		return queryset.order_by('-fecha')

	def _es_admin(self):
		if self.request.user.is_superuser:
			return True
		try:
			return self.request.user.clinica_asignacion.es_admin
		except Exception:
			return False

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		clinica_activa = get_clinica_from_request(self.request)
		if self.request.user.is_superuser:
			context['clinicas'] = Clinica.objects.filter(estado=True)
			context['sucursales'] = Sucursal.objects.filter(estado=True).select_related('clinica')
		else:
			context['clinicas'] = Clinica.objects.filter(id=clinica_activa.id) if clinica_activa else Clinica.objects.none()
			context['sucursales'] = Sucursal.objects.filter(clinica=clinica_activa, estado=True) if clinica_activa else Sucursal.objects.none()
		
		# Estadísticas de estado
		queryset = self.get_queryset()
		context['total_pendientes'] = queryset.filter(estado='PENDIENTE').count()
		context['total_aprobados'] = queryset.filter(estado='APROBADO').count()
		context['total_rechazados'] = queryset.filter(estado='RECHAZADO').count()
		
		return context


class PersonalHorasExtraAprobarView(LoginRequiredMixin, UsuarioEsAdminMixin, UpdateView):
	model = RegistroHorasPersonal
	fields = ['estado', 'observaciones']
	template_name = 'personal/horas_extra_aprobar.html'
	success_url = '/personal/horas-extra/'

	def form_valid(self, form):
		if form.instance.estado == 'APROBADO':
			form.instance.aprobado_por = self.request.user
			form.instance.aprobado_en = timezone.now()
		response = super().form_valid(form)
		messages.success(self.request, '✅ Registro actualizado')
		return response


class PersonalHorasExtraAprobarMasivaView(LoginRequiredMixin, UsuarioEsAdminMixin, View):
	"""Vista para aprobación masiva de horas extra"""
	
	def get(self, request):
		# Obtener registros pendientes
		queryset = RegistroHorasPersonal.objects.select_related(
			'personal', 'personal__usuario', 'personal__sucursal_principal__clinica'
		).filter(estado='PENDIENTE')

		clinica_activa = get_clinica_from_request(request)
		if clinica_activa and not request.user.is_superuser:
			queryset = queryset.filter(personal__sucursal_principal__clinica=clinica_activa)
		
		# Aplicar filtros (solo superadmin puede cambiar clínica)
		clinica_id = request.GET.get('clinica')
		if request.user.is_superuser and clinica_id:
			queryset = queryset.filter(personal__sucursal_principal__clinica_id=clinica_id)
		
		sucursal_id = request.GET.get('sucursal')
		if sucursal_id:
			queryset = queryset.filter(personal__sucursal_principal_id=sucursal_id)
		
		mes = request.GET.get('mes')
		anio = request.GET.get('anio')
		if mes and anio:
			queryset = queryset.filter(fecha__month=mes, fecha__year=anio)
		
		context = {
			'registros_pendientes': queryset.order_by('fecha'),
			'clinicas': Clinica.objects.filter(estado=True) if request.user.is_superuser else (Clinica.objects.filter(id=clinica_activa.id) if clinica_activa else Clinica.objects.none()),
			'sucursales': Sucursal.objects.filter(estado=True).select_related('clinica') if request.user.is_superuser else (Sucursal.objects.filter(clinica=clinica_activa, estado=True) if clinica_activa else Sucursal.objects.none()),
		}
		
		return render(request, 'personal/horas_extra_aprobar_masiva.html', context)
	
	def post(self, request):
		# Obtener IDs seleccionados
		ids_seleccionados = request.POST.getlist('registros_seleccionados')
		accion = request.POST.get('accion')
		observaciones = request.POST.get('observaciones', '')
		
		if not ids_seleccionados:
			messages.warning(request, '⚠️ Debe seleccionar al menos un registro')
			return redirect('personal:horas-extra-aprobar-masiva')
		
		# Actualizar registros
		registros = RegistroHorasPersonal.objects.filter(id__in=ids_seleccionados, estado='PENDIENTE')
		
		if accion == 'aprobar':
			registros.update(
				estado='APROBADO',
				aprobado_por=request.user,
				aprobado_en=timezone.now(),
				observaciones=observaciones
			)
			messages.success(request, f'✅ {registros.count()} registros aprobados correctamente')
		elif accion == 'rechazar':
			registros.update(
				estado='RECHAZADO',
				aprobado_por=request.user,
				aprobado_en=timezone.now(),
				observaciones=observaciones
			)
			messages.success(request, f'✅ {registros.count()} registros rechazados')
		
		return redirect('personal:horas-extra-aprobar-masiva')


class PersonalNominaReporteView(LoginRequiredMixin, UsuarioEsAdminMixin, View):
	"""Vista para generar reporte mensual de nómina"""
	
	def get(self, request):
		# Valores por defecto: mes y año actual
		hoy = timezone.now()
		mes = int(request.GET.get('mes', hoy.month))
		anio = int(request.GET.get('anio', hoy.year))
		
		# Obtener todo el personal activo
		personal_queryset = Personal.objects.filter(estado=True).select_related(
			'usuario', 'sucursal_principal', 'sucursal_principal__clinica'
		)
		clinica_activa = get_clinica_from_request(request)
		if clinica_activa and not request.user.is_superuser:
			personal_queryset = personal_queryset.filter(sucursal_principal__clinica=clinica_activa)
		
		# Aplicar filtros (solo superadmin puede cambiar clínica)
		clinica_id = request.GET.get('clinica')
		if request.user.is_superuser and clinica_id:
			personal_queryset = personal_queryset.filter(sucursal_principal__clinica_id=clinica_id)
		
		sucursal_id = request.GET.get('sucursal')
		if sucursal_id:
			personal_queryset = personal_queryset.filter(sucursal_principal_id=sucursal_id)
		
		# Calcular datos de nómina para cada personal
		nomina_data = []
		totales = {
			'salario_base': Decimal('0'),
			'horas_normales_total': Decimal('0'),
			'horas_25_total': Decimal('0'),
			'horas_50_total': Decimal('0'),
			'horas_100_total': Decimal('0'),
			'valor_horas_extra': Decimal('0'),
			'total_pagar': Decimal('0'),
		}
		
		for personal in personal_queryset:
			# Obtener horas extra aprobadas del mes
			horas_mes = RegistroHorasPersonal.objects.filter(
				personal=personal,
				fecha__month=mes,
				fecha__year=anio,
				estado='APROBADO'
			).aggregate(
				horas_total=Sum('horas') or Decimal('0'),
				horas_25=Sum('horas', filter=Q(tipo_extra='RECARGO_25')) or Decimal('0'),
				horas_50=Sum('horas', filter=Q(tipo_extra='RECARGO_50')) or Decimal('0'),
				horas_100=Sum('horas', filter=Q(tipo_extra='RECARGO_100')) or Decimal('0'),
				horas_sabado=Sum('horas', filter=Q(tipo_extra='SABADO_MEDIO_DIA')) or Decimal('0'),
				valor_total=Sum('valor_total') or Decimal('0'),
			)
			
			# Calcular totales
			salario = personal.salario_mensual or Decimal('0')
			valor_horas = horas_mes['valor_total'] or Decimal('0')
			total = salario + valor_horas
			
			nomina_data.append({
				'personal': personal,
				'salario_base': salario,
				'horas_normales': horas_mes['horas_total'] or Decimal('0'),
				'horas_25': horas_mes['horas_25'] or Decimal('0'),
				'horas_50': horas_mes['horas_50'] or Decimal('0'),
				'horas_100': horas_mes['horas_100'] or Decimal('0'),
				'horas_sabado': horas_mes['horas_sabado'] or Decimal('0'),
				'valor_horas_extra': valor_horas,
				'total_pagar': total,
			})
			
			# Acumular totales generales
			totales['salario_base'] += salario
			totales['horas_normales_total'] += horas_mes['horas_total'] or Decimal('0')
			totales['horas_25_total'] += horas_mes['horas_25'] or Decimal('0')
			totales['horas_50_total'] += horas_mes['horas_50'] or Decimal('0')
			totales['horas_100_total'] += horas_mes['horas_100'] or Decimal('0')
			totales['valor_horas_extra'] += valor_horas
			totales['total_pagar'] += total
		
		context = {
			'nomina_data': nomina_data,
			'totales': totales,
			'mes': mes,
			'anio': anio,
			'mes_nombre': timezone.datetime(anio, mes, 1).strftime('%B %Y'),
			'clinicas': Clinica.objects.filter(estado=True) if request.user.is_superuser else (Clinica.objects.filter(id=clinica_activa.id) if clinica_activa else Clinica.objects.none()),
			'sucursales': Sucursal.objects.filter(estado=True).select_related('clinica') if request.user.is_superuser else (Sucursal.objects.filter(clinica=clinica_activa, estado=True) if clinica_activa else Sucursal.objects.none()),
		}
		
		return render(request, 'personal/nomina_reporte.html', context)

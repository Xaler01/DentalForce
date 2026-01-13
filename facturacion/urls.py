"""
URLs para el módulo de Facturación
"""
from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    # Lista y búsqueda
    path('', views.lista_facturas, name='lista'),
    
    # CRUD de facturas
    path('nueva/', views.nueva_factura, name='nueva'),
    path('<int:pk>/', views.detalle_factura, name='detalle'),
    path('<int:pk>/items/', views.editar_items_factura, name='editar_items'),
    path('<int:factura_pk>/items/<int:item_pk>/eliminar/', views.eliminar_item_factura, name='eliminar_item'),
    
    # Pagos
    path('<int:pk>/pago/', views.registrar_pago, name='registrar_pago'),
    
    # Acciones
    path('<int:pk>/anular/', views.anular_factura, name='anular'),
    path('<int:pk>/imprimir/', views.imprimir_factura, name='imprimir'),
    
    # Reportes
    path('reportes/', views.reporte_facturas, name='reportes'),
    
    # AJAX
    path('api/citas-paciente/', views.obtener_citas_paciente, name='api_citas_paciente'),
]

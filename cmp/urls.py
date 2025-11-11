from django.urls import path

from .views import ProveedorView, ProveedorNew, ProveedorEdit, proveedorInactivar, \
    ComprasView, compras, compras_eliminar, compras_detalle_eliminar

urlpatterns = [
    path('proveedores/', ProveedorView.as_view(), name='proveedor_list'),
    path('proveedores/new', ProveedorNew.as_view(), name='proveedor_new'),
    path('proveedores/edit/<int:pk>', ProveedorEdit.as_view(), name='proveedor_edit'),
    path('proveedores/inactivar/<int:id>', proveedorInactivar, name='proveedor_inactivar'),

    path('compras/', ComprasView.as_view(), name='compras_list'),
    path('compras/new', compras, name='compras_new'),
    path('compras/edit/<int:compra_id>', compras, name="compras_edit"),
    path('compras/eliminar/<int:compra_id>', compras_eliminar, name='compras_eliminar'),
    path('compras/delete/<int:compra_id>/<int:detalle_id>', compras_detalle_eliminar, name='compras_detalle_eliminar'),
]

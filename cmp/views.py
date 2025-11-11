from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.urls import reverse_lazy
import datetime
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
import json
from django.db.models import Sum

from .models import Proveedor, ComprasEnc, ComprasDet
from cmp.forms import ProveedorForm, ComprasEncForm
from bases.views import SinPrivilegios
from inv.models import Producto


# Create your views here.

# INICIA VISTAS PROVEEDOR
class ProveedorView(SinPrivilegios, generic.ListView):
    model = Proveedor
    template_name = "cmp/proveedor_list.html"
    context_object_name = "obj"
    permission_required = "cmp.view_proveedor"


class ProveedorNew(SuccessMessageMixin, SinPrivilegios, generic.CreateView):
    model = Proveedor
    template_name = "cmp/proveedor_form.html"
    context_object_name = "obj"
    form_class = ProveedorForm
    success_url = reverse_lazy("cmp:proveedor_list")
    success_message = "Proveedor Nuevo"
    permission_required = "cmp.add_proveedor"

    def form_valid(self, form):
        form.instance.uc = self.request.user
        return super().form_valid(form)


class ProveedorEdit(SuccessMessageMixin, SinPrivilegios, generic.UpdateView):
    model = Proveedor
    template_name = "cmp/proveedor_form.html"
    context_object_name = "obj"
    form_class = ProveedorForm
    success_url = reverse_lazy("cmp:proveedor_list")
    success_message = "Proveedor Editado"
    permission_required = "cmp.change_proveedor"

    def form_valid(self, form):
        form.instance.um = self.request.user.id
        return super().form_valid(form)


@login_required(login_url="/login/")
@permission_required("cmp.change_proveedor", login_url="/login/")
def proveedorInactivar(request, id):
    template_name = "cmp/inactivar_prv.html"
    contexto = {}
    prv = Proveedor.objects.filter(pk=id).first()

    if not prv:
        return HttpResponse('Proveedor no existe ' + str(id))

    if request.method == 'GET':
        contexto = {'obj': prv}

    if request.method == 'POST':
        # Eliminar físicamente el proveedor en lugar de inactivarlo
        prv.delete()
        contexto = {'obj': 'OK'}
        return HttpResponse('Proveedor eliminado')

    return render(request, template_name, contexto)


class ComprasView(SinPrivilegios, generic.ListView):
    model = ComprasEnc
    template_name = "cmp/compras_list.html"
    context_object_name = "obj"
    permission_required = "cmp.view_comprasenc"


@login_required(login_url='/login/')
@permission_required('cmp.view_comprasenc', login_url='bases:sin_privilegios')
def compras(request, compra_id=None):
    template_name = "cmp/compras.html"
    prod = Producto.objects.filter(estado=True)
    form_compras = {}
    contexto = {}

    if request.method == 'GET':
        form_compras = ComprasEncForm()
        enc = ComprasEnc.objects.filter(pk=compra_id).first()

        if enc:
            det = ComprasDet.objects.filter(compra=enc)
            fecha_compra = datetime.date.isoformat(enc.fecha_compra)
            fecha_factura = datetime.date.isoformat(enc.fecha_factura)
            e = {
                'fecha_compra': fecha_compra,
                'proveedor': enc.proveedor,
                'observacion': enc.observacion,
                'no_factura': enc.no_factura,
                'fecha_factura': fecha_factura,
                'sub_total': round(float(enc.sub_total), 2),
                'descuento': round(float(enc.descuento), 2),
                'total': round(float(enc.total), 2)
            }

            form_compras = ComprasEncForm(e)
        else:
            det = None

        contexto = {'productos': prod, 'encabezado': enc, 'detalle': det, 'form_enc': form_compras}

    if request.method == 'POST':
        # Use the ModelForm to validate Encabezado; if validation passes save safely
        form_enc = ComprasEncForm(request.POST)
        if not compra_id:
            if form_enc.is_valid():
                # Use cleaned_data to ensure proper types
                cd = form_enc.cleaned_data
                prov = cd.get('proveedor')
                fecha_compra = cd.get('fecha_compra')
                fecha_factura = cd.get('fecha_factura')
                observacion = cd.get('observacion')
                no_factura = cd.get('no_factura')

                # create instance explicitly to avoid any accidental positional mapping issues
                try:
                    enc = ComprasEnc(
                        fecha_compra=fecha_compra,
                        observacion=observacion,
                        no_factura=no_factura,
                        fecha_factura=fecha_factura,
                        sub_total=cd.get('sub_total') or 0,
                        descuento=cd.get('descuento') or 0,
                        total=cd.get('total') or 0,
                        proveedor=prov,
                        uc=request.user
                    )
                    enc.save()
                    compra_id = enc.id
                except Exception as e:
                    # If saving fails, re-render the page with an error message
                    contexto = {'productos': prod, 'encabezado': None, 'detalle': None, 'form_enc': form_enc, 'error': str(e)}
                    return render(request, template_name, contexto)
            else:
                # validation failed: show errors
                contexto = {'productos': prod, 'encabezado': None, 'detalle': None, 'form_enc': form_enc}
                return render(request, template_name, contexto)
        else:
            enc = ComprasEnc.objects.filter(pk=compra_id).first()
            if enc:
                # update existing encabezado safely
                form_enc = ComprasEncForm(request.POST, instance=enc)
                if form_enc.is_valid():
                    enc = form_enc.save(commit=False)
                    enc.um = request.user.id
                    enc.save()
                else:
                    contexto = {'productos': prod, 'encabezado': enc, 'detalle': ComprasDet.objects.filter(compra=enc), 'form_enc': form_enc}
                    return render(request, template_name, contexto)

        if not compra_id:
            return redirect("cmp:compras_list")

        producto = request.POST.get("id_id_producto")
        cantidad = request.POST.get("id_cantidad_detalle")
        precio = request.POST.get("id_precio_detalle")
        sub_total_detalle = request.POST.get("id_sub_total_detalle")
        descuento_detalle = request.POST.get("id_descuento_detalle")
        total_detalle = request.POST.get("id_total_detalle")
        detalle_id = request.POST.get("id_detalle_id")  # ID del detalle si estamos editando
        tipo_descuento = request.POST.get("id_tipo_descuento", 'V')  # V: Valor, P: Porcentaje

        if not all([producto, cantidad, precio]):
            messages.error(request, "Todos los campos son requeridos")
            return redirect("cmp:compras_edit", compra_id=compra_id)

        try:
            prod = Producto.objects.get(pk=producto)
            # Convert string inputs to Decimal for precise calculation
            cantidad_dec = Decimal(str(cantidad))
            precio_dec = Decimal(str(precio))
            descuento_dec = Decimal(str(descuento_detalle)) if descuento_detalle else Decimal('0')
            
            # Calculate subtotal
            sub_total = cantidad_dec * precio_dec
            
            # Verificar si estamos editando un detalle existente
            if detalle_id:
                # Actualizar detalle existente
                det = ComprasDet.objects.filter(pk=detalle_id, compra=enc).first()
                if det:
                    det.producto = prod
                    det.cantidad = cantidad_dec
                    det.precio_prv = precio_dec
                    det.descuento = descuento_dec
                    det.tipo_descuento = tipo_descuento
                    det.sub_total = sub_total
                    # El total se calculará en el método save() del modelo
                    det.um = request.user.id
                    messages.success(request, "Detalle de compra actualizado con éxito")
                else:
                    messages.error(request, "Detalle no encontrado")
                    return redirect("cmp:compras_edit", compra_id=compra_id)
            else:
                # Crear nuevo detalle
                det = ComprasDet(
                    compra=enc,
                    producto=prod,
                    cantidad=cantidad_dec,
                    precio_prv=precio_dec,
                    descuento=descuento_dec,
                    tipo_descuento=tipo_descuento,
                    sub_total=sub_total,
                    costo=0,
                    uc=request.user
                )
                messages.success(request, "Detalle de compra guardado con éxito")
        except Producto.DoesNotExist:
            messages.error(request, "Producto no encontrado")
            return redirect("cmp:compras_edit", compra_id=compra_id)
        except (ValueError, InvalidOperation):
            messages.error(request, "Error en los valores ingresados. Verifique que sean números válidos")
            return redirect("cmp:compras_edit", compra_id=compra_id)

        if det:
            det.save()

            # Recalculate aggregates using the correct foreign key name 'compra'
            sub_total = ComprasDet.objects.filter(compra=enc).aggregate(Sum('sub_total'))
            descuento = ComprasDet.objects.filter(compra=enc).aggregate(Sum('descuento'))
            enc.sub_total = round(float(sub_total.get("sub_total__sum") or 0), 2)
            enc.descuento = round(float(descuento.get("descuento__sum") or 0), 2)
            enc.save()

        return redirect("cmp:compras_edit", compra_id=compra_id)

    return render(request, template_name, contexto)


@login_required(login_url='/login/')
@permission_required('cmp.delete_comprasenc', login_url='bases:sin_privilegios')
def compras_eliminar(request, compra_id):
    compra = get_object_or_404(ComprasEnc, pk=compra_id)
    
    if request.method == 'GET':
        # Eliminar todos los detalles asociados
        ComprasDet.objects.filter(compra=compra).delete()
        
        # Eliminar la compra
        compra.delete()
        
        messages.success(request, f"Compra '{compra.observacion}' eliminada correctamente")
        return redirect("cmp:compras_list")
    
    return redirect("cmp:compras_list")


@login_required(login_url='/login/')
@permission_required('cmp.delete_comprasdet', login_url='bases:sin_privilegios')
def compras_detalle_eliminar(request, compra_id, detalle_id):
    """
    Elimina un detalle específico de una compra y recalcula los totales
    """
    compra = get_object_or_404(ComprasEnc, pk=compra_id)
    detalle = get_object_or_404(ComprasDet, pk=detalle_id, compra=compra)
    
    # Eliminar el detalle
    detalle.delete()
    
    # Recalcular los totales de la compra con redondeo a 2 decimales
    sub_total = ComprasDet.objects.filter(compra=compra).aggregate(Sum('sub_total'))
    descuento = ComprasDet.objects.filter(compra=compra).aggregate(Sum('descuento'))
    
    compra.sub_total = round(float(sub_total.get("sub_total__sum") or 0), 2)
    compra.descuento = round(float(descuento.get("descuento__sum") or 0), 2)
    compra.save()
    
    messages.success(request, f"Detalle eliminado correctamente")
    return redirect("cmp:compras_edit", compra_id=compra_id)

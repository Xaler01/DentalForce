from django.http import HttpResponse
from django.shortcuts import render
#REQUEST  Sirve para realizar peticiones
#HttpResponses: Para enviar la respuesta usando el protocolo HTTP

def inicio(request):
    #return HttpResponse('Bienvenidos a la primera prueba')
    return render(request, 'index.html')

def inicio2(request):
    return HttpResponse('<p style= ¨color:red;¨>Bienvenidos a la primera prueba en rojo</p>')
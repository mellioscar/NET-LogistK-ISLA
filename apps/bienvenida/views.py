from django.shortcuts import render

# Create your views here.

def bienvenida_view(request):
    return render(request, 'bienvenida/bienvenida.html')

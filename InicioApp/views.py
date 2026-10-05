from django.shortcuts import render
from django.http import HttpResponse
import datetime
import json
import os


# Vista 1: Página principal
def Presentacion(request):

    ruta_json = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'Info_Game',
        'noticias.json'
    )

    with open(ruta_json, 'r', encoding='utf-8') as archivo:
        noticias = json.load(archivo)

    return render(request, 'inicio.html', {
        'noticias': noticias
    })


# Vista 2: Página de noticias
def noticias(request):

    ruta_json = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'Info_Game',
        'noticias.json'
    )

    with open(ruta_json, 'r', encoding='utf-8') as archivo:
        noticias = json.load(archivo)

    return render(request, 'noticias.html', {
        'noticias': noticias
    })


# Vista 3: Detalle de una noticia
def detalle_noticia(request, id):

    ruta_json = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'Info_Game',
        'noticias.json'
    )

    with open(ruta_json, 'r', encoding='utf-8') as archivo:
        noticias = json.load(archivo)

    noticia = next(
        (noticia for noticia in noticias if noticia['id'] == id),
        None
    )

    if noticia is None:
        return HttpResponse(
            "Noticia no encontrada",
            status=404
        )

    return render(request, 'detalle_noticia.html', {
        'noticia': noticia
    })


# Vista adicional: muestra la fecha actual
def ahora(request):

    fecha_actual = datetime.datetime.now()

    texto = f"<h2>Desde InicioApp hoy <b>{fecha_actual}</b></h2>"

    return HttpResponse(texto)
from django.urls import path

from InicioApp import views


urlpatterns = [

    path('', views.Presentacion, name='presentacion'),

    path('noticias/', views.noticias, name='noticias'),

    path('noticias/detalle/<int:id>/', views.detalle_noticia, name='detalle_noticia'),

    path('fecha_actual/', views.ahora, name='fecha_actual'),

]
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="vault_dashboard"),
    path("<str:module>/", views.record_list, name="vault_list"),
    path("<str:module>/nuevo/", views.record_form, name="vault_create"),
    path("<str:module>/<int:pk>/editar/", views.record_form, name="vault_edit"),
    path("<str:module>/<int:pk>/eliminar/", views.record_delete, name="vault_delete"),
]
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone

from .models import UserAccess


class AccessScheduleMiddleware:

    def __init__(self, get_response):

        self.get_response = get_response


    def __call__(self, request):

        user = request.user


        # ====================================================
        # SOLO CONTROLAR USUARIOS AUTENTICADOS
        # ====================================================

        if user.is_authenticated:


            # =================================================
            # EL ADMINISTRADOR NO TIENE RESTRICCIÓN
            # =================================================

            if user.is_superuser:

                return self.get_response(request)


            # =================================================
            # DETERMINAR SI ES OPERADOR O CONSULTA
            # =================================================

            restricted_role = user.groups.filter(
                name__in=[
                    "Operador",
                    "Consulta",
                ]
            ).exists()


            # Si no es Operador ni Consulta,
            # no se aplica este control.

            if not restricted_role:

                return self.get_response(request)


            # =================================================
            # OBTENER CONFIGURACIÓN DE ACCESO
            # =================================================

            access, created = UserAccess.objects.get_or_create(
                user=user
            )


            # =================================================
            # CUENTA SUSPENDIDA
            # =================================================

            if not access.enabled:

                logout(request)

                messages.warning(
                    request,
                    "Tu acceso se encuentra suspendido. "
                    "Solicita al Administrador que habilite "
                    "tu cuenta."
                )

                return redirect(
                    settings.LOGIN_URL
                )


            # =================================================
            # SIN RESTRICCIÓN HORARIA
            # =================================================
            #
            # ESTA ES LA PARTE IMPORTANTE.
            #
            # Si unrestricted_hours=True,
            # NO SE DEBE COMPROBAR access_start
            # NI access_end.
            #
            # Puede entrar a cualquier hora.

            if access.unrestricted_hours:

                return self.get_response(request)


            # =================================================
            # HORARIO RESTRINGIDO
            # =================================================

            current_time = timezone.localtime().time()

            start = access.access_start

            end = access.access_end


            # =================================================
            # HORARIO NORMAL
            # Ejemplo: 08:00 -> 18:00
            # =================================================

            if start < end:

                allowed = (
                    start <= current_time < end
                )


            # =================================================
            # HORARIO QUE CRUZA MEDIANOCHE
            # Ejemplo: 22:00 -> 06:00
            # =================================================

            else:

                allowed = (
                    current_time >= start
                    or
                    current_time < end
                )


            # =================================================
            # FUERA DEL HORARIO
            # =================================================

            if not allowed:

                logout(request)

                messages.warning(
                    request,
                    "Tu sesión fue cerrada porque estás "
                    "fuera de tu horario de acceso."
                )

                return redirect(
                    settings.LOGIN_URL
                )


        # ====================================================
        # CONTINUAR PETICIÓN
        # ====================================================

        return self.get_response(request)
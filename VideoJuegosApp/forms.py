from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.models import Group, User
from django.utils import timezone

from .models import (
    Game,
    GamerProfile,
    LibraryEntry,
    UserAccess,
)


# ============================================================
# ESTILO GENERAL DE FORMULARIOS
# ============================================================


class NeonFormMixin:

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            field.widget.attrs["class"] = "form-control"


# ============================================================
# FORMULARIO DE VIDEOJUEGOS
# ============================================================


class GameForm(NeonFormMixin, forms.ModelForm):

    class Meta:

        model = Game

        fields = (
            "title",
            "genre",
            "platform",
            "launch_year",
            "synopsis",
            "price",
            "stock",
            "cover",
            "technical_sheet",
        )

        labels = {
            "title": "Título",
            "genre": "Género",
            "platform": "Plataforma",
            "launch_year": "Año de lanzamiento",
            "synopsis": "Sinopsis",
            "price": "Precio",
            "stock": "Stock disponible",
            "cover": "Portada",
            "technical_sheet": "Ficha técnica",
        }

        widgets = {

            "synopsis": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe el videojuego..."
                }
            ),

            "price": forms.NumberInput(
                attrs={
                    "placeholder": "Ejemplo: 29990",
                    "min": "0",
                    "step": "1"
                }
            ),

            "stock": forms.NumberInput(
                attrs={
                    "placeholder": "Ejemplo: 15",
                    "min": "0",
                    "step": "1"
                }
            ),
        }


# ============================================================
# FORMULARIO DE PERFIL GAMER
# ============================================================


class GamerProfileForm(NeonFormMixin, forms.ModelForm):

    class Meta:

        model = GamerProfile

        fields = (
            "user",
            "nickname",
            "favorite_genre",
            "avatar",
        )


# ============================================================
# FORMULARIO DE BIBLIOTECA
# ============================================================


class LibraryEntryForm(NeonFormMixin, forms.ModelForm):

    class Meta:

        model = LibraryEntry

        fields = (
            "gamer",
            "game",
            "status",
            "score",
        )


# ============================================================
# FORMULARIO DE REGISTRO DE USUARIO
# ============================================================


class RegisterForm(forms.ModelForm):

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )

    password_confirm = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )

    email = forms.EmailField(
        label="Correo electrónico",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "type": "email",
                "autocomplete": "email",
                "placeholder": "ejemplo@correo.com",
                "inputmode": "email",
            }
        ),
    )

    class Meta:

        model = User

        fields = (
            "username",
            "email",
        )

        widgets = {

            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "username",
                    "placeholder": "Nombre de usuario",
                }
            ),
        }

        labels = {
            "username": "Nombre de usuario",
            "email": "Correo electrónico",
        }

    def clean_username(self):

        username = self.cleaned_data["username"]

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise forms.ValidationError(
                "Este nombre de usuario ya está registrado."
            )

        return username

    def clean_email(self):

        email = self.cleaned_data["email"].strip().lower()

        if not email:

            raise forms.ValidationError(
                "Debes ingresar un correo electrónico."
            )

        return email

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get(
            "password_confirm"
        )

        if (
            password
            and password_confirm
            and password != password_confirm
        ):

            raise forms.ValidationError(
                "Las contraseñas no coinciden."
            )

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        user.set_password(
            self.cleaned_data["password"]
        )

        if commit:
            user.save()

        return user


# ============================================================
# ROLES DEL SISTEMA
# ============================================================


ROLE_CHOICES = [
    ("Administrador", "Administrador"),
    ("Operador", "Operador"),
    ("Consulta", "Consulta"),
    ("Usuario", "Usuario"),
]


# ============================================================
# FORMULARIO ADMINISTRATIVO PARA CREAR USUARIOS
# ============================================================


class AdminUserCreateForm(
    NeonFormMixin,
    forms.ModelForm
):

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password"
            }
        )
    )

    password_confirm = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password"
            }
        )
    )

    role = forms.ChoiceField(
        label="Rol",
        choices=ROLE_CHOICES
    )

    class Meta:

        model = User

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "password",
            "password_confirm",
        )

        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }

        widgets = {

            "username": forms.TextInput(
                attrs={
                    "autocomplete": "username"
                }
            ),

            "first_name": forms.TextInput(
                attrs={
                    "autocomplete": "given-name"
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "autocomplete": "family-name"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email"
                }
            ),
        }

    def clean_username(self):

        username = self.cleaned_data["username"].strip()

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise forms.ValidationError(
                "Este nombre de usuario ya existe."
            )

        return username

    def clean_email(self):

        email = self.cleaned_data.get(
            "email",
            ""
        ).strip().lower()

        if email and User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "Este correo electrónico ya está registrado."
            )

        return email

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get(
            "password_confirm"
        )

        if (
            password
            and password_confirm
            and password != password_confirm
        ):

            raise forms.ValidationError(
                "Las contraseñas no coinciden."
            )

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        user.set_password(
            self.cleaned_data["password"]
        )

        role = self.cleaned_data.get("role")

        if role == "Administrador":

            user.is_superuser = True
            user.is_staff = True

        else:

            user.is_superuser = False
            user.is_staff = False

        if commit:

            user.save()

            self._apply_role(
                user,
                role
            )

        return user

    @staticmethod
    def _apply_role(user, role):

        user.groups.clear()

        if role == "Operador":

            group, created = Group.objects.get_or_create(
                name="Operador"
            )

            user.groups.add(group)

        elif role == "Consulta":

            group, created = Group.objects.get_or_create(
                name="Consulta"
            )

            user.groups.add(group)

        if role in [
            "Operador",
            "Consulta"
        ]:

            UserAccess.objects.get_or_create(
                user=user
            )

        else:

            UserAccess.objects.filter(
                user=user
            ).delete()


# ============================================================
# FORMULARIO ADMINISTRATIVO PARA EDITAR USUARIOS
# ============================================================


class AdminUserUpdateForm(
    NeonFormMixin,
    forms.ModelForm
):

    role = forms.ChoiceField(
        label="Rol",
        choices=ROLE_CHOICES
    )

    class Meta:

        model = User

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "is_active",
        )

        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
            "is_active": "Usuario activo",
        }

        widgets = {

            "username": forms.TextInput(
                attrs={
                    "autocomplete": "username"
                }
            ),

            "first_name": forms.TextInput(
                attrs={
                    "autocomplete": "given-name"
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "autocomplete": "family-name"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email"
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        user = self.instance

        if user.is_superuser:

            self.initial["role"] = "Administrador"

        elif user.groups.filter(
            name="Operador"
        ).exists():

            self.initial["role"] = "Operador"

        elif user.groups.filter(
            name="Consulta"
        ).exists():

            self.initial["role"] = "Consulta"

        else:

            self.initial["role"] = "Usuario"

    def clean_username(self):

        username = self.cleaned_data["username"].strip()

        exists = User.objects.filter(
            username__iexact=username
        ).exclude(
            pk=self.instance.pk
        ).exists()

        if exists:

            raise forms.ValidationError(
                "Este nombre de usuario ya existe."
            )

        return username

    def clean_email(self):

        email = self.cleaned_data.get(
            "email",
            ""
        ).strip().lower()

        exists = User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        ).exists()

        if email and exists:

            raise forms.ValidationError(
                "Este correo electrónico ya está registrado."
            )

        return email

    def clean_role(self):

        role = self.cleaned_data["role"]

        if (
            self.instance.pk
            and self.instance.is_superuser
            and role != "Administrador"
        ):

            raise forms.ValidationError(
                "El administrador principal debe conservar "
                "el rol Administrador."
            )

        return role

    def save(self, commit=True):

        user = super().save(commit=False)

        role = self.cleaned_data.get("role")

        if role == "Administrador":

            user.is_superuser = True
            user.is_staff = True

        else:

            user.is_superuser = False
            user.is_staff = False

        if commit:

            user.save()

            user.groups.clear()

            if role == "Operador":

                group, created = Group.objects.get_or_create(
                    name="Operador"
                )

                user.groups.add(group)

            elif role == "Consulta":

                group, created = Group.objects.get_or_create(
                    name="Consulta"
                )

                user.groups.add(group)

            if role in [
                "Operador",
                "Consulta"
            ]:

                UserAccess.objects.get_or_create(
                    user=user
                )

            else:

                UserAccess.objects.filter(
                    user=user
                ).delete()

        return user


# ============================================================
# CAMBIO DE CONTRASEÑA DESDE ADMINISTRACIÓN
# ============================================================


class AdminUserPasswordForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            field.widget.attrs["class"] = "form-control"


# ============================================================
# FORMULARIO DE CONTROL DE ACCESO
# ============================================================


class UserAccessForm(
    NeonFormMixin,
    forms.ModelForm
):

    class Meta:

        model = UserAccess

        fields = (
            "enabled",
            "unrestricted_hours",
            "access_start",
            "access_end",
        )

        labels = {
            "enabled": "Acceso habilitado",
            "unrestricted_hours": "Sin restricción horaria",
            "access_start": "Hora de inicio",
            "access_end": "Hora de término",
        }

        widgets = {

            "enabled": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),

            "unrestricted_hours": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),

            "access_start": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time"
                }
            ),

            "access_end": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time"
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        unrestricted = cleaned_data.get(
            "unrestricted_hours"
        )

        # Si no existe restricción horaria,
        # no es necesario validar las horas.
        if unrestricted:

            return cleaned_data

        start = cleaned_data.get("access_start")
        end = cleaned_data.get("access_end")

        if start and end and start == end:

            raise forms.ValidationError(
                "La hora de inicio y la hora de término "
                "no pueden ser iguales."
            )

        return cleaned_data


# ============================================================
# LOGIN CON CONTROL DE HORARIO
# ============================================================


class AccessAuthenticationForm(AuthenticationForm):

    def confirm_login_allowed(self, user):

        super().confirm_login_allowed(user)

        # ----------------------------------------------------
        # ADMINISTRADOR
        # SIN RESTRICCIÓN HORARIA
        # ----------------------------------------------------

        if user.is_superuser:

            return

        # ----------------------------------------------------
        # DETERMINAR SI ES OPERADOR O CONSULTA
        # ----------------------------------------------------

        restricted_role = user.groups.filter(
            name__in=[
                "Operador",
                "Consulta"
            ]
        ).exists()

        # Usuario normal:
        # puede iniciar sesión sin control horario.
        if not restricted_role:

            return

        # ----------------------------------------------------
        # OBTENER O CREAR CONTROL DE ACCESO
        # ----------------------------------------------------

        access, created = UserAccess.objects.get_or_create(
            user=user
        )

        # ----------------------------------------------------
        # SUSPENSIÓN MANUAL
        # ----------------------------------------------------

        if not access.enabled:

            raise forms.ValidationError(
                "Tu cuenta se encuentra suspendida. "
                "Solicita al Administrador que habilite "
                "tu acceso."
            )

        # ----------------------------------------------------
        # SIN RESTRICCIÓN HORARIA
        # ----------------------------------------------------

        if access.unrestricted_hours:

            return

        # ----------------------------------------------------
        # CONTROL HORARIO
        # ----------------------------------------------------

        current_time = timezone.localtime().time()

        start = access.access_start
        end = access.access_end

        # ----------------------------------------------------
        # HORARIO NORMAL
        # EJEMPLO: 08:00 - 18:00
        # ----------------------------------------------------

        if start < end:

            inside_schedule = (
                start <= current_time < end
            )

        # ----------------------------------------------------
        # HORARIO QUE CRUZA MEDIANOCHE
        # EJEMPLO: 22:00 - 06:00
        # ----------------------------------------------------

        else:

            inside_schedule = (
                current_time >= start
                or current_time < end
            )

        # ----------------------------------------------------
        # BLOQUEAR SI ESTÁ FUERA DE HORARIO
        # ----------------------------------------------------

        if not inside_schedule:

            raise forms.ValidationError(
                "Tu cuenta está fuera del horario de acceso "
                "permitido: "
                f"{start.strftime('%H:%M')} - "
                f"{end.strftime('%H:%M')}."
            )
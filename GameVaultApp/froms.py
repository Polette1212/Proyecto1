from django import forms
from django.contrib.auth.models import User

from .models import Game, GamerProfile, LibraryEntry


class NeonFormMixin:

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs
        )

        for field in self.fields.values():

            field.widget.attrs["class"] = "form-control"


# ============================================================
# FORMULARIO DE VIDEOJUEGOS
# ============================================================

class GameForm(
    NeonFormMixin,
    forms.ModelForm
):

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
# FORMULARIO DE PERFILES GAMER
# ============================================================

class GamerProfileForm(
    NeonFormMixin,
    forms.ModelForm
):

    class Meta:

        model = GamerProfile

        fields = (
            "user",
            "nickname",
            "favorite_genre",
            "avatar",
        )

        labels = {
            "user": "Usuario",
            "nickname": "Apodo",
            "favorite_genre": "Género favorito",
            "avatar": "Avatar",
        }


# ============================================================
# FORMULARIO DE BIBLIOTECA
# ============================================================

class LibraryEntryForm(
    NeonFormMixin,
    forms.ModelForm
):

    class Meta:

        model = LibraryEntry

        fields = (
            "gamer",
            "game",
            "status",
            "score",
        )

        labels = {
            "gamer": "Gamer",
            "game": "Videojuego",
            "status": "Estado",
            "score": "Puntuación",
        }


# ============================================================
# FORMULARIO DE REGISTRO
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

    class Meta:

        model = User

        fields = (
            "username",
            "email",
        )

        labels = {
            "username": "Nombre de usuario",
            "email": "Correo electrónico",
        }

        widgets = {

            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "username",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "email",
                }
            ),
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

        user = super().save(
            commit=False
        )

        user.set_password(
            self.cleaned_data["password"]
        )

        if commit:

            user.save()

        return user
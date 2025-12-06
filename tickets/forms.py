from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re

from .models import Ticket, Comentario, AsignacionCliente, Perfil, ComprobantePago


# ===========================
#   VALIDADORES AUXILIARES
# ===========================

# Solo letras (incluye acentos y ñ) y espacios
solo_letras_validator = RegexValidator(
    regex=r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$",
    message="Solo se permiten letras y espacios.",
)

# Teléfono: solo números, espacios y el signo +
telefono_validator = RegexValidator(
    regex=r"^[0-9 +]+$",
    message="El teléfono solo puede contener números, espacios y el signo '+'.",
)


# ===========================
#   FUNCIÓN AUXILIAR PASSWORD
# ===========================
def validar_password_segura(password):
    """
    Reglas de complejidad:
    - mínimo 8 caracteres
    - al menos 1 mayúscula
    - al menos 1 minúscula
    - al menos 1 número
    """
    if not password:
        return

    errores = []

    if len(password) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", password):
        errores.append("La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", password):
        errores.append("La contraseña debe contener al menos una letra minúscula.")
    if not re.search(r"[0-9]", password):
        errores.append("La contraseña debe contener al menos un número.")

    if errores:
        raise ValidationError(" ".join(errores))


# ==============
#   REGISTRO
# ==============
class RegistroForm(forms.ModelForm):
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Elige un nombre de usuario",
                "class": "form-control",
            }
        ),
    )

    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "tu@email.com",
                "class": "form-control",
            }
        ),
    )

    first_name = forms.CharField(
        label="Nombres",
        validators=[solo_letras_validator],
        widget=forms.TextInput(
            attrs={
                "placeholder": "Tu nombre",
                "class": "form-control",
                "pattern": r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+",
                "title": "Solo se permiten letras y espacios.",
            }
        ),
    )

    last_name = forms.CharField(
        label="Apellidos",
        validators=[solo_letras_validator],
        widget=forms.TextInput(
            attrs={
                "placeholder": "Tu apellido",
                "class": "form-control",
                "pattern": r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+",
                "title": "Solo se permiten letras y espacios.",
            }
        ),
    )

    telefono = forms.CharField(
        label="Teléfono (opcional)",
        required=False,
        validators=[telefono_validator],
        widget=forms.TextInput(
            attrs={
                "placeholder": "+56 9 1234 5678",
                "class": "form-control",
                "pattern": r"[0-9 +]+",
                "inputmode": "tel",
                "title": "Solo números, espacios y el signo +.",
            }
        ),
    )

    direccion = forms.CharField(
        label="Dirección (opcional)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Calle, número, comuna",
                "rows": 2,
                "class": "form-control",
            }
        ),
    )

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Crea una contraseña segura",
                "class": "form-control",
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirma tu contraseña",
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip()
        if first_name and not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$", first_name):
            raise ValidationError("El nombre solo puede contener letras y espacios.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip()
        if last_name and not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$", last_name):
            raise ValidationError("El apellido solo puede contener letras y espacios.")
        return last_name

    def clean_password2(self):
        p1 = self.cleaned_data.get("password")
        p2 = self.cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            raise ValidationError("Las contraseñas no coinciden.")

        validar_password_segura(p1)
        return p2

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono")
        if telefono and not re.match(r"^[0-9 +]+$", telefono):
            raise ValidationError(
                "El teléfono solo puede contener números, espacios y '+'."
            )
        return telefono

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
            telefono = self.cleaned_data.get("telefono")
            if telefono:
                perfil, _ = Perfil.objects.get_or_create(user=user)
                perfil.telefono = telefono
                perfil.save()
        return user


# ==============
#   LOGIN
# ==============
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "placeholder": "Tu usuario",
                "class": "form-control",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Tu contraseña",
                "class": "form-control",
            }
        ),
    )


# ==============
#   TICKET
# ==============
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["titulo", "descripcion", "prioridad", "foto"]
        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Título de la reparación",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe el problema del PC",
                }
            ),
            "prioridad": forms.Select(attrs={"class": "form-select"}),
            "foto": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


# ==============
#   COMENTARIO
# ==============
class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ["texto"]
        widgets = {
            "texto": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Escribe tu comentario...",
                }
            )
        }


# ==============
#   COMPROBANTE DE PAGO
# ==============
class ComprobantePagoForm(forms.ModelForm):
    class Meta:
        model = ComprobantePago
        fields = ["imagen"]
        labels = {"imagen": "Comprobante (imagen)"}
        widgets = {
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


# ==============
#   FILTROS LISTA
# ==============
class FiltroTicketsForm(forms.Form):
    estado = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=[("", "Todos")] + list(Ticket.ESTADO_CHOICES),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    prioridad = forms.ChoiceField(
        label="Prioridad",
        required=False,
        choices=[("", "Todas")] + list(Ticket.PRIORIDAD_CHOICES),
        widget=forms.Select(attrs={"class": "form-select"}),
    )


# ==============
#   USUARIO (ADMIN EDITA)
# ==============
class UsuarioAdminForm(forms.ModelForm):
    """
    Formulario para que el admin edite datos del usuario
    y asigne el ROL: usuario / técnico / admin.
    """

    ROL_CHOICES = [
        ("usuario", "Usuario"),
        ("tecnico", "Técnico"),
        ("admin", "Administrador"),
    ]

    rol = forms.ChoiceField(
        label="Rol",
        choices=ROL_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        usuario = self.instance

        if usuario and usuario.pk:
            if usuario.is_superuser:
                rol_actual = "admin"
            elif usuario.is_staff:
                rol_actual = "tecnico"
            else:
                rol_actual = "usuario"
            self.fields["rol"].initial = rol_actual

        for field_name in ["username", "first_name", "last_name", "email", "is_active"]:
            if field_name in self.fields:
                self.fields[field_name].disabled = True

    def save(self, commit=True):
        user = super().save(commit=False)
        rol = self.cleaned_data.get("rol")

        if rol == "admin":
            user.is_superuser = True
            user.is_staff = True
        elif rol == "tecnico":
            user.is_superuser = False
            user.is_staff = True
        else:
            user.is_superuser = False
            user.is_staff = False

        if commit:
            user.save()
        return user


# ==============
#   CAMBIO DE PASSWORD (ADMIN)
# ==============
class AdminPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")

        if p1 and p2 and p1 != p2:
            raise ValidationError("Las contraseñas no coinciden.")

        validar_password_segura(p1)
        return cleaned_data


# ==============
#   ASIGNAR CLIENTE A TÉCNICO
# ==============
class AsignacionClienteForm(forms.ModelForm):
    class Meta:
        model = AsignacionCliente
        fields = ["tecnico", "cliente"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tecnico"].queryset = User.objects.filter(is_staff=True)
        self.fields["cliente"].queryset = User.objects.filter(is_staff=False)

        self.fields["tecnico"].label = "Técnico"
        self.fields["cliente"].label = "Cliente"

        self.fields["tecnico"].widget.attrs.update({"class": "form-select"})
        self.fields["cliente"].widget.attrs.update({"class": "form-select"})


# ============================
#   FORMULARIOS DE PERFIL USUARIO
# ============================
class PerfilEditarForm(forms.ModelForm):
    """
    Edita: nombre, apellido, email (User) + teléfono (Perfil).
    """

    first_name = forms.CharField(
        label="Nombre",
        validators=[solo_letras_validator],
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "pattern": r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+",
                "title": "Solo se permiten letras y espacios.",
            }
        ),
    )
    last_name = forms.CharField(
        label="Apellido",
        validators=[solo_letras_validator],
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "pattern": r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+",
                "title": "Solo se permiten letras y espacios.",
            }
        ),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    telefono = forms.CharField(
        label="Teléfono",
        required=False,
        validators=[telefono_validator],
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "pattern": r"[0-9 +]+",
                "inputmode": "tel",
                "title": "Solo números, espacios y el signo +.",
            }
        ),
    )

    class Meta:
        model = Perfil
        fields = ["telefono"]


# ==========================================
#   PERFIL - CAMBIAR CONTRASEÑA
# ==========================================
class PerfilPasswordForm(forms.Form):
    """
    Formulario para que el usuario cambie su propia contraseña.
    """

    old_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Contraseña actual"}
        ),
    )

    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Nueva contraseña"}
        ),
    )

    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Repite la contraseña"}
        ),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data.get("old_password")
        if old and not self.user.check_password(old):
            raise forms.ValidationError("La contraseña actual no es correcta.")
        return old

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        validar_password_segura(p1)
        return cleaned

    def save(self, commit=True):
        new_password = self.cleaned_data["new_password1"]
        self.user.set_password(new_password)
        if commit:
            self.user.save()
        return self.user

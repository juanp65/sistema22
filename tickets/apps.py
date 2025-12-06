from django.apps import AppConfig
import os


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tickets'

    def ready(self):
        """
        Se ejecuta al iniciar Django en Render.
        Crea automáticamente el superusuario admintechfix 
        SOLO si no existe y si la variable CREATE_SUPERUSER_ON_STARTUP=True.
        """
        if os.getenv("CREATE_SUPERUSER_ON_STARTUP") == "True":

            from django.contrib.auth import get_user_model
            User = get_user_model()

            username = "admintechfix"
            email = "admin@techfix.com"
            password = os.getenv("ADMINTECHFIX_PASSWORD", "AdminTechfix2025!")

            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                print("⚡ Superusuario 'admintechfix' creado automáticamente.")
            else:
                print("ℹ El usuario 'admintechfix' ya existe — no se creó uno nuevo.")

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# ======================================================
#  MODELO TICKET (REPARACIONES)
# ======================================================
class Ticket(models.Model):
    PRIORIDAD_CHOICES = [
        ("baja", "Baja"),
        ("media", "Media"),
        ("alta", "Alta"),
    ]

    ESTADO_CHOICES = [
        ("nuevo", "Nuevo"),
        ("en_progreso", "En progreso"),
        ("cerrado", "Cerrado"),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="nuevo",
    )
    foto = models.ImageField(
        upload_to="tickets",
        blank=True,
        null=True,
    )

    creado_por = models.ForeignKey(
        User,
        related_name="tickets_creados",
        on_delete=models.CASCADE,
    )

    tecnico_asignado = models.ForeignKey(
        User,
        related_name="tickets_asignados",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[#{self.id}] {self.titulo}"


# ======================================================
#  COMENTARIOS
# ======================================================
class Comentario(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        related_name="comentarios",
        on_delete=models.CASCADE,
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    respuesta_a = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="respuestas",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"Comentario de {self.usuario} en ticket #{self.ticket_id}"


# ======================================================
#  ASIGNACIÓN CLIENTE ↔ TÉCNICO
# ======================================================
class AsignacionCliente(models.Model):

    tecnico = models.ForeignKey(
        User,
        related_name="clientes_asignados",
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
    )

    cliente = models.ForeignKey(
        User,
        related_name="tecnicos_asignados",
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": False},
    )

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tecnico", "cliente")
        verbose_name = "Asignación de cliente a técnico"
        verbose_name_plural = "Asignaciones de clientes a técnicos"

    def __str__(self):
        return f"{self.cliente.username} → {self.tecnico.username}"


# ======================================================
#  PERFIL DE USUARIO
# ======================================================
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=User)
def crear_o_actualizar_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
    else:
        try:
            instance.perfil.save()
        except Perfil.DoesNotExist:
            Perfil.objects.create(user=instance)


# ======================================================
#  ENVÍOS (SE CREA SOLO PARA TICKETS CERRADOS)
# ======================================================
class Envio(models.Model):
    ESTADO_ENVIO_CHOICES = [
        ("pendiente", "Preparando tu orden"),
        ("despachado", "Envío entregado a la empresa de reparto"),
        ("entregado", "Entregado al cliente"),
    ]

    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name="envio",
    )

    estado_envio = models.CharField(
        max_length=20,
        choices=ESTADO_ENVIO_CHOICES,
        default="pendiente",
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Envío"
        verbose_name_plural = "Envíos"

    def __str__(self):
        return f"Envío ticket #{self.ticket.id} - {self.get_estado_envio_display()}"


# ======================================================
#  COMPROBANTE DE PAGO (TRANSFERENCIA)
# ======================================================
class ComprobantePago(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        related_name="comprobantes",
        on_delete=models.CASCADE,
    )
    imagen = models.ImageField(
        upload_to="comprobantes",
        null=False,
        blank=False,
    )
    subido_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comprobante de pago"
        verbose_name_plural = "Comprobantes de pago"

    def __str__(self):
        return f"Comprobante #{self.id} - Ticket #{self.ticket.id}"

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q

from .forms import (
    RegistroForm,
    LoginForm,
    TicketForm,
    ComentarioForm,
    FiltroTicketsForm,
    UsuarioAdminForm,
    AdminPasswordForm,
    AsignacionClienteForm,
    PerfilEditarForm,
    PerfilPasswordForm,
    ComprobantePagoForm,
)
from .models import Ticket, Comentario, AsignacionCliente, Perfil, Envio, ComprobantePago


# ============================================
# HOME
# ============================================
def home_view(request):
    return render(request, "tickets/home.html")


# ============================================
# DASHBOARD
# ============================================
@login_required
def dashboard_view(request):

    # Usuario normal
    if not request.user.is_staff:
        return render(request, "tickets/dashboard_usuario.html")

    # Técnico (staff no admin)
    if request.user.is_staff and not request.user.is_superuser:
        return redirect("panel_tecnico")

    # Admin
    hoy = timezone.now().date()

    tickets_hoy = Ticket.objects.filter(creado_en__date=hoy).count()
    tickets_en_progreso = Ticket.objects.filter(estado="en_progreso").count()
    tickets_cerrados = Ticket.objects.filter(estado="cerrado").count()
    total_clientes = User.objects.filter(is_staff=False).count()

    tickets_pendientes = Ticket.objects.exclude(estado="cerrado").order_by(
        "-creado_en"
    )[:8]
    tickets_recientes = Ticket.objects.filter(estado="cerrado").order_by(
        "-actualizado_en"
    )[:5]

    contexto = {
        "tickets_hoy": tickets_hoy,
        "tickets_en_progreso": tickets_en_progreso,
        "tickets_cerrados": tickets_cerrados,
        "total_clientes": total_clientes,
        "tickets_pendientes": tickets_pendientes,
        "tickets_recientes": tickets_recientes,
    }

    return render(request, "tickets/dashboard_admin.html", contexto)


# ============================================
# REGISTRO
# ============================================
def registro_view(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("login")
    else:
        form = RegistroForm()

    return render(request, "tickets/registro.html", {"form": form})


# ============================================
# LOGIN
# ============================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            return redirect("dashboard")
    else:
        form = LoginForm(request)

    return render(request, "tickets/login.html", {"form": form})


# ============================================
# LOGOUT
# ============================================
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# ============================================
# CREAR TICKET
# ============================================
@login_required
def crear_ticket_view(request):
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creado_por = request.user
            ticket.save()
            messages.success(request, "Reparación creada correctamente.")
            return redirect("detalle_ticket", ticket_id=ticket.id)
    else:
        form = TicketForm()

    return render(request, "tickets/crear_ticket.html", {"form": form})


# ============================================
# LISTADO TICKETS
# ============================================
@login_required
def lista_tickets_view(request):

    # Admin / técnico
    if request.user.is_staff:
        qs = Ticket.objects.all().order_by("-creado_en")
    else:
        qs = Ticket.objects.filter(creado_por=request.user).order_by("-creado_en")

    # Filtros
    form_filtros = FiltroTicketsForm(request.GET or None)
    if form_filtros.is_valid():
        estado = form_filtros.cleaned_data.get("estado")
        prioridad = form_filtros.cleaned_data.get("prioridad")

        if estado:
            qs = qs.filter(estado=estado)
        if prioridad:
            qs = qs.filter(prioridad=prioridad)

    busqueda = request.GET.get("q", "").strip()
    if busqueda:
        qs = qs.filter(
            Q(id__icontains=busqueda)
            | Q(titulo__icontains=busqueda)
            | Q(creado_por__username__icontains=busqueda)
        )

    return render(
        request,
        "tickets/lista_tickets.html",
        {
            "tickets": qs,
            "form_filtros": form_filtros,
        },
    )


# ============================================
# DETALLE TICKET
# ============================================
@login_required
def detalle_ticket_view(request, ticket_id):

    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Permisos: cliente dueño o staff
    if not request.user.is_staff and ticket.creado_por != request.user:
        messages.error(request, "No tienes permiso.")
        return redirect("lista_tickets")

    if request.method == "POST":

        # -----------------------------------
        # 1) COMENTARIO
        # -----------------------------------
        if "agregar_comentario" in request.POST:
            form = ComentarioForm(request.POST)
            if form.is_valid():
                c = form.save(commit=False)
                c.ticket = ticket
                c.usuario = request.user

                respuesta_id = request.POST.get("respuesta_a")
                if respuesta_id:
                    c.respuesta_a_id = respuesta_id

                c.save()
                messages.success(request, "Comentario agregado.")
            return redirect("detalle_ticket", ticket_id=ticket.id)

        # -----------------------------------
        # 2) CAMBIAR ESTADO (SOLO ADMIN)
        # -----------------------------------
        if "cambiar_estado" in request.POST:
            if request.user.is_superuser:
                nuevo_estado = request.POST.get("estado")

                if nuevo_estado in dict(Ticket.ESTADO_CHOICES):
                    ticket.estado = nuevo_estado
                    ticket.save()

                    # Gestionar Envío
                    if nuevo_estado == "cerrado":
                        Envio.objects.get_or_create(ticket=ticket)
                    else:
                        Envio.objects.filter(ticket=ticket).delete()

                    messages.success(request, "Estado actualizado correctamente.")
                else:
                    messages.error(request, "Estado no válido.")
            return redirect("detalle_ticket", ticket_id=ticket.id)

        # -----------------------------------
        # 3) ASIGNAR TÉCNICO (SOLO ADMIN)
        # -----------------------------------
        if "asignar_tecnico" in request.POST:
            if request.user.is_superuser:
                tec_id = request.POST.get("tecnico_id")
                if tec_id:
                    tecnico = get_object_or_404(User, id=tec_id, is_staff=True)
                    ticket.tecnico_asignado = tecnico
                    ticket.save()

                    # Mantener relación cliente ↔ técnico
                    AsignacionCliente.objects.get_or_create(
                        tecnico=tecnico,
                        cliente=ticket.creado_por,
                    )
                    messages.success(request, "Técnico asignado correctamente.")
                else:
                    ticket.tecnico_asignado = None
                    ticket.save()
                    messages.success(request, "Técnico desasignado.")
            return redirect("detalle_ticket", ticket_id=ticket.id)

        # -----------------------------------
        # 4) SUBIR COMPROBANTE DE PAGO
        # -----------------------------------
        if "subir_comprobante" in request.POST:
            if request.user == ticket.creado_por or request.user.is_staff:
                form = ComprobantePagoForm(request.POST, request.FILES)
                if form.is_valid():
                    comp = form.save(commit=False)
                    comp.ticket = ticket
                    comp.subido_por = request.user
                    comp.save()
                    messages.success(
                        request, "Comprobante de pago subido correctamente."
                    )
                else:
                    messages.error(
                        request, "Hubo un problema al subir el comprobante."
                    )
            else:
                messages.error(
                    request, "No tienes permiso para subir comprobantes en este ticket."
                )
            return redirect("detalle_ticket", ticket_id=ticket.id)

    # --- GET / contexto ---
    comentario_form = ComentarioForm()
    comentarios = Comentario.objects.filter(
        ticket=ticket, respuesta_a__isnull=True
    ).order_by("creado_en")

    envio = Envio.objects.filter(ticket=ticket).first()
    tecnicos = User.objects.filter(is_staff=True)

    comprobante_form = ComprobantePagoForm()
    comprobantes = ticket.comprobantes.all().order_by("-creado_en")

    return render(
        request,
        "tickets/detalle_ticket.html",
        {
            "ticket": ticket,
            "comentarios": comentarios,
            "comentario_form": comentario_form,
            "envio": envio,
            "tecnicos": tecnicos,
            "ESTADO_CHOICES": Ticket.ESTADO_CHOICES,
            "comprobante_form": comprobante_form,
            "comprobantes": comprobantes,
        },
    )


# ============================================
# PANEL TÉCNICO
# ============================================
@login_required
def panel_tecnico_view(request):

    if not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    # ---------------------------------------
    # CAMBIAR ESTADO DESDE PANEL TÉCNICO
    # (ADMIN O TÉCNICO ASIGNADO)
    # ---------------------------------------
    if request.method == "POST":
        ticket_id = request.POST.get("ticket_id")
        nuevo_estado = request.POST.get("estado")

        ticket = get_object_or_404(Ticket, id=ticket_id)

        # Si NO es superuser, validar que el ticket esté asignado a ese técnico
        if not request.user.is_superuser and ticket.tecnico_asignado != request.user:
            messages.error(request, "No puedes modificar esta reparación.")
            return redirect("panel_tecnico")

        if nuevo_estado in dict(Ticket.ESTADO_CHOICES):
            ticket.estado = nuevo_estado
            ticket.save()

            if nuevo_estado == "cerrado":
                Envio.objects.get_or_create(ticket=ticket)
            else:
                Envio.objects.filter(ticket=ticket).delete()

            messages.success(
                request,
                f"Estado de la reparación #{ticket.id} actualizado a '{nuevo_estado}'.",
            )
        else:
            messages.error(request, "Estado no válido.")

        return redirect("panel_tecnico")

    # ---------------------------------------
    # LISTADO DE TICKETS
    # ---------------------------------------
    if request.user.is_superuser:
        tickets = Ticket.objects.all().order_by("estado", "-creado_en")
    else:
        tickets = Ticket.objects.filter(
            tecnico_asignado=request.user
        ).order_by("estado", "-creado_en")

    tecnicos = User.objects.filter(is_staff=True)

    return render(
        request,
        "tickets/panel_tecnico.html",
        {
            "tickets": tickets,
            "tecnicos": tecnicos,
            "ESTADO_CHOICES": Ticket.ESTADO_CHOICES,
        },
    )


# ============================================
# PANEL USUARIOS
# ============================================
@login_required
def usuarios_panel_view(request):

    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    usuarios = User.objects.order_by("id")

    return render(
        request,
        "tickets/usuarios/usuarios_panel.html",
        {
            "usuarios": usuarios,
        },
    )


# ============================================
# DETALLE DE USUARIO
# ============================================
@login_required
def usuario_detalle_view(request, user_id):

    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    usuario = get_object_or_404(User, id=user_id)

    return render(
        request,
        "tickets/usuarios/usuario_detalle.html",
        {
            "usuario_obj": usuario,
        },
    )


# ============================================
# EDITAR USUARIO (SOLO ROL)
# ============================================
@login_required
def usuario_editar_view(request, user_id):

    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    usuario = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UsuarioAdminForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Rol actualizado.")
            return redirect("usuario_detalle", user_id=usuario.id)
    else:
        form = UsuarioAdminForm(instance=usuario)

    return render(
        request,
        "tickets/usuarios/usuario_editar.html",
        {
            "usuario_obj": usuario,
            "form": form,
        },
    )


# ============================================
# ELIMINAR USUARIO
# ============================================
@login_required
def usuario_eliminar_view(request, user_id):

    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    usuario = get_object_or_404(User, id=user_id)

    # Evitar que el administrador se elimine a sí mismo
    if usuario == request.user:
        messages.error(request, "No puedes eliminar tu propio usuario.")
        return redirect("usuario_detalle", user_id=user_id)

    if request.method == "POST":
        usuario.delete()
        messages.success(request, "Usuario eliminado exitosamente.")
        return redirect("usuarios_panel")

    return redirect("usuario_detalle", user_id=user_id)


# ============================================
# PERFIL DEL USUARIO
# ============================================
@login_required
def perfil_view(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    return render(
        request,
        "tickets/perfil.html",
        {
            "usuario": request.user,
            "perfil": perfil,
        },
    )


# ============================================
# EDITAR PERFIL
# ============================================
@login_required
def perfil_editar_view(request):

    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = PerfilEditarForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            request.user.email = form.cleaned_data["email"]
            request.user.save()
            messages.success(request, "Perfil actualizado.")
            return redirect("perfil")
    else:
        form = PerfilEditarForm(
            instance=perfil,
            initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
                "telefono": perfil.telefono,
            },
        )

    return render(request, "tickets/perfil_editar.html", {"form": form})


# ============================================
# CAMBIAR CONTRASEÑA (DEL PROPIO USUARIO)
# ============================================
@login_required
def perfil_password_view(request):

    if request.method == "POST":
        form = PerfilPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contraseña actualizada correctamente.")
            return redirect("perfil")
    else:
        form = PerfilPasswordForm(request.user)

    return render(
        request,
        "tickets/perfil_password.html",
        {
            "form": form,
        },
    )


# ============================================
# ADMINISTRAR ENVÍOS
# ============================================
@login_required
def admin_envios_view(request):

    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    # Asegurar que todos los tickets cerrados tengan un Envio
    tickets_cerrados = Ticket.objects.filter(estado="cerrado")
    for t in tickets_cerrados:
        Envio.objects.get_or_create(ticket=t)

    if request.method == "POST":
        envio_id = request.POST.get("envio_id")
        nuevo_estado = request.POST.get("estado_envio")
        envio = get_object_or_404(Envio, id=envio_id)

        if nuevo_estado in dict(Envio.ESTADO_ENVIO_CHOICES):
            envio.estado_envio = nuevo_estado
            envio.save()
            messages.success(request, "Estado de envío actualizado.")
        else:
            messages.error(request, "Estado de envío no válido.")

        return redirect("admin_envios")

    envios = Envio.objects.all().order_by("-fecha_actualizacion")

    return render(
        request,
        "tickets/admin_envios.html",
        {
            "envios": envios,
            "ESTADO_ENVIO_CHOICES": Envio.ESTADO_ENVIO_CHOICES,
        },
    )


# ============================================
# ASIGNAR CLIENTE A TÉCNICO (ADMIN)
# ============================================
@login_required
def asignar_cliente_a_tecnico_view(request):

    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        form = AsignacionClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente asignado al técnico correctamente.")
            return redirect("panel_tecnico")
    else:
        form = AsignacionClienteForm()

    asignaciones = AsignacionCliente.objects.select_related("tecnico", "cliente")

    return render(
        request,
        "tickets/asignar_cliente.html",
        {
            "form": form,
            "asignaciones": asignaciones,
        },
    )

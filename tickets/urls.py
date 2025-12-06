from django.urls import path
from . import views

urlpatterns = [

    # ===========================
    #        HOME PÚBLICO
    # ===========================
    path("", views.home_view, name="home"),

    # ===========================
    #   AUTENTICACIÓN
    # ===========================
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro/", views.registro_view, name="registro"),

    # ===========================
    #   DASHBOARD SEGÚN ROL
    # ===========================
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # ===========================
    #        REPARACIONES
    # ===========================
    path("tickets/", views.lista_tickets_view, name="lista_tickets"),
    path("tickets/nuevo/", views.crear_ticket_view, name="crear_ticket"),
    path("tickets/<int:ticket_id>/", views.detalle_ticket_view, name="detalle_ticket"),

    # ===========================
    #       PANEL TÉCNICO
    # ===========================
    path("panel-tecnico/", views.panel_tecnico_view, name="panel_tecnico"),

    # ===========================
    #       ADMINISTRAR ENVÍOS
    # ===========================
    path("dashboard/envios/", views.admin_envios_view, name="admin_envios"),

    # ===========================
    #       PANEL DE USUARIOS (ADMIN)
    # ===========================
    path("usuarios/", views.usuarios_panel_view, name="usuarios_panel"),
    path("usuarios/<int:user_id>/", views.usuario_detalle_view, name="usuario_detalle"),
    path("usuarios/<int:user_id>/editar/", views.usuario_editar_view, name="usuario_editar"),

    # NUEVA RUTA → ELIMINAR USUARIO
    path("usuarios/<int:user_id>/eliminar/", views.usuario_eliminar_view, name="usuario_eliminar"),

    # ===========================
    #   ⚠️ ASIGNAR CLIENTE (DESACTIVADO)
    #   Esta vista NO existe en views.py → producía ERROR 500
    # ===========================
    # path("asignar-cliente/", views.asignar_cliente_a_tecnico_view, name="asignar_cliente"),

    # ===========================
    #       PERFIL (USUARIO)
    # ===========================
    path("perfil/", views.perfil_view, name="perfil"),
    path("perfil/editar/", views.perfil_editar_view, name="perfil_editar"),
    path("perfil/password/", views.perfil_password_view, name="perfil_password"),
]

from cit.models import ConfiguracionClinica
from clinicas.models import Clinica


def clinica_context(request):
    """Contexto global para mostrar nombre/eslogan de la clínica activa en layout."""
    default_nombre = "PowerDent"
    default_eslogan = "Gestión clínica"

    context = {
        "clinica_activa": None,
        "clinica_nombre": default_nombre,
        "clinica_eslogan": default_eslogan,
        "clinica_titulo_pestana": f"{default_nombre} | {default_eslogan}",
        "by_powerdent_label": "by PowerDent",
    }

    # 1) Intentar leer clínica activa desde sesión
    session_clinica_id = None
    try:
        session_clinica_id = request.session.get("clinica_id")
    except Exception:
        session_clinica_id = None

    clinica = None

    # 2) Si hay clinica en sesión, usarla
    if session_clinica_id:
        clinica = Clinica.objects.filter(id=session_clinica_id, estado=True).first()

    # 3) Si no, intentar por ConfiguracionClinica activa
    if not clinica:
        try:
            config = ConfiguracionClinica.objects.select_related("sucursal__clinica").filter(estado=True).first()
            if config and config.sucursal_id:
                clinica = config.sucursal.clinica
        except Exception:
            clinica = None

    # 4) NO hay fallback a primera clínica por seguridad multi-tenant
    # Si el usuario no tiene clínica seleccionada, el middleware lo redirigirá al selector

    if clinica:
        nombre = clinica.nombre or default_nombre
        eslogan = clinica.eslogan or default_eslogan
        titulo = clinica.titulo_pestana or f"{nombre} | {eslogan}"

        context.update({
            "clinica_activa": clinica,
            "clinica_nombre": nombre,
            "clinica_eslogan": eslogan,
            "clinica_titulo_pestana": titulo,
        })

    return context


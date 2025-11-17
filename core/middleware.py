import logging
from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger("core.errors")


class GlobalExceptionMiddleware:
    """
    Captura excepciones no manejadas.

    - En DEBUG: re-lanza (obtienes el traceback normal de Django)
    - En producción: log + JSON para API o HTML amigable para vistas normales
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            # En desarrollo queremos ver el error completo
            if settings.DEBUG:
                raise

            logger.exception("Unhandled exception in path=%s", request.path)

            wants_json = (
                request.headers.get("x-requested-with") == "XMLHttpRequest"
                or request.path.startswith("/api/")
            )
            if wants_json:
                return JsonResponse(
                    {"detail": "Ha ocurrido un error inesperado. Intenta nuevamente."},
                    status=500,
                )

            # HTML → usamos la vista global_error_500
            from core.views import global_error_500
            return global_error_500(request)




class SecurityHeadersMiddleware:
    """
    Agrega headers de seguridad a TODAS las respuestas HTTP:

    - Strict-Transport-Security (solo producción + HTTPS)
    - Content-Security-Policy (desde settings.CSP_DEFAULT_POLICY)
    - Permissions-Policy (desde settings.PERMISSIONS_POLICY)
    - X-Content-Type-Options, Referrer-Policy de regalo
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # HSTS: solo en producción y sobre HTTPS
        if not settings.DEBUG and request.is_secure():
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )

        # CSP y Permissions Policy desde settings
        csp = getattr(settings, "CSP_DEFAULT_POLICY", None)
        if csp:
            response.headers.setdefault("Content-Security-Policy", csp)

        pp = getattr(settings, "PERMISSIONS_POLICY", None)
        if pp:
            response.headers.setdefault("Permissions-Policy", pp)

        # Extras recomendados
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

        return response

import logging

from django.db import DatabaseError, connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    return Response(
        {
            "project": "FreshBasket",
            "status": "available",
            "endpoints": {
                "health": "/api/health/",
                "accounts": "/api/accounts/",
                "catalog": "/api/catalog/",
                "cart": "/api/cart/",
                "wishlist": "/api/wishlist/",
                "orders": "/api/orders/",
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    try:
        connection.ensure_connection()
        database_status = "connected" if connection.is_usable() else "unavailable"
    except DatabaseError:
        logger.exception("Database health check failed.")
        database_status = "unavailable"

    response_status = (
        status.HTTP_200_OK
        if database_status == "connected"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return Response(
        {
            "backend_status": "ok",
            "database_status": database_status,
            "project": "FreshBasket",
        },
        status=response_status,
    )

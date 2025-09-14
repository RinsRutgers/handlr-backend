"""
Health check views for monitoring the application status.
"""
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import os


def health_check(request):
    """
    Simple health check endpoint that verifies:
    - Database connectivity
    - Basic application status
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        status = {
            "status": "healthy",
            "database": "connected",
            "debug": settings.DEBUG,
            "version": "1.0.0"
        }
        
        return JsonResponse(status, status=200)
    
    except Exception as e:
        status = {
            "status": "unhealthy",
            "error": str(e),
            "database": "disconnected"
        }
        
        return JsonResponse(status, status=500)


def ready_check(request):
    """
    Readiness check for Kubernetes/container orchestration.
    """
    try:
        # More comprehensive checks can be added here
        # For example, checking if all required services are available
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        return JsonResponse({"status": "ready"}, status=200)
    
    except Exception as e:
        return JsonResponse({
            "status": "not ready",
            "error": str(e)
        }, status=503)

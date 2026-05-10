from .models import Service

def get_active_services():
    return Service.objects.filter(is_active=True)
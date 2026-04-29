
from django.conf import settings

def is_admin(user):

    if not user or not user.is_authenticated:
        return False
    
    is_admin_field = getattr(user, 'is_admin', False)
    is_staff_field = getattr(user, 'is_staff', False)
    is_superuser_field = getattr(user, 'is_superuser', False) 
    
    return any([
        is_admin_field,
        is_staff_field,
        is_superuser_field
    ])
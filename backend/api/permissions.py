import uuid
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from core.models import Tenant

class HasTenantPermission(permissions.BasePermission):
    """
    Enforces tenant isolation by requiring a valid X-Tenant-ID header containing
    a Tenant UUID. Attaches the Tenant object to the request.
    """
    def has_permission(self, request, view):
        tenant_id_str = request.headers.get('X-Tenant-ID')
        if not tenant_id_str:
            raise PermissionDenied("X-Tenant-ID header is required.")

        try:
            tenant_uuid = uuid.UUID(tenant_id_str)
        except ValueError:
            raise ValidationError("X-Tenant-ID header must be a valid UUID.")

        try:
            tenant = Tenant.objects.get(pk=tenant_uuid)
        except Tenant.DoesNotExist:
            raise PermissionDenied("Tenant matching the provided UUID does not exist.")

        # Attach tenant object to request for convenient downstream filtering
        request.tenant = tenant
        return True


class IsRecordUnlocked(permissions.BasePermission):
    """
    Blocks modifying (editing, locking, unlocking, approving, rejecting) 
    an EmissionRecord if it is locked for audit.
    """
    def has_object_permission(self, request, view, obj):
        # Read-only actions are always allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # If locked, block modification requests
        if obj.locked:
            # Allow changes only if the view explicitly allows unlocking 
            # (which we check by action name in the view)
            if view.action == 'unlock':
                return True
            raise PermissionDenied("This record is locked for audit and cannot be modified.")

        return True

from rest_framework import permissions


class ConsumerPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if super(ConsumerPermission, self).has_permission(request, view) and request.user.consumer is not None:
            return True


class VendorPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if super(VendorPermission, self).has_permission(request, view) and request.user.vendor is not None:
            return True


class EmployeePermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if super(EmployeePermission, self).has_permission(request, view) and request.user.employee is not None:
            return True

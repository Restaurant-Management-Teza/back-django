# permissions.py
from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='MANAGER').exists()


class IsWaiter(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='WAITER').exists()
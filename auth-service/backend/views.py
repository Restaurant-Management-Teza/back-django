from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import DefaultUser
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    Provides all CRUD operations for DefaultUser.
    """
    queryset = DefaultUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
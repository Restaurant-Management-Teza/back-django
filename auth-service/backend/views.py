from django.contrib.auth.models import User
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token

from .models import WaiterProfile
from .serializers import UserSerializer, UserFullSerializer, ZoneUpdateSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "User created successfully",
                "token": token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

class CustomLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # 1) Let DRF verify the credentials first
        response = super().post(request, *args, **kwargs)

        token = Token.objects.get(key=response.data["token"])
        user  = token.user

        groups      = user.groups.values_list("name", flat=True)
        user_group  = groups[0] if groups else None

        zone = None
        if user_group == "WAITER":
            zone = getattr(getattr(user, "waiter_profile", None), "zone", None)

        # 5) Build custom payload
        return Response({
            "token":      token.key,
            "username":   user.username,
            "user_group": user_group,   # "WAITER", "MANAGER", ...
            "zone":       zone,        # int or null
            "user_id": user.id,
        })

class UserFullList(generics.ListAPIView):
    """
    GET /v1/api/users-full/   → list with groups and zone
    """
    permission_classes = [AllowAny]

    queryset = (
        User.objects
            .all()
            .prefetch_related("groups", "waiter_profile")  # one DB hit
    )
    serializer_class  = UserFullSerializer


class UserZoneUpdate(generics.GenericAPIView):
    """
    PUT /v1/api/users/<id>/zone/   { "zone": 4 }
    – Only allowed for WAITERs.
    """
    permission_classes = [AllowAny]
    serializer_class   = ZoneUpdateSerializer
    queryset = User.objects.select_related("waiter_profile")

    def put(self, request, pk):
        user = self.get_object()

        # ensure the user is in WAITER group
        if not user.groups.filter(name="WAITER").exists():
            return Response(
                {"detail": "User is not a waiter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # validate payload
        zone_serializer = self.get_serializer(data=request.data)
        zone_serializer.is_valid(raise_exception=True)
        zone_value = zone_serializer.validated_data["zone"]

        # update / create profile
        profile, _ = WaiterProfile.objects.get_or_create(user=user)
        profile.zone = zone_value
        profile.save()

        user.refresh_from_db()  # <- add this line

        return Response(UserFullSerializer(user).data, status=status.HTTP_200_OK)

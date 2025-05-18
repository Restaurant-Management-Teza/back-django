# serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers

from backend.models import WaiterProfile


class UserSerializer(serializers.ModelSerializer):
    user_type = serializers.ChoiceField(choices=["WAITER", "MANAGER", "CUSTOMER"], write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'user_type']
        extra_kwargs = {'password': {'write_only': True}}


    def create(self, validated_data):
        user_type = validated_data.pop("user_type")
        raw_password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(raw_password)
        user.save()

        # assign group
        from django.contrib.auth.models import Group
        group, _ = Group.objects.get_or_create(name=user_type.upper())
        user.groups.add(group)

        # create waiter profile if needed
        if group.name == "WAITER":
            WaiterProfile.objects.get_or_create(user=user)

        return user


class UserFullSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(   # → ["WAITER", "MANAGER"]
        slug_field="name", read_only=True, many=True
    )
    zone   = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ["id", "username", "email", "groups", "zone"]

    def get_zone(self, obj):
        """
        Returns zone int if the user is a waiter and has a profile, else None.
        """
        return getattr(getattr(obj, "waiter_profile", None), "zone", None)


class ZoneUpdateSerializer(serializers.Serializer):
    zone = serializers.IntegerField(min_value=1, allow_null=True)
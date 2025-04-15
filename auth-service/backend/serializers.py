from rest_framework import serializers
from .models import DefaultUser, UserType

class UserSerializer(serializers.ModelSerializer):
    """
    Serializes the DefaultUser model for CRUD operations.
    By default, password here is plain text. If you want to hash it,
    do so in create/update or in your model manager.
    """
    class Meta:
        model = DefaultUser
        fields = [
            'id',
            'username',
            'email',
            'password',
            'full_name',
            'user_type',
            'is_active',
            'is_staff',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        """
        Optionally hash the password here or rely on model manager.
        """
        password = validated_data.pop('password', None)
        instance = super().create(validated_data)
        if password:
            instance.password = password  # or hash it
            instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.password = password  # or hash it
            instance.save()
        return instance
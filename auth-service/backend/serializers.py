# serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    user_type = serializers.ChoiceField(choices=["WAITER", "MANAGER", "CUSTOMER"], write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'user_type']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Assign to group
        from django.contrib.auth.models import Group
        group, _ = Group.objects.get_or_create(name=user_type.upper())
        user.groups.add(group)

        return user
# serializers.py
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    Table, Session, MenuItem, Order,
    CustomerRequest, OrderItem
)

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    table = TableSerializer(read_only=True)
    table_id = serializers.PrimaryKeyRelatedField(
        queryset=Table.objects.all(),
        source='table',
        write_only=True
    )

    class Meta:
        model = Session
        fields = ['id', 'table', 'table_id', 'created_at', 'is_active']


class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='menu_item.name', read_only=True)
    price = serializers.DecimalField(source='menu_item.price', max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'quantity', 'name', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    session_id = serializers.PrimaryKeyRelatedField(
        queryset=Session.objects.all(),
        source='session',
    )

    class Meta:
        model = Order
        fields = ['id', 'session_id', 'is_approved', 'is_completed', 'created_at', 'items']


class CustomerRequestSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(write_only=True)
    tabel_id = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRequest
        fields = ['id', 'order_id', 'request_type', 'note', 'is_handled', 'created_at', 'tabel_id']

    def get_tabel_id(self, obj):
        return obj.order.session.table.id if obj.order and obj.order.session and obj.order.session.table else None

    def validate_order_id(self, value):
        try:
            return Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise ValidationError("Order with this ID does not exist.")

    def create(self, validated_data):
        order = validated_data.pop('order_id')
        return CustomerRequest.objects.create(order=order, **validated_data)


class SessionInitRequestSerializer(serializers.Serializer):
    table_id = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all())
    note = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        table = validated_data['table_id']
        note = validated_data.get('note', '')

        # Create session
        session = Session.objects.create(table=table)

        # Create initial order
        order = Order.objects.create(session=session)

        # Create initial customer request
        CustomerRequest.objects.create(
            order=order,
            request_type='initial',
            note=note
        )

        return {
            'session_id': session.id,
            'order_id': order.id
        }
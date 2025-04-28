# views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    Table, Session, MenuItem, Order,
    CustomerRequest, OrderItem, RequestType
)
from .serializers import (
    TableSerializer, SessionSerializer, MenuItemSerializer,
    OrderSerializer, CustomerRequestSerializer, OrderItemSerializer, SessionInitRequestSerializer
)
from rest_framework.permissions import AllowAny

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'ingredients']
    ordering_fields = ['price', 'created_at', 'name']


class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderItemsByOrderAPI(APIView):
    ordering_fields = ['price', 'quantity', 'name']
    ordering = ['added_at']
    def get(self, request, order_id):
        get_object_or_404(Order, id=order_id)
        items = OrderItem.objects.filter(order_id=order_id)
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def perform_create(self, serializer):
        # If order ID is expected to come from somewhere else (e.g., cookie or session), do this:
        # order_id = self.request.COOKIES.get('order_id')
        # order = get_object_or_404(Order, pk=order_id)

        # Or just make sure it’s passed in validated_data
        serializer.save()


class CustomerRequestViewSet(viewsets.ModelViewSet):
    queryset = CustomerRequest.objects.all()
    serializer_class = CustomerRequestSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        channel_layer = get_channel_layer()

        # Prepare a dict representing the entire CustomerRequest
        cr_data = {
            "id": instance.id,
            "order_id": instance.order.id,
            "request_type": instance.request_type,
            "note": instance.note,
            "is_handled": instance.is_handled,
            "created_at": str(instance.created_at),
        }

        async_to_sync(channel_layer.group_send)(
            "request_watchers",
            {
                "type": "request_broadcast",
                "request_id": instance.id,
                "request_type": instance.request_type,
                "note": instance.note or "",
                "order_id": instance.order.id,
                "customer_request": cr_data,
                "table_id": instance.order.session.table.id if instance.order else None,
            }
        )

class CreateSessionWithInitialRequest(APIView):
    serializer_class = SessionInitRequestSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        session = Session.objects.filter(id=session_id).first()

        if session_id and session and session.is_active:
            order = session.orders.first()
            return Response({
                "message": "Session already exists",
                "session_id": str(session.id),
                "order_id": order.id if order else None
            }, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()

            response = Response({
                "message": "New session and initial request created",
                "session_id": str(result["session_id"]),
                "order_id": result["order_id"]
            }, status=status.HTTP_201_CREATED)

            response.set_cookie(
                key='session_id',
                value=str(result["session_id"]),
                httponly=True,
                samesite='Lax',
                secure=False
            )
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HandleCustomerRequestView(APIView):
    def post(self, request, request_id):
        customer_request = get_object_or_404(CustomerRequest, id=request_id)

        if customer_request.is_handled:
            return Response({"message": "Request already handled."}, status=status.HTTP_200_OK)

        customer_request.is_handled = True
        customer_request.save()

        if customer_request.request_type == RequestType.PAYMENT:
            order = customer_request.order
            session = order.session

            order.is_completed = True
            order.save()

            session.is_active = False
            session.save()

        return Response({"message": f"Request {request_id} marked as handled."}, status=status.HTTP_200_OK)


class CreateOrderItemByTableAPI(APIView):
    def post(self, request, table_id):
        menu_item_id = request.data.get('menu_item_id')
        quantity = request.data.get('quantity', 1)

        table = get_object_or_404(Table, id=table_id)

        session = table.sessions.filter(is_active=True).first()
        if not session:
            return Response({"detail": "No active session for this table."}, status=status.HTTP_400_BAD_REQUEST)

        order = session.orders.filter(is_completed=False).first()
        if not order:
            order = Order.objects.create(session=session, is_approved=True)

        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        order_item = OrderItem.objects.create(order=order, menu_item=menu_item, quantity=quantity)

        serializer = OrderItemSerializer(order_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


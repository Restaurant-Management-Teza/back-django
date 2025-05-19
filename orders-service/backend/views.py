# views.py
import math                         # ← add this
from django.utils import timezone   # good habit for tz-aware “now”
import math
from rest_framework import viewsets, filters, status
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    Table, Session, MenuItem, Order,
    CustomerRequest, OrderItem, RequestType, Zone, KitchenEvents
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

class GetOrderByTableIdAPI(APIView):
    def get(self, request, table_id):
        table = get_object_or_404(Table, id=table_id)

        # Get active session
        session = table.sessions.filter(is_active=True).first()
        if not session:
            return Response({"detail": "No active session found for this table."}, status=status.HTTP_404_NOT_FOUND)

        # Get first active (not completed) order
        order = session.orders.filter(is_completed=False).first()
        if not order:
            return Response({"detail": "No active order found for this table."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetOrdersByZoneAPI(APIView):
    """
    GET /v1/api/zones/<zone_id>/orders/

    • Looks up the zone.
    • Finds every *unfinished* order that belongs to a table in that zone
      (session → table → zone).
    • Returns a list (could be empty) serialized with OrderSerializer.
    """
    def get(self, request, zone_id):
        # 1️⃣  does the zone exist?
        zone = get_object_or_404(Zone, id=zone_id)

        # 2️⃣  all open orders inside this zone
        open_orders = (
            Order.objects
                 .filter(is_completed=False,
                         session__table__zone=zone)   # session → table → zone
                 .select_related('session', 'session__table')  # SQL efficiency
                 .prefetch_related('items', 'items__menu_item')
        )

        if not open_orders.exists():
            return Response(
                {"detail": "No active orders found in this zone."},
                status=status.HTTP_204_NO_CONTENT,        # 204 = empty but ok
            )

        serializer = OrderSerializer(open_orders, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        order_item = serializer.save()

        from backend.utils.eta import simple_eta

        eta = simple_eta(order_item.menu_item)

        KitchenEvents.objects.create(
            order_item   = order_item,
            eta_finish_at = eta,
        )


class CustomerRequestViewSet(viewsets.ModelViewSet):
    queryset = CustomerRequest.objects.all()
    serializer_class = CustomerRequestSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        channel_layer = get_channel_layer()

        # ─── determine zone ───────────────────────────────────────────
        table   = instance.order.session.table
        zone_obj = getattr(table, "zone", None)           # FK - or - None
        zone_id  = zone_obj.id if zone_obj else getattr(table, "zone_id", None)
        # ──────────────────────────────────────────────────────────────

        # ─── build one payload to reuse ───────────────────────────────
        payload = {
            "type":            "request_broadcast",
            "request_id":      instance.id,
            "request_type":    instance.request_type,
            "note":            instance.note or "",
            "order_id":        instance.order.id,
            "table_id":        table.id,
            "zone_id":         zone_id,
            "customer_request": {
                "id":           instance.id,
                "order_id":     instance.order.id,
                "request_type": instance.request_type,
                "note":         instance.note,
                "is_handled":   instance.is_handled,
                "created_at":   instance.created_at.isoformat(),
            },
        }
        # ──────────────────────────────────────────────────────────────

        # ▶ 1) zone-specific broadcast (waiters)
        if zone_id is not None:
            async_to_sync(channel_layer.group_send)(f"zone_{zone_id}", payload)

        # ▶ 2) global broadcast (managers)
        async_to_sync(channel_layer.group_send)("request_watchers", payload)

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

        from backend.utils.eta import simple_eta

        eta = simple_eta(order_item.menu_item)

        KitchenEvents.objects.create(
            order_item=order_item,
            eta_finish_at=eta,
        )

        serializer = OrderItemSerializer(order_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrderETAAPIView(APIView):
    """
    GET /v1/api/orders/{order_id}/eta/  ->  {"eta_minutes": 17}
    """
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        # collect all eta datetimes for dishes in this order
        evts = order.items.values_list("kitchen_events__eta_finish_at", flat=True)
        evts = [e for e in evts if e]          # drop NULLs / None

        if not evts:
            return Response({"eta_minutes": None})

        eta_dt  = max(evts)                    # longest dish drives the order
        minutes = math.ceil((eta_dt - timezone.now()).total_seconds() / 60)

        return Response({"eta_minutes": max(0, minutes)})


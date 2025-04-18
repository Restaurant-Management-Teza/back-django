from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TableViewSet, SessionViewSet, MenuItemViewSet,
    OrderViewSet, CustomerRequestViewSet, OrderItemViewSet, CreateSessionWithInitialRequest, HandleCustomerRequestView,
    OrderItemsByOrderAPI
)

router = DefaultRouter()
router.register(r'tables', TableViewSet)
router.register(r'sessions', SessionViewSet)
router.register(r'menu-items', MenuItemViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'requests', CustomerRequestViewSet)



urlpatterns = [
    path('', include(router.urls)),
    path('create-session/', CreateSessionWithInitialRequest.as_view(), name='create-session'),
    path('handle-request/<int:request_id>/', HandleCustomerRequestView.as_view(), name='handle-customer-request'),
    path('order-items-by-order/<int:order_id>/', OrderItemsByOrderAPI.as_view(), name='orderitems-by-order'),
]
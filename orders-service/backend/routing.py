from django.urls import re_path
from .consumers import RequestMonitorConsumer

websocket_urlpatterns = [
    re_path(r'^ws/requests/$', RequestMonitorConsumer.as_asgi()),
]
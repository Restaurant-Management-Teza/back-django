from django.urls import re_path
from .consumers import RequestMonitorConsumer, ZoneRequestConsumer

websocket_urlpatterns = [
    re_path(r'^ws/requests/?$', RequestMonitorConsumer.as_asgi()),
    re_path(r"ws/zones/?$", ZoneRequestConsumer.as_asgi()),  # ← NEW

]
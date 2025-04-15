import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import backend.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# Traditional Django HTTP
django_asgi_app = get_asgi_application()

# Our Channels config
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # for normal HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(
            backend.routing.websocket_urlpatterns
        )
    ),
})
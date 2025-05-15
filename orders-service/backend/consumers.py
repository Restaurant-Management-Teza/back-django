import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer

class RequestMonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("request_watchers", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("request_watchers", self.channel_name)

    # This method is called when you do `type="request_broadcast"`
    async def request_broadcast(self, event):
        """
        event might look like:
        {
          "type": "request_broadcast",
          "request_id": 42,
          "request_type": "menu_item",
          "note": "Some note",
          "order_id": 10,
          "customer_request": {
            "id": 42,
            "order_id": 10,
            "request_type": "menu_item",
            "note": "Some note",
            "is_handled": false,
            "created_at": "2025-04-16 14:25:00"
          }
        }
        """
        data = {
            "request_id": event.get("request_id"),
            "request_type": event.get("request_type"),
            "note": event.get("note", ""),
            "order_id": event.get("order_id"),
            "customer_request": event.get("customer_request", {}),
            "table_id": event.get("table_id"),
        }

        # Send JSON back to the client
        await self.send(text_data=json.dumps(data))

class ZoneRequestConsumer(AsyncWebsocketConsumer):
    """
    Waiter endpoint
    ───────────────
    • Client must connect with ?zone_id=<id>
    • Joins group 'zone_<id>'
    • Will reject the socket if zone_id is missing.
    """

    async def connect(self):
        qs = parse_qs(self.scope["query_string"].decode())
        self.zone_id = qs.get("zone_id", [None])[0]

        if not self.zone_id:
            # no zone_id provided → reject connection
            await self.close()
            return

        self.group_name = f"zone_{self.zone_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Handler for messages coming from group_send
    async def request_broadcast(self, event):
        # Optionally, you could strip fields here before sending
        await self.send(text_data=json.dumps(event))
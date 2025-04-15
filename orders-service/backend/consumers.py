import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RequestMonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join a group so we can broadcast to all watchers
        await self.channel_layer.group_add("request_watchers", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard("request_watchers", self.channel_name)

    # We can ignore receive() or handle it if we want client->server
    async def receive(self, text_data=None, bytes_data=None):
        pass

    # We'll broadcast new events with "type": "request_broadcast"
    async def request_broadcast(self, event):
        # event might look like: { "type": "request_broadcast", "request_id": 42, "msg": "..." }
        await self.send(text_data=json.dumps({
            "request_id": event.get("request_id"),
            "request_type": event.get("request_type"),
            "note": event.get("note", "")
        }))
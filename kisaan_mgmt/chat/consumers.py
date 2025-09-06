import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth.models import User
from .models import ChatRoom, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chatroom_id = self.scope['url_route']['kwargs']['chatroom_id']
        self.room_group_name = f'chat_{self.chatroom_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        is_bid = data.get('is_bid', False)
        bid_amount = data.get('bid_amount')
        bid_quantity = data.get('bid_quantity')

        user = self.scope["user"]
        chatroom = await database_sync_to_async(ChatRoom.objects.get)(id=self.chatroom_id)

        # Save message to DB
        msg_obj = await database_sync_to_async(Message.objects.create)(
            chatroom=chatroom,
            sender=user,
            text=message,
            is_bid=is_bid,
            bid_amount=bid_amount if is_bid else None,
            bid_quantity=bid_quantity if is_bid else None,
            bid_status='pending' if is_bid else None
        )

        timestamp = timezone.localtime(msg_obj.timestamp).strftime("%b %d, %Y %H:%M")

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_username': user.username,
                'is_bid': is_bid,
                'bid_amount': bid_amount,
                'bid_quantity': bid_quantity,
                'bid_status': msg_obj.bid_status,
                'timestamp': timestamp
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

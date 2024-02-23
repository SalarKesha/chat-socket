from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import Message, GroupChat


class ChatConsumer(AsyncJsonWebsocketConsumer):
    group_users = dict()

    async def connect(self):
        self.user = self.scope['user']
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.chat_room_id = f"chat_{self.chat_id}"
        self.message_types = {'join': 'join', 'leave': 'leave', 'delete': 'delete', 'msg': 'msg'}
        if self.user.is_authenticated:
            await self.channel_layer.group_add(self.chat_room_id, self.channel_name)
            await self.accept()
            await self.channel_layer.group_send(self.chat_room_id,
                                                {'type': 'chat_message', 'text': f'{self.user} joined the chat',
                                                 'message_type': self.message_types['join']})
            # if result := self.group_users.get(self.chat_room_id, None):
            #     if self.user not in result:
            #         self.group_users[self.chat_room_id].append(self.user)
            #         print("=========")
            #         print(self.group_users)
            #         print("=========")
            # else:
            #     self.group_users[self.chat_room_id] = [self.user]
            #     print("=========")
            #     print(self.group_users)
            #     print("=========")
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(self.chat_room_id,
                                            {'type': 'chat_message', 'text': f'{self.user} leaved the chat',
                                             'message_type': self.message_types['leave']})
        await self.channel_layer.group_discard(self.chat_room_id, self.channel_name)

    async def receive_json(self, content, **kwargs):
        await self.save_message(text=content.get('text'), user=self.user)
        await self.channel_layer.group_send(self.chat_room_id,
                                            {'type': 'chat_message', 'text': content.get('text', None),
                                             'sender': self.user.username, 'message_type': self.message_types['msg']})

    async def chat_message(self, event):
        # channel_names = await self.channel_layer.get_group_channels(self.chat_room_id)
        # print(self.group_users)
        if event.get('sender', False):
            await self.send_json(
                {'text': event.get('text'), 'sender': event['sender'], 'message_type': event.get('message_type')},
                close=False)
        else:
            await self.send_json(
                {'text': event.get('text'), 'message_type': event.get('message_type')},
                close=False)

    @database_sync_to_async
    def save_message(self, user, text):
        chat = GroupChat.objects.get(unique_code=self.chat_id)
        return Message.objects.create(chat=chat, sender=user, text=text)

import json
from datetime import datetime

from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from django.contrib.auth.models import User
from django.db.models import Q

from video_chat.models import VideoChat

VC_CONTACTING, VC_NOT_AVAILABLE, VC_ACCEPTED, VC_REJECTED, VC_BUSY, VC_PROCESSING, VC_ENDED = 0, 1, 2, 3, 4, 5, 6


class VideoChatConsumer(AsyncConsumer):
    async def websocket_connect(self):
        self.user = self.scope['user']
        self.user_room_id = f"videochat_{self.user.id}"
        await self.channel_layer.group_add(self.user_room_id, self.channel_name)
        await self.send({
            'type': 'websocket.accept'
        })

    async def websocket_disconnect(self, event):
        video_chat_id = self.scope['session'].get('video_chat_id', None)
        video_chat = await self.change_video_chat_status(video_chat_id, VC_ENDED)
        if video_chat:
            await self.change_video_chat_datetime(video_chat_id, False)
            await self.channel_layer.group_send(
                f"videochat_{video_chat.caller.id}",
                {
                    'type': 'chat_message',
                    'message': json.dumps({'type': 'offerResult', 'status': VC_ENDED, 'video_chat_id': video_chat.id})
                }
            )
            await self.channel_layer.group_send(
                f"videochat_{video_chat.callee.id}",
                {
                    'type': 'chat_message',
                    'message': json.dumps({'type': 'offerResult', 'status': VC_ENDED, 'video_chat_id': video_chat.id})
                }
            )
        await self.channel_layer.group_discard(self.user_room_id, self.channel_name)
        raise StopConsumer()

    async def websocket_receive(self, event):
        text_data = event.get('text', None)
        bytes_data = event.get('bytes', None)
        if text_data:
            text_data_json = json.loads(text_data)
            message_type = text_data_json['type']
            if message_type == 'createOffer':
                callee_username = text_data_json['username']
                status, video_chat_id = await self.create_video_chat(callee_username)
                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({'type': 'offerResult', 'status': status, 'video_chat_id': video_chat_id})
                })
                if status == VC_CONTACTING:
                    video_chat = await self.get_video_chat(video_chat_id)
                    await self.channel_layer.group_send(
                        f"videochat_{video_chat.callee.id}",
                        {
                            'type': 'chat_message',
                            'message': json.dumps({'type': 'offer', 'username': self.user.username}),
                            'video_chat_id': video_chat_id
                        }
                    )
                else:
                    pass
            elif message_type == "cancelOffer":
                video_chat_id = text_data_json['video_chat_id']
                video_chat = await self.get_video_chat(video_chat_id)
                self.scope['session']['video_chat_id'] = None
                self.scope['session'].save()
                if video_chat.status != VC_ACCEPTED or video_chat.status != VC_REJECTED:
                    await self.change_video_chat_status(video_chat_id, VC_NOT_AVAILABLE)
                    await self.send({
                        'type': 'websocket.send',
                        'text': json.dumps(
                            {'type': 'offerResult', 'status': VC_NOT_AVAILABLE, 'video_chat_id': video_chat.id})
                    })
                    await self.channel_layer.group_send(
                        f"videochat_{video_chat.callee.id}",
                        {
                            'type': 'chat_message',
                            'message': json.dumps({'type': 'offerFinished'})
                        }
                    )
            elif message_type == "acceptOffer":
                video_chat_id = text_data_json['video_chat_id']
                video_chat = await self.change_video_chat_status(video_chat_id, VC_PROCESSING)
                await self.change_video_chat_datetime(video_chat_id, True)
                await self.channel_layer.group_send(
                    f"videochat_{video_chat_id}",
                    {
                        'type': 'chat_message',
                        'message': json.dumps(
                            {'type': 'offerResult', 'status': VC_ACCEPTED, 'video_chat_id': video_chat.id})
                    }
                )
            elif message_type == "rejectOffer":
                video_chat_id = text_data_json['video_chat_id']
                video_chat = await self.change_video_chat_status(video_chat_id, VC_REJECTED)
                self.scope['session']['video_chat_id'] = None
                self.scope['session'].save()
                await self.channel_layer.group_send(
                    f"videochat_{video_chat.caller.id}",
                    {
                        'type': 'chat'
                    }
                )
            elif message_type == "hangUp":
                video_chat_id = text_data_json['video_chat_id']
                video_chat = await self.change_video_chat_status(video_chat_id, VC_ENDED)
                await self.change_video_chat_datetime(video_chat_id, False)
                self.scope['session']['video_chat_id'] = None
                self.scope['session'].save()
                await self.channel_layer.group_add(
                    f"videochat_{video_chat.caller.id}",
                    {
                        'type': 'chat_message',
                        'message': json.dumps({'type': 'offerResult', 'status': VC_REJECTED, 'video_chat_id': video_chat.id})
                    }
                )
                await self.channel_layer.group_add(
                    f"videochat_{video_chat.callee.id}",
                    {
                        'type': 'chat_message',
                        'message': json.dumps(
                            {'type': 'offerResult', 'status': VC_REJECTED, 'video_chat_id': video_chat.id})
                    }
                )
                await self.channel_layer.group_add(
                    f"videochat_{video_chat.callee.id}",
                    {
                        'type': 'chat_message',
                        'message': json.dumps(
                            {'type': 'finished'})
                    }
                )
            elif message_type == "callerDate":
                video_chat_id = text_data_json['video_chat_id']
                video_chat = await self.get_video_chat(video_chat_id)
                await self.channel_layer.group_send(
                    f"vidoechat_{video_chat.callee.id}",
                    {
                        'type': 'chat_message',
                        'message': text_data
                    }
                )
            elif message_type == "calleeDate":
                video_chat_id = text_data_json['video_chat_id']
                video_chat = await self.get_video_chat(video_chat_id)
                await self.channel_layer.group_send(
                    f"vidoechat_{video_chat.caller.id}",
                    {
                        'type': 'chat_message',
                        'message': text_data
                    }
                )

    @database_sync_to_async
    def get_video_chat(self, id):
        try:
            video_chat = VideoChat.objects.get(id=id)
            return video_chat
        except VideoChat.DoesNotExist:
            return None

    @database_sync_to_async
    def create_video_chat(self, callee_username):
        try:
            callee = User.objects.get(username=callee_username)
        except User.DoesNotExist:
            return 404, None
        if VideoChat.objects.filter(Q(caller=callee) | Q(callee=callee), status=VC_PROCESSING).count() > 0:
            return VC_BUSY, None
        video_chat = VideoChat.objects.create(caller=self.user, callee=callee)
        self.scope['session']['video_chat_id'] = video_chat.id
        self.scope['session'].save()
        return VC_CONTACTING, video_chat.id

    @database_sync_to_async
    def change_video_chat_status(self, id, status):
        try:
            video_chat = VideoChat.objects.get(id=id)
            video_chat.status = status
            video_chat.save()
            return video_chat
        except VideoChat.DoesNotExist:
            return None

    @database_sync_to_async
    def change_video_chat_datetime(self, id, is_start):
        try:
            video_chat = VideoChat.objects.get(id=id)
            if is_start:
                video_chat.started_time = datetime.now()
            else:
                video_chat.finished_time = datetime.now()
            video_chat.save()
            return video_chat
        except VideoChat.DoesNotExist:
            return None

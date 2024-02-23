from django.urls import path
from video_chat.views import video_chat
urlpatterns = [
    path('', video_chat, name='video_chat')
]
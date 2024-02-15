from django.urls import path
from chat import views


urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_chat, name='create_chat'),
    path('chat/<str:chat_id>/', views.chat, name='chat'),
    path('leave/<str:chat_id>/', views.leave_chat, name='leave_chat'),
]
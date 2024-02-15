from django.contrib import admin
from django.contrib.admin import register

from chat.models import GroupChat, Member, Message


@register(GroupChat)
class GroupChatAdmin(admin.ModelAdmin):
    list_display = ['creator', 'title', 'unique_code', 'created_time']


@register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['chat', 'user', 'created_time']


@register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['chat', 'sender', 'text', 'created_time']

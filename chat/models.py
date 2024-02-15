import random

from django.contrib.auth.models import User
from django.db import models


# just for practice
def unique_generator(length=10):
    source = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return ''.join(random.choices(source, k=length))


class GroupChat(models.Model):
    creator = models.ForeignKey(User, related_name='users', on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    unique_code = models.CharField(max_length=50, default=unique_generator)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.unique_code


class Member(models.Model):
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='members')
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Message(models.Model):
    JOIN = 1
    LEAVE = 2
    DELETE = 3
    MSG = 4
    TYPES = [
        (JOIN, 'join'),
        (LEAVE, 'leave'),
        (DELETE, 'delete'),
        (MSG, 'msg'),
    ]
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField(default='')
    type = models.PositiveSmallIntegerField(default=MSG, choices=TYPES)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

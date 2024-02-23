from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

status_list = {
    'contacting': 0,
    'not available': 1,
    'accepted': 2,
    'rejected': 3,
    'busy': 4,
    'processing': 5,
    'ended': 6
}


class VideoChat(models.Model):
    caller = models.ForeignKey(User, related_name='caller_user', on_delete=models.CASCADE)
    callee = models.ForeignKey(User, related_name='callee_user', on_delete=models.CASCADE)
    status = models.IntegerField(default=0)
    started_time = models.DateTimeField(default=datetime.now)
    finished_time = models.DateTimeField(default=datetime.now)
    created_time = models.DateTimeField(auto_now_add=True)

    @property
    def duration(self):
        return self.finished_time - self.created_time

    @property
    def status_name(self):
        return status_list[self.status]

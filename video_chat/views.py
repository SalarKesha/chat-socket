from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from video_chat.models import VideoChat


@login_required
def video_chat(request):
    current_user = request.user
    call_logs = VideoChat.objects.filter(Q(callee=current_user) | Q(caller=current_user))
    return render(request, 'video_chat/video_chat.html', {'call_logs': call_logs})

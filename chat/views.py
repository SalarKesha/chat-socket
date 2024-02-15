import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from chat.forms import UserRegisterForm
from chat.models import GroupChat, Member, Message


@login_required
def index(request):
    current_user = request.user
    print(current_user.members.all())
    return render(request, 'chat/index.html', {'members': current_user.members.all()})


@login_required
def create_chat(request):
    current_user = request.user
    title = request.POST['group_name']
    chat = GroupChat.objects.create(creator=current_user, title=title)
    Member.objects.create(chat=chat, user=current_user)
    print(chat.unique_code)
    print(type(chat.unique_code))
    # return redirect(reverse('chat', args=chat.unique_code))
    return redirect('chat', chat_id=chat.unique_code)


@login_required
def chat(request, chat_id):
    current_user = request.user
    try:
        chat = GroupChat.objects.get(unique_code=chat_id)
        messages = chat.messages.all().order_by('created_time')
    except GroupChat.DoesNotExist:
        return render(request, 'chat/404.html')
    if request.method == 'GET':
        if Member.objects.filter(chat=chat, user=current_user).count() == 0:
            return render(request, 'chat/join_chat.html', {'chat': chat})
        return render(request, 'chat/chat.html', {'chat': chat, 'messages': messages})
    elif request.method == 'POST':
        Member.objects.create(chat=chat, user=current_user)
        return render(request, 'chat/chat.html', {'chat': chat, 'messages': messages})


@login_required
def leave_chat(request, chat_id):
    current_user = request.user
    try:
        chat = GroupChat.objects.get(unique_code=chat_id)
    except GroupChat.DoesNotExist:
        return render(request, 'chat/404.html')
    if chat.creator_id == current_user.id:
        chat.delete()
    else:
        Member.objects.filter(chat=chat, user=current_user).delete()
    return redirect('index')

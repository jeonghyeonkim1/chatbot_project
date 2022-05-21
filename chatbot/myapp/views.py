from django.shortcuts import render


def chatmain(request):
    return render(request, 'chat_main.html')

from django.shortcuts import render


def home(request):
    return render(request, 'home.html')

def test(request):
    return render(request, 'test.html')

def rubybot(request):
    return render(request, 'rubybot.html')

def urambot(request):
    return render(request, 'urambot.html')

def storage(request):
    return render(request, 'storage.html')

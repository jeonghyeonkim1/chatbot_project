from django.shortcuts import render


def home(request):
    return render(request, 'home.html')

def test(request):
    return render(request, 'test.html')

def kakao(request):
    return render(request, 'kakao.html')

def naver(request):
    return render(request, 'naver.html')

def notice(request):
    return render(request, 'notice.html')
